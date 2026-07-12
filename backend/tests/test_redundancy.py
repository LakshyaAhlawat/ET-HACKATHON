from app.models.sld import SLDEdge, SLDNode
from sld.redundancy import analyse_redundancy
from sld.topology import SldTopology, all_topologies


def _to_sld_nodes(topology: SldTopology) -> list[SLDNode]:
    return [
        SLDNode(node_id=n.node_id, node_class=n.node_class, bbox=(0, 0, 0, 0), confidence=1.0)
        for n in topology.nodes
    ]


def _to_sld_edges(topology: SldTopology) -> list[SLDEdge]:
    return [
        SLDEdge(source_node_id=a, target_node_id=b, confidence=1.0) for a, b in topology.edges
    ]


def test_all_five_ground_truth_topologies_match_expected_verdict() -> None:
    for topology in all_topologies():
        nodes = _to_sld_nodes(topology)
        edges = _to_sld_edges(topology)

        result = analyse_redundancy(
            nodes, edges, claimed_redundancy="2N", source_doc=topology.topology_id
        )

        assert result.holds == topology.expected_2n_holds, (
            f"{topology.topology_id} ({topology.name}): expected holds="
            f"{topology.expected_2n_holds}, got {result.holds}. Reason: {result.reason}"
        )
        if topology.expected_spof is not None:
            assert result.spof_node_id == topology.expected_spof, (
                f"{topology.topology_id}: expected SPOF {topology.expected_spof}, "
                f"got {result.spof_node_id}"
            )


def test_true_2n_topology_reports_no_spof() -> None:
    topology = next(t for t in all_topologies() if t.topology_id == "sld-01")
    result = analyse_redundancy(
        _to_sld_nodes(topology), _to_sld_edges(topology), "2N", topology.topology_id
    )

    assert result.holds is True
    assert result.spof_node_id is None
    assert result.failure_paths == []


def test_spof_topology_identifies_the_shared_node() -> None:
    topology = next(t for t in all_topologies() if t.topology_id == "sld-02")
    result = analyse_redundancy(
        _to_sld_nodes(topology), _to_sld_edges(topology), "2N", topology.topology_id
    )

    assert result.holds is False
    assert result.spof_node_id == "ATS"
    assert len(result.failure_paths) == 2


def test_missing_source_or_load_is_insufficient() -> None:
    nodes = [
        SLDNode(node_id="A", node_class="breaker", bbox=(0, 0, 0, 0), confidence=1.0),
        SLDNode(node_id="B", node_class="busbar", bbox=(0, 0, 0, 0), confidence=1.0),
    ]
    edges = [SLDEdge(source_node_id="A", target_node_id="B", confidence=1.0)]

    result = analyse_redundancy(nodes, edges, "2N")

    assert result.holds is False
    assert "transformer" in result.reason.lower() or "it-load" in result.reason.lower()


def test_single_path_is_insufficient_for_2n() -> None:
    nodes = [
        SLDNode(node_id="XFMR", node_class="transformer", bbox=(0, 0, 0, 0), confidence=1.0),
        SLDNode(node_id="BRK", node_class="breaker", bbox=(0, 0, 0, 0), confidence=1.0),
        SLDNode(node_id="LOAD", node_class="it_load", bbox=(0, 0, 0, 0), confidence=1.0),
    ]
    edges = [
        SLDEdge(source_node_id="XFMR", target_node_id="BRK", confidence=1.0),
        SLDEdge(source_node_id="BRK", target_node_id="LOAD", confidence=1.0),
    ]

    result = analyse_redundancy(nodes, edges, "2N")

    assert result.holds is False
    assert "requires at least two" in result.reason
