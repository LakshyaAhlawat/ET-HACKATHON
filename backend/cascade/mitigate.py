"""Ranks candidate schedule interventions for the pitch's baseline scenario:
a 3-week transformer supply delay.

Structured as a LangGraph state machine for an explicit, visualisable
pipeline (per CLAUDE.md's tech stack) — but every node is deterministic
Python. Ranking interventions by Delta P(slip) / cost is arithmetic, not a
judgment call, so no LLM is involved anywhere in this file.
"""

import copy
from typing import Any, TypedDict

import networkx as nx
from langgraph.graph import END, StateGraph

from app.models.cascade import MitigationCandidate
from cascade.dag import (
    HANDOVER_TASK_ID,
    TARGET_HANDOVER_DAY,
    TRANSFORMER_DELAY_TASK_ID,
    build_dag,
)
from cascade.simulate import simulate_handover

# The pitch's baseline scenario: a 3-week transformer supply delay already happened.
BASELINE_TRANSFORMER_DELAY_DAYS = 3.0 * 7
N_RUNS = 5_000
SEED = 99


def _p_slip(dag: nx.DiGraph, extra_delay_days: dict[str, float]) -> float:
    handover_days = simulate_handover(
        dag,
        HANDOVER_TASK_ID,
        n_runs=N_RUNS,
        seed=SEED,
        extra_delay_days=extra_delay_days,
    )
    return float((handover_days > TARGET_HANDOVER_DAY).mean())


def _intervention_air_freight(dag: nx.DiGraph) -> tuple[nx.DiGraph, dict[str, float]]:
    """Air-freight the transformer: recovers 2.5 of the 3 delay weeks, at cost."""
    delay = {TRANSFORMER_DELAY_TASK_ID: BASELINE_TRANSFORMER_DELAY_DAYS - 2.5 * 7}
    return dag, delay


def _intervention_resequence_trades(dag: nx.DiGraph) -> tuple[nx.DiGraph, dict[str, float]]:
    """Zero-cost: LV panel installation only needs the transformer physically
    placed, not its full site acceptance test — fast-track that dependency
    instead of serially waiting on SAT, which is the actual bottleneck the
    transformer delay pushes downstream."""
    modified = dag.copy()
    if modified.has_edge("XFMR-SAT", "ELEC-INSTALL"):
        modified.remove_edge("XFMR-SAT", "ELEC-INSTALL")
        modified.add_edge("XFMR-INSTALL", "ELEC-INSTALL")
    delay = {TRANSFORMER_DELAY_TASK_ID: BASELINE_TRANSFORMER_DELAY_DAYS}
    return modified, delay


def _intervention_split_ist(dag: nx.DiGraph) -> tuple[nx.DiGraph, dict[str, float]]:
    """Split IST into phases run concurrently rather than serially, cutting
    the integrated test's own duration on the critical path."""
    modified = dag.copy()
    modified.nodes["IST-INTEGRATED"]["duration_mean"] *= 0.6
    modified.nodes["IST-INTEGRATED"]["duration_std"] *= 0.6
    delay = {TRANSFORMER_DELAY_TASK_ID: BASELINE_TRANSFORMER_DELAY_DAYS}
    return modified, delay


def _intervention_second_crew(dag: nx.DiGraph) -> tuple[nx.DiGraph, dict[str, float]]:
    """Add a second crew to the transformer install to halve its duration."""
    modified = dag.copy()
    modified.nodes["XFMR-INSTALL"]["duration_mean"] *= 0.5
    modified.nodes["XFMR-INSTALL"]["duration_std"] *= 0.5
    delay = {TRANSFORMER_DELAY_TASK_ID: BASELINE_TRANSFORMER_DELAY_DAYS}
    return modified, delay


_CANDIDATES: list[dict[str, Any]] = [
    {
        "intervention_id": "resequence_trades",
        "name": "Resequence trades: fast-track LV electrical off transformer install",
        "description": (
            "LV panel installation currently waits for the transformer's FULL "
            "site acceptance test, but it only actually needs the transformer "
            "physically placed. Depend on install completion instead of SAT "
            "completion — a pure scheduling fix, no cost."
        ),
        "cost_inr": 0.0,
        "build": _intervention_resequence_trades,
    },
    {
        "intervention_id": "split_ist_phases",
        "name": "Split the integrated systems test into concurrent phases",
        "description": (
            "Run power, mechanical, life-safety, and IT integration checks "
            "concurrently under coordinated test engineering instead of one "
            "long serial IST window."
        ),
        "cost_inr": 400_000.0,
        "build": _intervention_split_ist,
    },
    {
        "intervention_id": "second_crew_transformer_install",
        "name": "Add a second crew to the transformer install",
        "description": (
            "Mobilize a second crew for the outdoor switchyard transformer "
            "install to roughly halve its on-site duration."
        ),
        "cost_inr": 900_000.0,
        "build": _intervention_second_crew,
    },
    {
        "intervention_id": "air_freight_transformer",
        "name": "Air-freight the transformer",
        "description": (
            "Recover ~2.5 of the 3 delayed weeks by air-freighting the "
            "transformer instead of sea freight."
        ),
        "cost_inr": 2_800_000.0,
        "build": _intervention_air_freight,
    },
]


class MitigateState(TypedDict):
    baseline_p_slip: float
    results: list[MitigationCandidate]


def _compute_baseline(state: MitigateState) -> MitigateState:
    dag = build_dag()
    baseline_p_slip = _p_slip(dag, {TRANSFORMER_DELAY_TASK_ID: BASELINE_TRANSFORMER_DELAY_DAYS})
    return {**state, "baseline_p_slip": baseline_p_slip}


def _simulate_candidates(state: MitigateState) -> MitigateState:
    results: list[MitigationCandidate] = []
    for candidate in _CANDIDATES:
        dag = copy.deepcopy(build_dag())
        modified_dag, extra_delay = candidate["build"](dag)
        mitigated_p_slip = _p_slip(modified_dag, extra_delay)

        delta = state["baseline_p_slip"] - mitigated_p_slip
        cost = candidate["cost_inr"]
        is_zero_cost = cost <= 0
        efficiency = None if is_zero_cost else delta / cost

        results.append(
            MitigationCandidate(
                intervention_id=candidate["intervention_id"],
                name=candidate["name"],
                description=candidate["description"],
                cost_inr=cost,
                baseline_p_slip=state["baseline_p_slip"],
                mitigated_p_slip=mitigated_p_slip,
                delta_p_slip=delta,
                efficiency_per_inr=efficiency,
                is_zero_cost=is_zero_cost,
            )
        )

    return {**state, "results": results}


def _rank(state: MitigateState) -> MitigateState:
    # Zero-cost wins surface first regardless of magnitude — cost-effectiveness
    # is undefined-but-infinite at zero cost. Everything else ranks by
    # Delta P(slip) per rupee, descending.
    ranked = sorted(
        state["results"],
        key=lambda c: (
            0 if c.is_zero_cost else 1,
            -(c.delta_p_slip if c.is_zero_cost else (c.efficiency_per_inr or 0.0)),
        ),
    )
    return {**state, "results": ranked}


def _build_graph() -> Any:
    graph = StateGraph(MitigateState)
    graph.add_node("compute_baseline", _compute_baseline)
    graph.add_node("simulate_candidates", _simulate_candidates)
    graph.add_node("rank", _rank)
    graph.set_entry_point("compute_baseline")
    graph.add_edge("compute_baseline", "simulate_candidates")
    graph.add_edge("simulate_candidates", "rank")
    graph.add_edge("rank", END)
    return graph.compile()


def run_mitigation_analysis() -> list[MitigationCandidate]:
    app = _build_graph()
    final_state = app.invoke({"baseline_p_slip": 0.0, "results": []})
    results: list[MitigationCandidate] = final_state["results"]
    return results
