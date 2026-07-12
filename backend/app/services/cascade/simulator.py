from app.models.cascade import CascadeResult, DelayScenario, ScheduleTask


def run_cascade_simulation(
    tasks: list[ScheduleTask],
    delays: list[DelayScenario],
    monte_carlo_iterations: int = 10_000,
) -> CascadeResult:
    """Propagate delays through the CPM critical path and Monte Carlo the completion date.

    NetworkX builds the DAG and computes the critical path; NumPy draws the
    per-task duration samples for the Monte Carlo sweep. No LLM involved —
    this is pure arithmetic over a schedule graph.
    """
    raise NotImplementedError
