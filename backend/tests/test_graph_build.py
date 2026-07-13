from app.models.graph import TraversalResult
from graph.build import build_graph, full_graph, shortest_path_to_handover


def _traverse(start_req_id: str | None) -> TraversalResult:
    return TraversalResult.model_validate(shortest_path_to_handover(start_req_id))


def test_graph_includes_all_five_node_types() -> None:
    graph = build_graph()
    node_types = {data["node_type"] for _node, data in graph.nodes(data=True)}
    assert node_types == {"spec", "equipment", "vendor", "shipment", "task"}


def test_graph_has_no_isolated_spec_nodes() -> None:
    # Every spec node with a mapped discipline must have at least one
    # outgoing REQUIRES edge -- otherwise build_graph() added a node with
    # no edges, which would break every traversal from it.
    graph = build_graph()
    spec_nodes = [n for n, data in graph.nodes(data=True) if data["node_type"] == "spec"]
    assert spec_nodes
    for node in spec_nodes:
        assert graph.out_degree(node) >= 1


def test_shortest_path_reaches_handover_for_a_known_clause() -> None:
    result = _traverse("MECH-3.4.2")
    assert result.start_node_id == "MECH-3.4.2"
    assert result.path_node_ids[0] == "MECH-3.4.2"
    assert result.path_node_ids[-1] == "HANDOVER"
    # Equipment -> Vendor -> Shipment must appear right after the spec node.
    node_types = [n.node_type for n in result.nodes]
    assert node_types[:4] == ["spec", "equipment", "vendor", "shipment"]


def test_shortest_path_reports_reason_for_unknown_clause() -> None:
    result = _traverse("NOT-A-REAL-CLAUSE")
    assert result.path_node_ids == []
    assert "NOT-A-REAL-CLAUSE" in result.reason


def test_shortest_path_falls_back_to_a_real_clause_when_none_given() -> None:
    result = _traverse(None)
    assert result.path_node_ids
    assert result.start_node_id is not None
    assert not result.start_node_id.startswith("CTRL-")


def test_full_graph_result_matches_networkx_graph_size() -> None:
    graph = build_graph()
    result = full_graph()
    assert len(result.nodes) == graph.number_of_nodes()
    assert len(result.edges) == graph.number_of_edges()
