from typing import Literal

from pydantic import BaseModel


class SourceRegion(BaseModel):
    source_doc: str
    source_page: int
    source_bbox: tuple[float, float, float, float]


class Requirement(BaseModel):
    req_id: str  # "MECH-3.4.2"
    equipment_class: str  # "chiller"
    parameter: str  # "cooling_capacity"
    operator: Literal[">=", "<=", "==", "in", "!="]
    value: float
    unit: str  # "TR"
    condition: str | None  # "@35C ambient"  <- LOAD-BEARING
    source_doc: str
    source_page: int
    source_bbox: tuple[float, float, float, float]


class ExtractedValue(BaseModel):
    equipment_class: str
    parameter: str
    value: float
    unit: str
    condition: str | None
    source_doc: str
    source_page: int
    source_bbox: tuple[float, float, float, float]
    extraction_confidence: float


class Verdict(BaseModel):
    req_id: str
    status: Literal["PASS", "NON_CONFORMANCE", "INSUFFICIENT_DATA"]
    required: str  # human-readable: ">= 500 TR @ 35C"
    submitted: str | None  # "480 TR @ 35C"
    delta_pct: float | None  # -4.0
    reason: str  # why INSUFFICIENT_DATA, if applicable
    spec_evidence: SourceRegion
    submittal_evidence: SourceRegion | None
