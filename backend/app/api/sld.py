from fastapi import APIRouter, HTTPException

from app.models.sld import RedundancyResult, SLDEdge, SLDNode
from app.services.sld.analyser import analyse_redundancy

router = APIRouter(prefix="/sld", tags=["sld"])


@router.post("/analyse", response_model=RedundancyResult)
def analyse(
    nodes: list[SLDNode],
    edges: list[SLDEdge],
    claimed_redundancy: str,
) -> RedundancyResult:
    try:
        return analyse_redundancy(nodes, edges, claimed_redundancy)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501, detail="SLD redundancy analyser not yet implemented"
        ) from exc
