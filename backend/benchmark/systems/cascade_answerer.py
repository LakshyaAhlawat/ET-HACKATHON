"""Routes the 5 cascade_scenarios questions to the real schedule engine
(backend/cascade/dag.py + simulate.py + mitigate.py) -- no LLM, no retrieval,
pure arithmetic over the actual 111-task DAG and its Monte Carlo sweep, per
CLAUDE.md's "NEVER an LLM for arithmetic" rule.
"""

import re
import time
from functools import lru_cache
from typing import Any

from benchmark.schema import BenchmarkQuestion, SystemAnswer
from cascade.dag import HANDOVER_TASK_ID, TARGET_HANDOVER_DAY, TRANSFORMER_DELAY_TASK_ID, build_dag
from cascade.mitigate import run_mitigation_analysis
from cascade.simulate import simulate_handover

_GENERATOR_DELAY_TASK_ID = "DG-PROCURE"
_DAYS_PER_WEEK = 7.0
_CURRENCY_RE = re.compile(r"₹\s*([\d.]+)\s*(lakh|crore)", re.IGNORECASE)
_WEEKS_RE = re.compile(r"(-?\d+(?:\.\d+)?)[\s-]*week", re.IGNORECASE)


@lru_cache(maxsize=1)
def _dag() -> Any:
    return build_dag()


def _lakh(amount: float, unit: str) -> float:
    return amount * (100.0 if unit.lower() == "crore" else 1.0)


def _money_values(text: str) -> list[float]:
    return [_lakh(float(v), unit) for v, unit in _CURRENCY_RE.findall(text)]


def _week_values(text: str) -> list[float]:
    return [float(v) for v in _WEEKS_RE.findall(text)]


def _cascade_001(question: BenchmarkQuestion) -> str:
    dag = _dag()
    handover_days = simulate_handover(
        dag, HANDOVER_TASK_ID, n_runs=5000, seed=42,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: 3 * _DAYS_PER_WEEK},
    )
    import numpy as np

    p50 = float(np.percentile(handover_days, 50))
    p_slip = float(np.mean(handover_days > TARGET_HANDOVER_DAY))
    slip_weeks = (p50 - TARGET_HANDOVER_DAY) / _DAYS_PER_WEEK
    return (
        f"Simulated p50 handover day {p50:.1f} (target {TARGET_HANDOVER_DAY:.0f}), "
        f"a slip of {slip_weeks:.1f} weeks; P(handover > target) = {p_slip:.2f}. "
        "Monsoon seasonal window is applied automatically by the simulator when the "
        "delayed installation start falls inside it."
    )


def _cascade_002(question: BenchmarkQuestion) -> str:
    dag = _dag()
    import numpy as np

    combined = simulate_handover(
        dag, HANDOVER_TASK_ID, n_runs=5000, seed=42,
        extra_delay_days={
            TRANSFORMER_DELAY_TASK_ID: 3 * _DAYS_PER_WEEK,
            _GENERATOR_DELAY_TASK_ID: 2 * _DAYS_PER_WEEK,
        },
    )
    transformer_only = simulate_handover(
        dag, HANDOVER_TASK_ID, n_runs=5000, seed=42,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: 3 * _DAYS_PER_WEEK},
    )
    p50_combined = float(np.percentile(combined, 50))
    p50_transformer_only = float(np.percentile(transformer_only, 50))
    aggregate_slip_weeks = (p50_combined - TARGET_HANDOVER_DAY) / _DAYS_PER_WEEK
    return (
        f"Simulated combined p50 handover day {p50_combined:.1f} vs transformer-only "
        f"{p50_transformer_only:.1f} -- the two delays are not simply additive on the "
        f"critical path; aggregate slip is {aggregate_slip_weeks:.1f} weeks."
    )


def _cascade_generic_cost(question: BenchmarkQuestion) -> str:
    """CASCADE_003/004/005 combine the real mitigation-ranking output with
    plain arithmetic over the cost/week and week figures stated in the
    question itself -- deterministic parsing + arithmetic, not an LLM
    judgment call."""
    candidates = run_mitigation_analysis()
    money = _money_values(question.question)
    weeks = _week_values(question.question)
    lines = ["Ranked mitigations from mitigate.py: " + ", ".join(
        f"{c.name} (Δp_slip={c.delta_p_slip:+.3f}, cost=₹{c.cost_inr / 100_000:.0f}L)"
        for c in candidates
    )]
    if money and weeks:
        cost_per_week = money[0] / weeks[0] if weeks[0] else 0.0
        lines.append(
            f"Parsed cost/week figures from question: {money} lakh over {weeks} week(s) "
            f"-> ~₹{cost_per_week:.1f}L/week reference rate."
        )
    return " | ".join(lines)


_HANDLERS = {
    "transformer_delay": _cascade_001,
    "concurrent_delay": _cascade_002,
}


def answer_question(question: BenchmarkQuestion) -> SystemAnswer:
    start = time.perf_counter()
    handler = _HANDLERS.get(question.type, _cascade_generic_cost)
    try:
        text = handler(question)
        notes = "real DAG + Monte Carlo simulation (cascade/simulate.py)"
    except Exception as exc:  # pragma: no cover
        text = f"cascade engine error: {exc}"
        notes = "error"
    latency_ms = (time.perf_counter() - start) * 1000

    return SystemAnswer(
        system="ours",
        question_id=question.id,
        predicted_status=None,
        predicted_text=text,
        retrieved_context=[],
        latency_ms=latency_ms,
        notes=notes,
    )
