import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/sld", tags=["sld"])

RESULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sld_results.json"


def _read_results() -> Any:
    if not RESULTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="sld_results.json not found — run `python -m sld.precompute` first",
        )
    return json.loads(RESULTS_PATH.read_text())


@router.get("/topologies")
def get_topologies() -> list[dict[str, Any]]:
    """All 5 evaluation SLDs: detections, connectivity graph, and the
    redundancy verdict, precomputed offline (see sld/precompute.py)."""
    return list(_read_results())
