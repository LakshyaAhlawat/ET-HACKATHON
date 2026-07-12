"""NumPy Monte Carlo simulation over the cascade schedule DAG.

Vectorized across all n_runs simultaneously: each task is visited once in
topological order, and its start/finish for all runs is computed as one
array operation. No LLM involved — pure arithmetic over a schedule graph,
per CLAUDE.md's architectural rule.
"""

from typing import Any

import networkx as nx
import numpy as np

from app.models.cascade import SweepPoint

_HISTOGRAM_BINS = 40


def _window_bounds(window: Any) -> tuple[float, float, float] | None:
    """Reads (start_day, end_day, multiplier) from a SeasonalWindow model or
    a plain dict — tests use both shapes for a node's seasonal_window."""
    if window is None:
        return None
    if isinstance(window, dict):
        return window["start_day"], window["end_day"], window["multiplier"]
    return window.start_day, window.end_day, window.multiplier


def simulate_handover(
    dag: nx.DiGraph,
    sink_task_id: str,
    n_runs: int = 10_000,
    seed: int | None = None,
    extra_delay_days: dict[str, float] | None = None,
) -> np.ndarray:
    """Runs n_runs Monte Carlo samples of the schedule and returns an array
    of shape (n_runs,) with the sink task's simulated finish day per run.

    extra_delay_days adds a fixed extra duration to specific task(s) in every
    run (e.g. a transformer procurement delay), on top of the sampled
    per-task duration distribution.
    """
    rng = np.random.default_rng(seed)
    topo_order = list(nx.topological_sort(dag))
    index = {task_id: i for i, task_id in enumerate(topo_order)}
    n_tasks = len(topo_order)

    means = np.array([dag.nodes[t]["duration_mean"] for t in topo_order])
    stds = np.array([dag.nodes[t]["duration_std"] for t in topo_order])

    durations = rng.normal(loc=means, scale=stds, size=(n_runs, n_tasks))
    # Floor at 20% of the mean so sampled durations never go to zero/negative.
    durations = np.maximum(durations, means * 0.2)

    if extra_delay_days:
        for task_id, extra in extra_delay_days.items():
            durations[:, index[task_id]] += extra

    start = np.zeros((n_runs, n_tasks))
    finish = np.zeros((n_runs, n_tasks))

    for task_id in topo_order:
        i = index[task_id]
        predecessors = list(dag.predecessors(task_id))
        if predecessors:
            pred_indices = [index[p] for p in predecessors]
            start[:, i] = finish[:, pred_indices].max(axis=1)

        task_duration = durations[:, i]
        window = _window_bounds(dag.nodes[task_id].get("seasonal_window"))
        if window is not None:
            window_start, window_end, multiplier = window
            in_window = (start[:, i] >= window_start) & (start[:, i] <= window_end)
            task_duration = np.where(in_window, task_duration * multiplier, task_duration)

        finish[:, i] = start[:, i] + task_duration

    return finish[:, index[sink_task_id]]


def sweep_transformer_delay(
    dag: nx.DiGraph,
    transformer_task_id: str,
    sink_task_id: str,
    target_handover_day: float,
    weeks_range: tuple[float, float] = (0.0, 8.0),
    step_weeks: float = 0.5,
    n_runs: int = 10_000,
    seed: int | None = 42,
) -> list[SweepPoint]:
    """Runs the Monte Carlo simulation once per transformer-delay step across
    weeks_range, precomputing everything the frontend slider needs so a drag
    event never triggers a new simulation."""
    n_steps = round((weeks_range[1] - weeks_range[0]) / step_weeks) + 1
    delay_weeks_values = [
        round(weeks_range[0] + i * step_weeks, 4) for i in range(n_steps)
    ]

    # Fixed bin edges across every sweep point, from a zero-delay run, so the
    # frontend histogram redraws smoothly instead of jumping axes on drag.
    baseline = simulate_handover(dag, sink_task_id, n_runs=n_runs, seed=seed)
    bin_edges = np.linspace(
        baseline.min() * 0.9, baseline.min() + (8.0 * 7 * 3), _HISTOGRAM_BINS + 1
    )

    points: list[SweepPoint] = []
    for delay_weeks in delay_weeks_values:
        handover_days = simulate_handover(
            dag,
            sink_task_id,
            n_runs=n_runs,
            seed=seed,
            extra_delay_days={transformer_task_id: delay_weeks * 7.0},
        )
        counts, _ = np.histogram(handover_days, bins=bin_edges)
        points.append(
            SweepPoint(
                transformer_delay_weeks=delay_weeks,
                p50_handover_day=float(np.percentile(handover_days, 50)),
                p90_handover_day=float(np.percentile(handover_days, 90)),
                mean_handover_day=float(np.mean(handover_days)),
                p_slip=float(np.mean(handover_days > target_handover_day)),
                histogram_bin_edges=[float(e) for e in bin_edges],
                histogram_counts=[int(c) for c in counts],
            )
        )

    return points
