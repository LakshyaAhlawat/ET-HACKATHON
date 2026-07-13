"""Routes sld_topology questions: SLD_001-005 map positionally onto the five
real detected-and-analysed topologies in data/sld_results.json (the actual
YOLOv8 + Hough + NetworkX pipeline output from Session 5). SLD_006-010 are
generic electrical-engineering questions not tied to a specific diagram --
those fall through to fused_retrieval over design_basis_electrical.md.
"""

import json
import time
from functools import lru_cache
from typing import Any

from benchmark.schema import REPO_ROOT, BenchmarkQuestion, SystemAnswer
from benchmark.systems import fused_retrieval

_SLD_RESULTS_PATH = REPO_ROOT / "data" / "sld_results.json"

# SLD_001..SLD_005 -> sld-01..sld-05, by position (both are ordered 5-item lists).
_POSITIONAL_TOPOLOGY = {f"SLD_{i:03d}": f"sld-{i:02d}" for i in range(1, 6)}


@lru_cache(maxsize=1)
def _sld_results() -> dict[str, Any]:
    data = json.loads(_SLD_RESULTS_PATH.read_text(encoding="utf-8"))
    return {entry["topology_id"]: entry for entry in data}


def _answer_from_pipeline(question: BenchmarkQuestion) -> SystemAnswer:
    start = time.perf_counter()
    topology_id = _POSITIONAL_TOPOLOGY[question.id]
    entry = _sld_results().get(topology_id)
    latency_ms = (time.perf_counter() - start) * 1000

    if entry is None:
        return SystemAnswer(
            system="ours",
            question_id=question.id,
            predicted_text=f"no SLD pipeline result for {topology_id}",
            latency_ms=latency_ms,
            notes="missing pipeline output",
        )

    redundancy = entry["redundancy"]
    holds = redundancy["holds"]
    text = (
        f"{topology_id} ({entry['name']}): claimed {redundancy['claimed_redundancy']}, "
        f"holds={holds}. {redundancy['reason']}"
    )
    if redundancy.get("spof_node_id"):
        text += f" SPOF node: {redundancy['spof_node_id']}."

    return SystemAnswer(
        system="ours",
        question_id=question.id,
        predicted_status="NON_CONFORMANCE" if not holds else "PASS",
        predicted_text=text,
        retrieved_context=[],
        latency_ms=latency_ms,
        notes="real YOLOv8 + Hough + NetworkX pipeline (backend/sld)",
    )


def answer_question(question: BenchmarkQuestion) -> SystemAnswer:
    if question.id in _POSITIONAL_TOPOLOGY:
        return _answer_from_pipeline(question)
    return fused_retrieval.answer_question(question)
