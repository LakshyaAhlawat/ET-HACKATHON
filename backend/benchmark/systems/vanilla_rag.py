"""Vanilla RAG strawman: naive chunk -> embed -> retrieve, no rerank, no
structured judgment.

Built deliberately weak, per the session brief: this is "just bolt on a
chatbot" made concrete. Its embeddings are real (sentence-transformers), its
retrieval is real cosine similarity -- but its answer for planted-deviation
questions comes from a sentiment-style keyword scan of the top-1 chunk, and
it NEVER emits INSUFFICIENT_DATA. That is the point: a chatbot given a
retrieved paragraph will confidently say yes-or-no even when the paragraph
doesn't actually contain the condition needed to answer -- CLAUDE.md's
mandate that INSUFFICIENT_DATA is a required third outcome exists precisely
because this failure mode is what naive RAG defaults to.
"""

import time
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from benchmark.corpus import Chunk, load_corpus_chunks
from benchmark.schema import BenchmarkQuestion, SystemAnswer

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_NEGATIVE_KEYWORDS = (
    "not include", "not included", "not stated", "does not", "not specified",
    "deferred", "missing", "shared header", "single ", "no standby",
    "not less than", "voids", "void", "exceeds", "below the", "not confirmed",
)

_EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model() -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_EMBED_MODEL_NAME)  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def _corpus_embeddings() -> tuple[list[Chunk], np.ndarray]:
    chunks = list(load_corpus_chunks())
    embeddings = _model().encode([c.text for c in chunks], normalize_embeddings=True)
    return chunks, np.asarray(embeddings)


def retrieve(query: str, top_k: int = 1) -> list[str]:
    chunks, embeddings = _corpus_embeddings()
    query_vec = _model().encode([query], normalize_embeddings=True)[0]
    scores = embeddings @ query_vec
    ranked = np.argsort(-scores)[:top_k]
    return [chunks[i].text for i in ranked]


def _classify_deviation(retrieved: list[str]) -> str:
    text = " ".join(retrieved).lower()
    if any(kw in text for kw in _NEGATIVE_KEYWORDS):
        return "NON_CONFORMANCE"
    return "PASS"  # naive RAG's default: sounds confident, never abstains


def answer_question(question: BenchmarkQuestion, top_k: int = 2) -> SystemAnswer:
    start = time.perf_counter()
    retrieved = retrieve(question.question, top_k=top_k)
    latency_ms = (time.perf_counter() - start) * 1000

    if question.category == "planted_deviations":
        status = _classify_deviation(retrieved)
        return SystemAnswer(
            system="vanilla_rag",
            question_id=question.id,
            predicted_status=status,
            predicted_text=status,
            retrieved_context=retrieved,
            latency_ms=latency_ms,
            notes="sentiment-keyword guess on top-1 chunk; never abstains",
        )

    return SystemAnswer(
        system="vanilla_rag",
        question_id=question.id,
        predicted_status=None,
        predicted_text=" / ".join(retrieved),
        retrieved_context=retrieved,
        latency_ms=latency_ms,
        notes="single-vector retrieval only, no rerank, no synthesis",
    )
