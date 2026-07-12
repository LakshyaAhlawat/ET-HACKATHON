from pydantic import BaseModel


class SLDNode(BaseModel):
    node_id: str
    node_class: str  # transformer, breaker, ats, ups, generator, busbar, it_load
    bbox: tuple[float, float, float, float]
    confidence: float
    tag: str | None = None  # OCR-extracted label, e.g. "TX-01 2000kVA"


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
    spof_node_id: str | None = None
    # The two representative paths the verdict was decided from, populated on
    # both outcomes — for the frontend to trace: disjoint (holds) or sharing
    # spof_node_id (not holds). Empty when fewer than 2 paths exist at all.
    traced_paths: list[list[str]] = []
