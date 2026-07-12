from fastapi import APIRouter

from app.models.schema import ExtractedValue, Requirement, Verdict
from app.services.compliance.evaluator import evaluate_requirement

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/evaluate", response_model=Verdict)
def evaluate(requirement: Requirement, extracted_values: list[ExtractedValue]) -> Verdict:
    return evaluate_requirement(requirement, extracted_values)
