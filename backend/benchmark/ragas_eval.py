"""RAGAS metrics (faithfulness, context precision, context recall) for the
retrieval-based systems and categories -- bm25 / vanilla_rag / ours on
multi_hop + rfi_dedup (the two categories with no dedicated deterministic
engine, where retrieval quality is the whole story).

This uses Groq (llama-3.3-70b-versatile) as RAGAS's judge LLM, via the same
GROQ_API_KEY already configured for production extraction. Given known Groq
daily-quota exhaustion earlier this project (see CLAUDE.md session history),
every call is wrapped: a quota or network failure produces a clearly-labeled
"skipped" result for that row rather than a crash or a faked score. RAGAS
evaluation never influences the deterministic PASS/NON_CONFORMANCE/
INSUFFICIENT_DATA verdicts -- it only scores retrieval quality on the
free-text categories, and only if explicitly requested.
"""

import os
from functools import lru_cache
from typing import Any

from benchmark.schema import BenchmarkQuestion, SystemAnswer

RAGAS_CATEGORIES = {"multi_hop", "rfi_dedup"}
_MODEL = "llama-3.3-70b-versatile"


class RagasUnavailable(Exception):
    pass


@lru_cache(maxsize=1)
def _llm() -> Any:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RagasUnavailable("GROQ_API_KEY not set")
    from groq import Groq
    from ragas.llms import llm_factory

    client = Groq(api_key=api_key)
    return llm_factory(_MODEL, provider="groq", client=client)


@lru_cache(maxsize=1)
def _metrics() -> dict[str, Any]:
    from ragas.metrics.collections import ContextPrecision, ContextRecall, Faithfulness

    llm = _llm()
    return {
        "faithfulness": Faithfulness(llm=llm),
        "context_precision": ContextPrecision(llm=llm),
        "context_recall": ContextRecall(llm=llm),
    }


async def score_answer(question: BenchmarkQuestion, answer: SystemAnswer) -> dict[str, Any]:
    """Scores one system's answer to one question. Returns a dict with
    faithfulness/context_precision/context_recall in [0, 1], or a single
    'skipped' key with the reason if RAGAS/Groq is unavailable."""
    if not answer.retrieved_context:
        return {"skipped": "no retrieved context to score"}

    try:
        metrics = _metrics()
        reference_parts = [question.expected_answer, question.reason, question.reasoning]
        reference = " ".join(reference_parts).strip()

        faithfulness = await metrics["faithfulness"].ascore(
            user_input=question.question,
            response=answer.predicted_text,
            retrieved_contexts=answer.retrieved_context,
        )
        context_precision = await metrics["context_precision"].ascore(
            user_input=question.question,
            reference=reference,
            retrieved_contexts=answer.retrieved_context,
        )
        context_recall = await metrics["context_recall"].ascore(
            user_input=question.question,
            retrieved_contexts=answer.retrieved_context,
            reference=reference,
        )
        return {
            "faithfulness": faithfulness.value,
            "context_precision": context_precision.value,
            "context_recall": context_recall.value,
        }
    except RagasUnavailable as exc:
        return {"skipped": str(exc)}
    except Exception as exc:  # noqa: BLE001 -- quota/network errors must not crash the run
        return {"skipped": f"{type(exc).__name__}: {exc}"}
