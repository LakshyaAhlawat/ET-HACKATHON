import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/graph", tags=["graph"])

RESULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "graph.json"


@router.get("")
def get_graph() -> dict[str, Any]:
    """Full precomputed knowledge graph (see graph/precompute.py):
    Spec --REQUIRES--> Equipment --SUBMITTED_BY--> Vendor --DELIVERS-->
    Shipment --BLOCKS--> Task, with Task being the real 111-task cascade
    schedule."""
    if not RESULTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="graph.json not found — run `python -m graph.precompute` first",
        )
    return dict(json.loads(RESULTS_PATH.read_text(encoding="utf-8")))


@router.get("/traverse")
def traverse(start_req_id: str | None = None) -> dict[str, Any]:
    """Shortest path from a spec clause to HANDOVER, computed live via
    NetworkX (cheap graph traversal, no LLM) -- the frontend graph screen
    animates this path node by node, same phase-animation pattern as the
    SLD explorer's path trace."""
    from graph.build import shortest_path_to_handover

    return shortest_path_to_handover(start_req_id)
