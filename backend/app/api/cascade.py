import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.cascade import CascadeLookup, MitigationCandidate, Task

router = APIRouter(prefix="/api/cascade", tags=["cascade"])

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _read_json(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{filename} not found — run `python -m cascade.precompute` first",
        )
    return json.loads(path.read_text())


@router.get("/tasks", response_model=list[Task])
def get_tasks() -> list[Task]:
    """The ~120-task schedule DAG, for the frontend Gantt chart."""
    return [Task.model_validate(t) for t in _read_json("cascade_tasks.json")]


@router.get("/lookup", response_model=CascadeLookup)
def get_lookup() -> CascadeLookup:
    """The precomputed transformer-delay sweep (0-8 weeks, 0.5-week steps).

    Fetch this ONCE — the frontend slider must never trigger a new
    simulation on drag; it interpolates this lookup client-side.
    """
    return CascadeLookup.model_validate(_read_json("cascade_lookup.json"))


@router.get("/mitigations", response_model=list[MitigationCandidate])
def get_mitigations() -> list[MitigationCandidate]:
    """Ranked interventions for the baseline 3-week transformer delay scenario."""
    return [MitigationCandidate.model_validate(m) for m in _read_json("cascade_mitigations.json")]
