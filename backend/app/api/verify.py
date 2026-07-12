import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.models.schema import ExtractedValue, Requirement, Verdict
from app.services.compliance.evaluator import evaluate_requirement

router = APIRouter(prefix="/api/verify", tags=["verify"])

EXTRACTED_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "extracted"
# Single-spec demo scope: every submittal is checked against this one spec's
# precomputed requirements. A multi-project system would look this up by
# project/submittal association instead of a fixed filename.
SPEC_REQUIREMENTS_FILE = "spec.requirements.json"


@router.post("/{submittal_id}", response_model=list[Verdict])
def verify_submittal(submittal_id: str) -> list[Verdict]:
    """Runs every precomputed requirement against a submittal's precomputed
    extracted values and returns one Verdict per requirement.

    Reads offline-generated JSON from data/extracted/ (see ingestion/ingest.py)
    — no LLM calls happen here, per CLAUDE.md's architectural rule.
    """
    values_path = EXTRACTED_DIR / f"{submittal_id}.values.json"
    requirements_path = EXTRACTED_DIR / SPEC_REQUIREMENTS_FILE

    if not values_path.exists():
        raise HTTPException(
            status_code=404, detail=f"No extracted values found for submittal '{submittal_id}'"
        )
    if not requirements_path.exists():
        raise HTTPException(status_code=404, detail="No extracted spec requirements found")

    values = [ExtractedValue.model_validate(v) for v in json.loads(values_path.read_text())]
    requirements = [
        Requirement.model_validate(r) for r in json.loads(requirements_path.read_text())
    ]

    return [evaluate_requirement(req, values) for req in requirements]
