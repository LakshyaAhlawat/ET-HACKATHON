from pydantic import BaseModel


class SeasonalWindow(BaseModel):
    """A monsoon-style window: a duration MULTIPLIER applied only if a task's
    simulated start day falls inside it — never a hard block on scheduling."""

    start_day: float
    end_day: float
    multiplier: float


class Task(BaseModel):
    task_id: str
    name: str
    discipline: str
    phase: str
    duration_mean_days: float
    duration_std_days: float
    predecessors: list[str]
    seasonal_window: SeasonalWindow | None = None
    is_milestone: bool = False  # surfaced in the simplified frontend Gantt


class SweepPoint(BaseModel):
    transformer_delay_weeks: float
    p50_handover_day: float
    p90_handover_day: float
    mean_handover_day: float
    p_slip: float
    histogram_bin_edges: list[float]
    histogram_counts: list[int]


class CascadeLookup(BaseModel):
    target_handover_day: float
    points: list[SweepPoint]


class MitigationCandidate(BaseModel):
    intervention_id: str
    name: str
    description: str
    cost_inr: float
    baseline_p_slip: float
    mitigated_p_slip: float
    delta_p_slip: float
    efficiency_per_inr: float | None  # None for zero-cost options (undefined ratio)
    is_zero_cost: bool
