"""The payoff: enumerates all paths IT-load -> source and checks 2N.

"Source" means a transformer node — the diagram's detection classes don't
include a separate utility/grid symbol, so a transformer is where utility
power enters the diagram. 2N holds iff there exist two node-disjoint paths
from some source to the IT-load. If every pair of paths shares a node, that
node is the single point of failure.

Pure NetworkX graph reachability — no LLM involved, per CLAUDE.md's
architectural rule.
"""

import networkx as nx

from app.models.sld import RedundancyResult, SLDEdge, SLDNode

SOURCE_CLASS = "transformer"
LOAD_CLASS = "it_load"


def _build_graph(nodes: list[SLDNode], edges: list[SLDEdge]) -> nx.Graph:
    graph: nx.Graph = nx.Graph()
    for node in nodes:
        graph.add_node(node.node_id, node_class=node.node_class)
    for edge in edges:
        graph.add_edge(edge.source_node_id, edge.target_node_id)
    return graph


def analyse_redundancy(
    nodes: list[SLDNode],
    edges: list[SLDEdge],
    claimed_redundancy: str,
    source_doc: str = "",
) -> RedundancyResult:
    graph = _build_graph(nodes, edges)

    sources = [n.node_id for n in nodes if n.node_class == SOURCE_CLASS]
    loads = [n.node_id for n in nodes if n.node_class == LOAD_CLASS]

    if not sources or not loads:
        return RedundancyResult(
            source_doc=source_doc,
            claimed_redundancy=claimed_redundancy,
            holds=False,
            reason=(
                "Could not identify both a source (transformer) and an IT-load "
                "node in the detected topology"
            ),
            failure_paths=[],
        )

    load_id = loads[0]
    all_paths: list[list[str]] = []
    for source_id in sources:
        if source_id not in graph or load_id not in graph:
            continue
        all_paths.extend(nx.all_simple_paths(graph, source=source_id, target=load_id))

    if len(all_paths) < 2:
        return RedundancyResult(
            source_doc=source_doc,
            claimed_redundancy=claimed_redundancy,
            holds=False,
            reason=(
                f"Only {len(all_paths)} path(s) found from source to IT-load; "
                f"{claimed_redundancy} requires at least two"
            ),
            failure_paths=all_paths,
        )

    for i in range(len(all_paths)):
        for j in range(i + 1, len(all_paths)):
            path_a = set(all_paths[i]) - {load_id}
            path_b = set(all_paths[j]) - {load_id}
            if path_a.isdisjoint(path_b):
                return RedundancyResult(
                    source_doc=source_doc,
                    claimed_redundancy=claimed_redundancy,
                    holds=True,
                    reason=(
                        f"Found node-disjoint paths: {' -> '.join(all_paths[i])} and "
                        f"{' -> '.join(all_paths[j])}"
                    ),
                    failure_paths=[],
                    traced_paths=[all_paths[i], all_paths[j]],
                )

    # No disjoint pair exists — every path shares at least one node with
    # every other. Several nodes can be common at once (a whole shared
    # "tail" after paths converge, e.g. ATS -> BRK_OUT -> load); report the
    # FIRST point of convergence, since that's where redundancy was actually
    # lost and where fixing it would matter, not an arbitrary downstream node.
    common_nodes = set(all_paths[0]) - {load_id}
    for path in all_paths[1:]:
        common_nodes &= set(path) - {load_id}
    spof = min(common_nodes, key=all_paths[0].index) if common_nodes else None

    return RedundancyResult(
        source_doc=source_doc,
        claimed_redundancy=claimed_redundancy,
        holds=False,
        reason=(
            f"Every path from source to IT-load shares node '{spof}' — single point of failure"
            if spof
            else "No node-disjoint path pair exists, but no single common node was found"
        ),
        failure_paths=all_paths,
        spof_node_id=spof,
        traced_paths=all_paths[:2],
    )
