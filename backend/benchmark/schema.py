import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "benchmark" / "ground_truth_50.json"
PR_CURVE_CONTROLS_PATH = REPO_ROOT / "data" / "benchmark" / "pr_curve_controls.json"
CORPUS_DIR = REPO_ROOT / "data" / "fixtures" / "benchmark_corpus"

Category = Literal[
    "planted_deviations", "multi_hop", "sld_topology", "rfi_dedup", "cascade_scenarios"
]


class BenchmarkQuestion(BaseModel):
    """One row of the 50-question ground-truth key (or a PR-curve control)."""

    id: str
    category: Category
    type: str = ""
    question: str
    expected_answer: str
    reason: str = ""
    reasoning: str = ""
    evidence: dict[str, Any] = {}
    evidence_pointers: list[str] = []
    req_id: str | None = None  # set for planted_deviations rows only


def load_ground_truth() -> list[BenchmarkQuestion]:
    """Loads the official 50-question key verbatim -- never edited to match
    system output (see data/benchmark/ground_truth_50.json metadata)."""
    data = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    return [BenchmarkQuestion.model_validate(q) for q in data["questions"]]


def load_pr_curve_controls() -> list[BenchmarkQuestion]:
    """Loads the 5 synthesized compliant control cases used only to give the
    precision/recall curve a negative class -- NOT part of the official key."""
    data = json.loads(PR_CURVE_CONTROLS_PATH.read_text(encoding="utf-8"))
    return [BenchmarkQuestion.model_validate(q) for q in data["questions"]]


class SystemAnswer(BaseModel):
    """One system's answer to one question."""

    system: str
    question_id: str
    predicted_status: str | None = None  # PASS / NON_CONFORMANCE / INSUFFICIENT_DATA
    predicted_text: str = ""
    retrieved_context: list[str] = []
    delta_pct: float | None = None
    latency_ms: float = 0.0
    correct: bool | None = None
    notes: str = ""


class QuestionResult(BaseModel):
    """A question plus every system's answer to it -- the per-question JSON
    a judge can inspect on demand."""

    question: BenchmarkQuestion
    answers: dict[str, SystemAnswer]
