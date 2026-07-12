from pydantic import BaseModel


class SLDNode(BaseModel):
    node_id: str
    label: str
    bbox: tuple[float, float, float, float]
    confidence: float


class SLDEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    confidence: float


class RedundancyResult(BaseModel):
    source_doc: str
    claimed_redundancy: str  # e.g. "2N"
    holds: bool
    reason: str
    failure_paths: list[list[str]]
