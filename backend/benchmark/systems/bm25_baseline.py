"""BM25 keyword-search baseline.

Retrieves the top matching corpus chunks by keyword overlap (rank_bm25) and,
for planted-deviation questions, applies a naive raw-number comparison --
deliberately unit-blind and condition-blind, so it reproduces the exact
failure modes CLAUDE.md's architecture exists to prevent: it cannot tell
1688 kW from 1688 TR, and it cannot recognize that a stated value without
its required condition is not evidence of anything.
"""

import re
import time

from rank_bm25 import BM25Okapi

from benchmark.corpus import Chunk, load_corpus_chunks
from benchmark.schema import BenchmarkQuestion, SystemAnswer

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")
_MIN_KEYWORDS = ("not less than", "minimum", "at least", ">=", "no less than")
_MAX_KEYWORDS = ("not exceed", "not more than", "maximum", "<=", "no more than")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9.]+", text.lower())


def _build_index() -> tuple[BM25Okapi, list[Chunk]]:
    chunks = list(load_corpus_chunks())
    corpus_tokens = [_tokenize(c.text) for c in chunks]
    return BM25Okapi(corpus_tokens), chunks


_INDEX_CACHE: dict[str, tuple[BM25Okapi, list[Chunk]]] = {}


def _index() -> tuple[BM25Okapi, list[Chunk]]:
    if "bm25" not in _INDEX_CACHE:
        _INDEX_CACHE["bm25"] = _build_index()
    return _INDEX_CACHE["bm25"]


def retrieve(query: str, top_k: int = 3) -> list[str]:
    bm25, chunks = _index()
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [chunks[i].text for i in ranked]


def _numbers(text: str) -> list[float]:
    return [float(n.replace(",", "")) for n in _NUMBER_RE.findall(text)]


def _classify_deviation(question: str, retrieved: list[str]) -> tuple[str, str]:
    """Naive unit-blind, condition-blind classifier: pulls the first two
    numbers out of the retrieved text and compares them raw."""
    text = " ".join(retrieved)
    numbers = _numbers(text)
    if len(numbers) < 2:
        return "INSUFFICIENT_DATA", "fewer than 2 numbers found in retrieved context"

    spec_value, submitted_value = numbers[0], numbers[1]
    q_lower = question.lower()
    if any(k in q_lower for k in _MAX_KEYWORDS):
        ok = submitted_value <= spec_value
    elif any(k in q_lower for k in _MIN_KEYWORDS):
        ok = submitted_value >= spec_value
    else:
        ok = submitted_value == spec_value
    status = "PASS" if ok else "NON_CONFORMANCE"
    return status, f"raw compare {submitted_value} vs {spec_value} (units/condition ignored)"


def answer_question(question: BenchmarkQuestion, top_k: int = 3) -> SystemAnswer:
    start = time.perf_counter()
    retrieved = retrieve(question.question, top_k=top_k)
    latency_ms = (time.perf_counter() - start) * 1000

    if question.category == "planted_deviations":
        status, note = _classify_deviation(question.question, retrieved)
        return SystemAnswer(
            system="bm25",
            question_id=question.id,
            predicted_status=status,
            predicted_text=status,
            retrieved_context=retrieved,
            latency_ms=latency_ms,
            notes=note,
        )

    return SystemAnswer(
        system="bm25",
        question_id=question.id,
        predicted_status=None,
        predicted_text=" / ".join(retrieved[:2]),
        retrieved_context=retrieved,
        latency_ms=latency_ms,
        notes="keyword retrieval only, no synthesis",
    )
