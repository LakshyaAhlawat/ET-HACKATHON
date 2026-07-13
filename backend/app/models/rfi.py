from pydantic import BaseModel


class RFIRecord(BaseModel):
    rfi_id: str
    date: str
    title: str
    question: str
    response: str


class ClaimExtraction(BaseModel):
    """LLM-perceived shape of what an RFI response actually claims. Purely
    descriptive -- whether two claims contradict is decided by deterministic
    comparison in dedup.py, never by the model.

    Two independent contradiction shapes show up in a real RFI log: two
    different *numbers* for the same parameter (stated_value/unit), and a
    later response revealing a *caveat* an earlier, unconditional-sounding
    approval on the same subject never mentioned (has_unstated_caveat) --
    e.g. "yes, biodiesel is approved" followed by "biodiesel voids the
    warranty unless it was in the original submittal."""

    subject: str
    stated_value: float | None
    unit: str | None
    condition: str | None
    is_definitive: bool
    has_unstated_caveat: bool = False


class DuplicateMatch(BaseModel):
    query: str
    matched_rfi_id: str
    matched_title: str
    similarity: float


class ContradictionFlag(BaseModel):
    rfi_a_id: str
    rfi_b_id: str
    topic_similarity: float
    claim_a: ClaimExtraction
    claim_b: ClaimExtraction
    reason: str


class RFIAnalysisResult(BaseModel):
    total_historical_rfis: int
    contradictions: list[ContradictionFlag]
    hours_saved_estimate: float
    hours_saved_methodology: str
