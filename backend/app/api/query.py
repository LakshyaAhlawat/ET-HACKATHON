from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from retrieval.router import RouterResponse, dispatch

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str


@router.post("", response_model=RouterResponse)
def run_query(request: QueryRequest) -> RouterResponse:
    """Classifies the question (factual / compliance_check / topological /
    schedule) and dispatches to the engine that actually answers it -- see
    retrieval/router.py. The classification is the only LLM call in this
    path; every answer still comes from a deterministic engine."""
    try:
        return dispatch(request.query)
    except Exception as exc:
        # The classification step is a live Groq call -- a quota or network
        # failure should surface as a clean 503, not a raw traceback. The
        # deterministic engines dispatch() calls into never raise for
        # ordinary "no data" cases (they return INSUFFICIENT_DATA instead).
        raise HTTPException(
            status_code=503,
            detail=f"Query classification unavailable: {type(exc).__name__}: {exc}",
        ) from exc
