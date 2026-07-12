import networkx as nx
import numpy as np
import pytest

from cascade.dag import HANDOVER_TASK_ID, TRANSFORMER_DELAY_TASK_ID, build_dag
from cascade.simulate import simulate_handover, sweep_transformer_delay


def _toy_dag() -> nx.DiGraph:
    """A -> B -> D, A -> C -> D. D is the sink (handover-equivalent)."""
    dag = nx.DiGraph()
    dag.add_node("A", duration_mean=10.0, duration_std=0.0, seasonal_window=None)
    dag.add_node("B", duration_mean=5.0, duration_std=0.0, seasonal_window=None)
    dag.add_node("C", duration_mean=20.0, duration_std=0.0, seasonal_window=None)
    dag.add_node("D", duration_mean=3.0, duration_std=0.0, seasonal_window=None)
    dag.add_edge("A", "B")
    dag.add_edge("A", "C")
    dag.add_edge("B", "D")
    dag.add_edge("C", "D")
    return dag


def test_deterministic_toy_dag_matches_manual_critical_path() -> None:
    # A(10) -> C(20) -> D(3) = 33 is the critical path (longer than A->B->D=18)
    dag = _toy_dag()
    result = simulate_handover(dag, sink_task_id="D", n_runs=100, seed=1)

    assert result.min() == pytest.approx(33.0)
    assert result.max() == pytest.approx(33.0)  # zero std -> no variance


def test_toy_dag_extra_delay_on_non_critical_path_has_no_effect() -> None:
    # Delaying B (on the shorter A->B->D path) shouldn't move the handover
    # day at all, since C is the binding constraint.
    dag = _toy_dag()
    baseline = simulate_handover(dag, sink_task_id="D", n_runs=100, seed=1)
    delayed = simulate_handover(
        dag, sink_task_id="D", n_runs=100, seed=1, extra_delay_days={"B": 5.0}
    )

    assert delayed.mean() == pytest.approx(baseline.mean())


def test_toy_dag_extra_delay_on_critical_path_passes_through() -> None:
    dag = _toy_dag()
    delayed = simulate_handover(
        dag, sink_task_id="D", n_runs=100, seed=1, extra_delay_days={"C": 5.0}
    )

    assert delayed.min() == pytest.approx(38.0)


def test_seasonal_window_multiplies_duration_only_when_start_falls_inside() -> None:
    dag = nx.DiGraph()
    dag.add_node("A", duration_mean=10.0, duration_std=0.0, seasonal_window=None)
    dag.add_node(
        "B",
        duration_mean=10.0,
        duration_std=0.0,
        seasonal_window={"start_day": 5.0, "end_day": 50.0, "multiplier": 2.0},
    )
    dag.add_edge("A", "B")

    # A finishes at day 10, which is inside B's [5, 50] window -> B's duration doubles.
    in_window = simulate_handover(dag, sink_task_id="B", n_runs=10, seed=1)
    assert in_window.min() == pytest.approx(10.0 + 20.0)

    # Push A's duration out past B's window so B starts at day 100 -> no multiplier.
    dag.nodes["A"]["duration_mean"] = 100.0
    out_of_window = simulate_handover(dag, sink_task_id="B", n_runs=10, seed=1)
    assert out_of_window.min() == pytest.approx(100.0 + 10.0)


def test_p_slip_is_a_valid_probability() -> None:
    dag = build_dag()
    result = simulate_handover(dag, sink_task_id=HANDOVER_TASK_ID, n_runs=500, seed=1)
    p_slip = float(np.mean(result > 300.0))

    assert 0.0 <= p_slip <= 1.0


def test_transformer_delay_never_decreases_handover_day() -> None:
    dag = build_dag()
    baseline = simulate_handover(
        dag, sink_task_id=HANDOVER_TASK_ID, n_runs=2000, seed=7
    )
    delayed = simulate_handover(
        dag,
        sink_task_id=HANDOVER_TASK_ID,
        n_runs=2000,
        seed=7,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: 21.0},
    )

    assert delayed.mean() >= baseline.mean()


def test_transformer_delay_can_amplify_beyond_the_raw_delay() -> None:
    # The whole point of the monsoon window on the switchyard install: a
    # transformer delay long enough to push that install into the monsoon
    # window should cost MORE than the raw injected delay, not just pass
    # through 1:1. Use the same seed so only the delay differs.
    dag = build_dag()
    small_delay = simulate_handover(
        dag,
        sink_task_id=HANDOVER_TASK_ID,
        n_runs=3000,
        seed=3,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: 3.0 * 7},
    )
    large_delay = simulate_handover(
        dag,
        sink_task_id=HANDOVER_TASK_ID,
        n_runs=3000,
        seed=3,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: 8.0 * 7},
    )

    raw_delay_diff_days = (8.0 - 3.0) * 7
    actual_diff_days = large_delay.mean() - small_delay.mean()
    assert actual_diff_days > raw_delay_diff_days


def test_sweep_returns_seventeen_points_from_0_to_8_weeks_step_half() -> None:
    dag = build_dag()
    sweep = sweep_transformer_delay(
        dag,
        transformer_task_id=TRANSFORMER_DELAY_TASK_ID,
        sink_task_id=HANDOVER_TASK_ID,
        target_handover_day=300.0,
        weeks_range=(0.0, 8.0),
        step_weeks=0.5,
        n_runs=200,
        seed=1,
    )

    assert len(sweep) == 17
    assert sweep[0].transformer_delay_weeks == pytest.approx(0.0)
    assert sweep[-1].transformer_delay_weeks == pytest.approx(8.0)


def test_sweep_p_slip_is_monotonically_non_decreasing() -> None:
    dag = build_dag()
    sweep = sweep_transformer_delay(
        dag,
        transformer_task_id=TRANSFORMER_DELAY_TASK_ID,
        sink_task_id=HANDOVER_TASK_ID,
        target_handover_day=300.0,
        weeks_range=(0.0, 8.0),
        step_weeks=1.0,
        n_runs=1500,
        seed=1,
    )

    p_slips = [point.p_slip for point in sweep]
    assert p_slips == sorted(p_slips)


def test_sweep_histogram_bin_edges_are_consistent_across_points() -> None:
    dag = build_dag()
    sweep = sweep_transformer_delay(
        dag,
        transformer_task_id=TRANSFORMER_DELAY_TASK_ID,
        sink_task_id=HANDOVER_TASK_ID,
        target_handover_day=300.0,
        weeks_range=(0.0, 8.0),
        step_weeks=2.0,
        n_runs=200,
        seed=1,
    )

    first_edges = sweep[0].histogram_bin_edges
    assert all(point.histogram_bin_edges == first_edges for point in sweep)
