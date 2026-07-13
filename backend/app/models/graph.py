from typing import Literal

from pydantic import BaseModel

NodeType = Literal["spec", "equipment", "vendor", "shipment", "task"]
RelationType = Literal["REQUIRES", "SUBMITTED_BY", "DELIVERS", "BLOCKS", "PRECEDES"]


class GraphNode(BaseModel):
    node_id: str
    node_type: NodeType
    label: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: RelationType


class GraphResult(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class TraversalResult(BaseModel):
    """A path traced from a Spec clause through Equipment/Vendor/Shipment
    into the real cascade schedule, ending at HANDOVER (or wherever the
    path was cut off) -- the frontend graph screen animates this list of
    node ids edge by edge."""

    start_node_id: str | None
    path_node_ids: list[str]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    reason: str
