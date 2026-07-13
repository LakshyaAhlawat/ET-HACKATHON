"""Query router: an LLM classifies each incoming question into one of four
categories and dispatches it to the engine that actually knows how to
answer it. Without this, every question falls into generic RAG and gets
answered from lexical/semantic similarity alone -- including compliance
questions (which need the deterministic evaluator, not a vibe check),
topology questions (which need graph reachability), and schedule questions
(which need the Monte Carlo simulator, not a guess).

The LLM's job here is classification, not judgment: it decides *which tool*
answers the question. It never itself renders a PASS/NON_CONFORMANCE
verdict, a redundancy verdict, or a schedule number -- those still come
from evaluator.py, graph.py, and cascade/simulate.py respectively, exactly
per CLAUDE.md's rule.

Offline/demo mode: classify_query() is the only live network call anywhere
in the request path (every dispatch handler below reads a precomputed file
or runs a local model/deterministic engine). data/demo_query_cache.json
holds precomputed classifications for the fixed set of questions the demo
script actually asks (see retrieval/cache_demo_queries.py) so the demo
never depends on Groq being reachable -- an exact cache hit skips the
network call entirely. Anything outside that fixed set still classifies
live when Groq is reachable.
"""

import json
import os
import re
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Literal

import instructor
from groq import Groq
from pydantic import BaseModel

from app.services.compliance.corpus_extractor import (
    find_requirement,
    find_requirement_by_equipment,
)
from app.services.compliance.evaluator import evaluate_requirement
from retrieval import hybrid

MODEL = "llama-3.3-70b-versatile"
QueryCategory = Literal["factual", "compliance_check", "topological", "schedule"]

_CLAUSE_ID_RE = re.compile(r"\b([A-Z]{2,6}-\d[\w.\-§ ]*\d)\b")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_CACHE_PATH = REPO_ROOT / "data" / "demo_query_cache.json"


def _normalize(query: str) -> str:
    return " ".join(query.strip().lower().split())


@lru_cache(maxsize=1)
def _demo_cache() -> dict[str, QueryCategory]:
    if not DEMO_CACHE_PATH.exists():
        return {}
    entries = json.loads(DEMO_CACHE_PATH.read_text(encoding="utf-8"))
    return {_normalize(e["query"]): e["category"] for e in entries}


def _client() -> instructor.Instructor:
    api_key = os.environ["GROQ_API_KEY"]
    return instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.TOOLS)


class RouterDecision(BaseModel):
    category: QueryCategory
    reasoning: str


_CLASSIFY_INSTRUCTIONS = """Classify the question into exactly one category:

- factual: a lookup question answerable from spec/RFI/vendor documents
  ("what temperature setpoint does the spec require?")
- compliance_check: asks whether a specific piece of equipment meets a
  specific requirement ("does the chiller meet the cooling capacity spec?")
- topological: asks about connectivity, redundancy, or a dependency chain
  (electrical single-line topology, or spec -> equipment -> vendor ->
  shipment -> task chains)
- schedule: asks about delay impact, critical path, or handover timing

Question: {query}"""


def classify_query(query: str) -> RouterDecision:
    return _client().chat.completions.create(
        model=MODEL,
        response_model=RouterDecision,
        messages=[{"role": "user", "content": _CLASSIFY_INSTRUCTIONS.format(query=query)}],
    )


class RouterResponse(BaseModel):
    category: QueryCategory
    engine: str
    result: dict[str, object]


def _dispatch_compliance(query: str) -> dict[str, object]:
    clause_match = _CLAUSE_ID_RE.search(query)
    requirement = find_requirement(clause_match.group(1)) if clause_match else None
    if requirement is None:
        # No clause id in the question -- fall back to whichever equipment
        # class the retrieval layer thinks is most relevant.
        hits = hybrid.retrieve(query, top_k=5, rerank_top_n=1)
        equipment_guess = hits[0].source_doc if hits else None
        requirement = (
            find_requirement_by_equipment(equipment_guess) if equipment_guess else None
        )
    if requirement is None:
        return {"status": "INSUFFICIENT_DATA", "reason": "no matching requirement found"}

    from app.services.compliance.corpus_extractor import find_extracted_values

    verdict = evaluate_requirement(requirement, find_extracted_values(requirement.req_id))
    return verdict.model_dump()


def _dispatch_topological(query: str) -> dict[str, object]:
    from graph.build import shortest_path_to_handover

    clause_match = _CLAUSE_ID_RE.search(query)
    return shortest_path_to_handover(clause_match.group(1) if clause_match else None)


def _dispatch_schedule(query: str) -> dict[str, object]:
    from cascade.dag import HANDOVER_TASK_ID, TRANSFORMER_DELAY_TASK_ID, build_dag
    from cascade.simulate import simulate_handover

    weeks_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?week", query, re.IGNORECASE)
    delay_weeks = float(weeks_match.group(1)) if weeks_match else 3.0
    handover_days = simulate_handover(
        build_dag(), HANDOVER_TASK_ID, n_runs=2000, seed=42,
        extra_delay_days={TRANSFORMER_DELAY_TASK_ID: delay_weeks * 7.0},
    )
    import numpy as np

    return {
        "assumed_delay_weeks": delay_weeks,
        "p50_handover_day": float(np.percentile(handover_days, 50)),
        "p_slip": float(np.mean(handover_days > 240.0)),
    }


def _dispatch_factual(query: str) -> dict[str, object]:
    hits = hybrid.retrieve(query)
    return {"chunks": [hit.__dict__ for hit in hits]}


_DISPATCH: dict[QueryCategory, tuple[str, Callable[[str], dict[str, object]]]] = {
    "compliance_check": ("compliance_evaluator", _dispatch_compliance),
    "topological": ("graph_traversal", _dispatch_topological),
    "schedule": ("cascade_simulator", _dispatch_schedule),
    "factual": ("hybrid_retrieval", _dispatch_factual),
}


def dispatch(query: str) -> RouterResponse:
    cached_category = _demo_cache().get(_normalize(query))
    if cached_category is not None:
        decision = RouterDecision(
            category=cached_category, reasoning="cached demo classification, no network call"
        )
    else:
        decision = classify_query(query)
    engine, handler = _DISPATCH[decision.category]
    result = handler(query)
    return RouterResponse(category=decision.category, engine=engine, result=result)
