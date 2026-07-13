import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/rfi", tags=["rfi"])

RESULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "rfi_analysis.json"


class RFIMatchRequest(BaseModel):
    question: str


@router.get("/analysis")
def get_analysis() -> dict[str, Any]:
    """Precomputed contradiction analysis over the historical RFI log (see
    rfi/precompute.py) — semantic clustering + LLM claim extraction is not
    re-run on every request."""
    if not RESULTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="rfi_analysis.json not found — run `python -m rfi.precompute` first",
        )
    return dict(json.loads(RESULTS_PATH.read_text(encoding="utf-8")))


@router.post("/match")
def match(request: RFIMatchRequest) -> list[dict[str, Any]]:
    """Semantic-matches a new RFI question against the historical log —
    embedding similarity only, no LLM call, so this is cheap enough to run
    live on every submission."""
    from rfi.dedup import semantic_match

    return [m.model_dump() for m in semantic_match(request.question)]
