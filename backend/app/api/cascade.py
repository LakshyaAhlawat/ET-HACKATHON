from fastapi import APIRouter, HTTPException

from app.models.cascade import CascadeResult, DelayScenario, ScheduleTask
from app.services.cascade.simulator import run_cascade_simulation

router = APIRouter(prefix="/cascade", tags=["cascade"])


@router.post("/simulate", response_model=CascadeResult)
def simulate(tasks: list[ScheduleTask], delays: list[DelayScenario]) -> CascadeResult:
    try:
        return run_cascade_simulation(tasks, delays)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=501, detail="Cascade simulator not yet implemented"
        ) from exc
