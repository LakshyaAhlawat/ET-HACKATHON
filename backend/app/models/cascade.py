from pydantic import BaseModel


class ScheduleTask(BaseModel):
    task_id: str
    name: str
    duration_days: float
    predecessors: list[str]
    duration_std_dev_days: float = 0.0


class DelayScenario(BaseModel):
    task_id: str
    delay_days: float


class CascadeResult(BaseModel):
    baseline_completion_day: float
    delayed_completion_day: float
    slip_days: float
    critical_path: list[str]
    p50_completion_day: float
    p90_completion_day: float
