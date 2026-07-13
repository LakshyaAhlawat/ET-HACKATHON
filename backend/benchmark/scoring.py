"""Scoring for the 50-question benchmark (+ 5 PR-curve controls).

Two different scoring regimes, because the categories are not comparable:

- planted_deviations (+ controls): expected_answer is a clean enum
  (PASS / NON_CONFORMANCE / INSUFFICIENT_DATA) -- exact-match, plus
  precision/recall framed around "flagging a deviation" as the positive
  class, plus a tolerance-threshold sweep on 'ours' own delta_pct so the
  precision/recall tradeoff the user wants to show in the pitch is a real
  curve, not an assertion.
- everything else (multi_hop, rfi_dedup, sld_topology, cascade_scenarios):
  expected_answer is free text. Scored by keyword/evidence-pointer recall
  against the system's retrieved context + answer text -- a cheap,
  deterministic, reproducible proxy for "did this system actually find the
  right material." RAGAS (ragas_eval.py) supplies the richer semantic
  metrics (faithfulness, context precision/recall) on top of this for the
  retrieval-based systems.
"""

import re
from dataclasses import dataclass, field

from benchmark.schema import BenchmarkQuestion, SystemAnswer

_POSITIVE_LABEL = "NON_CONFORMANCE"
TOLERANCE_SWEEP_PCT = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0]


@dataclass
class ConfusionCounts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)


def _is_positive(status: str | None) -> bool:
    return status == _POSITIVE_LABEL


def confusion_for_deviation_detection(
    questions: list[BenchmarkQuestion], answers: dict[str, SystemAnswer]
) -> ConfusionCounts:
    counts = ConfusionCounts()
    for q in questions:
        answer = answers.get(q.id)
        predicted = answer.predicted_status if answer else None
        expected_positive = _is_positive(q.expected_answer)
        predicted_positive = _is_positive(predicted)
        if expected_positive and predicted_positive:
            counts.tp += 1
        elif not expected_positive and predicted_positive:
            counts.fp += 1
        elif expected_positive and not predicted_positive:
            counts.fn += 1
        else:
            counts.tn += 1
    return counts


def exact_match_accuracy(
    questions: list[BenchmarkQuestion], answers: dict[str, SystemAnswer]
) -> float:
    if not questions:
        return 0.0
    correct = sum(
        1 for q in questions
        if (answers.get(q.id) and answers[q.id].predicted_status == q.expected_answer)
    )
    return correct / len(questions)


def insufficient_data_accuracy(
    questions: list[BenchmarkQuestion], answers: dict[str, SystemAnswer]
) -> float | None:
    """Of the questions whose correct answer is 'we don't have enough
    information', what fraction did the system correctly abstain on --
    the metric that most directly separates a real verifier from a chatbot
    that never says INSUFFICIENT_DATA (see vanilla_rag.py)."""
    subset = [q for q in questions if q.expected_answer == "INSUFFICIENT_DATA"]
    if not subset:
        return None
    correct = sum(
        1 for q in subset
        if answers.get(q.id) and answers[q.id].predicted_status == "INSUFFICIENT_DATA"
    )
    return correct / len(subset)


def tolerance_sweep(
    questions: list[BenchmarkQuestion], ours_answers: dict[str, SystemAnswer]
) -> list[dict[str, float | int | None]]:
    """Sweeps a forgiveness band over 'ours' own delta_pct: at tolerance T%,
    any NON_CONFORMANCE verdict whose |delta_pct| <= T is reclassified as
    PASS before scoring. This is the only system with a continuous delta_pct
    signal to sweep -- BM25/vanilla RAG/Ctrl+F each contribute one fixed
    (recall, precision) point instead (see report.py)."""
    points = []
    for tolerance in TOLERANCE_SWEEP_PCT:
        adjusted: dict[str, SystemAnswer] = {}
        for q in questions:
            answer = ours_answers.get(q.id)
            if answer is None:
                continue
            status = answer.predicted_status
            near_miss = answer.delta_pct is not None and abs(answer.delta_pct) <= tolerance
            if status == _POSITIVE_LABEL and near_miss:
                status = "PASS"
            adjusted[q.id] = answer.model_copy(update={"predicted_status": status})
        counts = confusion_for_deviation_detection(questions, adjusted)
        points.append(
            {
                "tolerance_pct": tolerance,
                "precision": counts.precision,
                "recall": counts.recall,
                "f1": counts.f1,
                "tp": counts.tp, "fp": counts.fp, "fn": counts.fn, "tn": counts.tn,
            }
        )
    return points


_WORD_RE = re.compile(r"[a-z0-9]+")


def _keywords(text: str, min_len: int = 4) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if len(w) >= min_len}


@dataclass
class RetrievalScore:
    keyword_recall: float
    matched: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)


def retrieval_keyword_recall(
    question: BenchmarkQuestion, answer: SystemAnswer | None
) -> RetrievalScore:
    """Cheap, deterministic proxy for retrieval quality on free-text
    categories: what fraction of the distinctive keywords in the reference
    (expected_answer + reason/reasoning) also appear somewhere in the
    system's retrieved context or answer text."""
    reference = " ".join([question.expected_answer, question.reason, question.reasoning])
    reference_keywords = _keywords(reference)
    if not reference_keywords:
        return RetrievalScore(keyword_recall=0.0)

    context = answer.retrieved_context if answer else []
    answer_text = answer.predicted_text if answer else ""
    haystack = " ".join([*context, answer_text])
    haystack_keywords = _keywords(haystack)

    matched = sorted(reference_keywords & haystack_keywords)
    missed = sorted(reference_keywords - haystack_keywords)
    return RetrievalScore(
        keyword_recall=len(matched) / len(reference_keywords),
        matched=matched,
        missed=missed,
    )
