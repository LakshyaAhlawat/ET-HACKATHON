"""Builds the project knowledge graph: Spec --REQUIRES--> Equipment
--SUBMITTED_BY--> Vendor --DELIVERS--> Shipment --BLOCKS--> Task, with the
Task layer being the real 111-task cascade schedule (backend/cascade/dag.py)
so a traversal from a spec clause runs straight into the actual critical
path, ending at HANDOVER.

No live Neo4j instance is available in this dev environment (no
NEO4J_URI configured -- see app/core/config.py), so the graph is built and
queried with NetworkX and shipped as precomputed JSON (data/graph.json),
matching how cascade/ and sld/ avoid depending on a running service at demo
time. graph/neo4j_sync.py can push this same graph to a live AuraDB
instance if credentials are ever supplied -- the schema is identical either
way, this module just doesn't require it to run.

Every edge here comes from data already in the repo (requirement facts,
the vendor named in each submittal, the real cascade schedule) -- nothing
is invented for the graph. Where a submittal doesn't name a vendor, no
SUBMITTED_BY edge is created rather than guessing one.
"""

from functools import lru_cache

import networkx as nx

from app.models.graph import GraphEdge, GraphNode, GraphResult, TraversalResult
from app.models.schema import ExtractedValue
from app.services.compliance.corpus_extractor import extract_corpus_facts
from cascade.dag import HANDOVER_TASK_ID, build_tasks

# equipment_class -> cascade discipline. "any" (generic procurement clauses
# like lead-time requirements) has no single discipline and is left out.
_DISCIPLINE_MAP = {
    "chiller": "CHW",
    "cooling_loop": "CHW",
    "tim": "ITN",
    "ats": "ELEC",
    "ups": "UPS",
    "generator": "DG",
    "switchgear": "ELEC",
    "cable": "ELEC",
}

# Substring of ExtractedValue.source_doc -> vendor name. Only submittals
# that actually name a vendor get an edge; the rest are left unconnected
# rather than guessed.
_VENDOR_MAP = {
    "Vertiv CentraVac": "Vertiv",
    "Trane Sintesis": "Trane",
    "Schneider ATS": "Schneider Electric",
    "Vertiv UPS": "Vertiv",
    "Generator package": "Caterpillar",
    "Switchgear package": "ABB",
    "Chiller documentation package": "Vertiv",
}


def _vendor_for(source_doc: str) -> str | None:
    for substring, vendor in _VENDOR_MAP.items():
        if substring in source_doc:
            return vendor
    return None


@lru_cache(maxsize=1)
def build_graph() -> nx.DiGraph:
    graph = nx.DiGraph()

    for task in build_tasks():
        node_type = "shipment" if task.task_id.endswith("-SHIP") else "task"
        graph.add_node(task.task_id, node_type=node_type, label=task.name)
    for task in build_tasks():
        for pred in task.predecessors:
            relation = "BLOCKS" if pred.endswith("-SHIP") else "PRECEDES"
            graph.add_edge(pred, task.task_id, relation=relation)

    requirements, values = extract_corpus_facts()
    values_by_key: dict[tuple[str, str], list[ExtractedValue]] = {}
    for v in values:
        values_by_key.setdefault((v.equipment_class, v.parameter), []).append(v)

    for req in requirements:
        discipline = _DISCIPLINE_MAP.get(req.equipment_class)
        if discipline is None:
            continue

        graph.add_node(req.req_id, node_type="spec", label=req.req_id)
        graph.add_node(req.equipment_class, node_type="equipment", label=req.equipment_class)
        graph.add_edge(req.req_id, req.equipment_class, relation="REQUIRES")

        matches = values_by_key.get((req.equipment_class, req.parameter), [])
        vendor = next(
            (_vendor_for(v.source_doc) for v in matches if _vendor_for(v.source_doc)), None
        )
        if vendor is None:
            continue
        graph.add_node(vendor, node_type="vendor", label=vendor)
        graph.add_edge(req.equipment_class, vendor, relation="SUBMITTED_BY")

        shipment_id = f"{discipline}-SHIP"
        if graph.has_node(shipment_id):
            graph.add_edge(vendor, shipment_id, relation="DELIVERS")

    return graph


def _to_graph_node(graph: nx.DiGraph, node_id: str) -> GraphNode:
    data = graph.nodes[node_id]
    return GraphNode(node_id=node_id, node_type=data["node_type"], label=data["label"])


def full_graph() -> GraphResult:
    graph = build_graph()
    nodes = [_to_graph_node(graph, n) for n in graph.nodes]
    edges = [
        GraphEdge(source=u, target=v, relation=graph.edges[u, v]["relation"])
        for u, v in graph.edges
    ]
    return GraphResult(nodes=nodes, edges=edges)


def shortest_path_to_handover(start_req_id: str | None) -> dict[str, object]:
    """Traces the shortest path from a spec clause to HANDOVER through
    Equipment -> Vendor -> Shipment -> the real cascade schedule. Falls back
    to the first requirement with a complete vendor chain only when no
    clause id was given at all -- an unrecognized clause id reports "not
    found" rather than silently substituting a different one, so the router
    never answers a different question than the one asked."""
    graph = build_graph()
    requirements, _ = extract_corpus_facts()
    req_ids = [r.req_id for r in requirements]

    if start_req_id is None:
        # Prefer a real spec clause over the PR-curve CTRL-* controls when
        # picking a default demo path.
        ranked = sorted(req_ids, key=lambda r: r.startswith("CTRL-"))
        candidate = next(
            (r for r in ranked if graph.has_node(r) and nx.has_path(graph, r, HANDOVER_TASK_ID)),
            None,
        )
    else:
        candidate = start_req_id if start_req_id in req_ids else None

    if candidate is None or not nx.has_path(graph, candidate, HANDOVER_TASK_ID):
        return TraversalResult(
            start_node_id=start_req_id,
            path_node_ids=[],
            nodes=[],
            edges=[],
            reason=(
                f"No traceable path from {start_req_id!r} to {HANDOVER_TASK_ID} -- "
                "either the clause id wasn't found or its submittal doesn't name a "
                "vendor, so the chain has no Vendor/Shipment edge to continue on."
            ),
        ).model_dump()

    path = nx.shortest_path(graph, candidate, HANDOVER_TASK_ID)
    nodes = [_to_graph_node(graph, n) for n in path]
    edges = [
        GraphEdge(source=u, target=v, relation=graph.edges[u, v]["relation"])
        for u, v in zip(path[:-1], path[1:], strict=True)
    ]
    return TraversalResult(
        start_node_id=candidate,
        path_node_ids=path,
        nodes=nodes,
        edges=edges,
        reason=f"Shortest path from {candidate} to {HANDOVER_TASK_ID} ({len(path)} nodes).",
    ).model_dump()
