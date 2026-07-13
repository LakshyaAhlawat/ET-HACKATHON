"""RFI semantic dedup + contradiction detection.

Two independent jobs, matching CLAUDE.md's rule:

- semantic_match(): pure embedding similarity (no LLM) -- given a new RFI
  question, finds the historical RFIs most likely to already answer it.
- detect_contradictions(): LLM *perceives* a comparable claim (subject,
  value, unit, whether it's a hedge or a firm answer) out of each of a pair
  of topically-similar historical RFIs; deterministic code then decides
  whether the two claims are numerically incompatible. The LLM never
  itself says "these contradict" -- only the delta_pct-style comparison in
  _claims_contradict() does.
"""

import os
from functools import lru_cache
from itertools import combinations

import instructor
import numpy as np
from groq import Groq
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from app.models.rfi import (
    ClaimExtraction,
    ContradictionFlag,
    DuplicateMatch,
    RFIAnalysisResult,
    RFIRecord,
)
from retrieval.hybrid import EMBED_MODEL_NAME
from rfi.parse import load_rfi_log

MODEL = "llama-3.3-70b-versatile"
CANDIDATE_SIMILARITY_THRESHOLD = 0.45
CONTRADICTION_TOLERANCE_PCT = 3.0

HOURS_PER_AVOIDED_DUPLICATE = 2.5
HOURS_PER_FLAGGED_CONTRADICTION = 6.0


def _client() -> instructor.Instructor:
    api_key = os.environ["GROQ_API_KEY"]
    return instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.TOOLS)


def _rfi_text(rfi: RFIRecord) -> str:
    return f"{rfi.title}. {rfi.question} {rfi.response}"


@lru_cache(maxsize=1)
def _embed_model() -> object:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBED_MODEL_NAME)


@lru_cache(maxsize=1)
def _corpus_embeddings() -> np.ndarray:
    records = load_rfi_log()
    model = _embed_model()
    return np.asarray(model.encode([_rfi_text(r) for r in records], normalize_embeddings=True))  # type: ignore[attr-defined]


def semantic_match(new_question: str, top_k: int = 3) -> list[DuplicateMatch]:
    """Embeds a new RFI question and returns the most similar historical
    RFIs -- what an engineer would otherwise spend time manually searching
    the RFI log for."""
    records = load_rfi_log()
    embeddings = _corpus_embeddings()
    query_vec = _embed_model().encode(new_question, normalize_embeddings=True)  # type: ignore[attr-defined]
    scores = embeddings @ query_vec
    ranked = np.argsort(-scores)[:top_k]
    return [
        DuplicateMatch(
            query=new_question,
            matched_rfi_id=records[i].rfi_id,
            matched_title=records[i].title,
            similarity=float(scores[i]),
        )
        for i in ranked
    ]


def _candidate_pairs() -> list[tuple[int, int, float]]:
    embeddings = _corpus_embeddings()
    n = len(embeddings)
    similarity = embeddings @ embeddings.T
    return [
        (i, j, float(similarity[i, j]))
        for i, j in combinations(range(n), 2)
        if similarity[i, j] >= CANDIDATE_SIMILARITY_THRESHOLD
    ]


class _PairClaims(BaseModel):
    claim_a: ClaimExtraction
    claim_b: ClaimExtraction


_CLAIM_PROMPT = """Two RFI (Request for Information) log entries may concern the same
underlying parameter. For EACH entry, extract a single comparable claim: what
value does its response actually commit to, on what subject, under what
condition (if any), and whether it's a firm/definitive answer or a hedge
(deferred, "not yet confirmed", conditional on something else).

Also set has_unstated_caveat=true on an entry ONLY if its response reveals a
condition or exception that would make someone who relied on the OTHER
entry's answer alone reach the WRONG practical conclusion -- e.g. one says
"yes, approved" with no caveat, the other reveals "approved, but this voids
the warranty unless X" (a real trap for someone who only saw the first
answer). Do NOT set it just because one entry adds more detail, additional
supporting context, a risk explanation that still ends in the same
recommendation, or clarifies the scope of a DIFFERENT but related item --
none of those change the practical answer, so they are not contradictions.
When in doubt, prefer false.

If the two entries are about the same parameter FOR THE SAME underlying
equipment/scenario, use the SAME `subject` string (snake_case) for both
claims so they can be compared. If they name a different equipment variant,
chemistry, or sub-type (e.g. lithium-ion vs. VRLA batteries), those are NOT
comparable even if the parameter name matches -- use different subjects
that include the variant (e.g. "lithium_replacement_interval" vs.
"vrla_replacement_interval") so they are correctly treated as unrelated.

RFI A ({rfi_a_id}): {rfi_a_title}
Question: {rfi_a_question}
Response: {rfi_a_response}

RFI B ({rfi_b_id}): {rfi_b_title}
Question: {rfi_b_question}
Response: {rfi_b_response}"""


_CLAIM_SYSTEM_PROMPT = (
    "You extract structured, comparable claims from RFI log entries. You never "
    "decide whether two entries contradict -- that comparison happens in "
    "deterministic code after you return."
)


def _extract_pair_claims(rfi_a: RFIRecord, rfi_b: RFIRecord) -> _PairClaims:
    user_content = _CLAIM_PROMPT.format(
        rfi_a_id=rfi_a.rfi_id, rfi_a_title=rfi_a.title,
        rfi_a_question=rfi_a.question, rfi_a_response=rfi_a.response,
        rfi_b_id=rfi_b.rfi_id, rfi_b_title=rfi_b.title,
        rfi_b_question=rfi_b.question, rfi_b_response=rfi_b.response,
    )
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": _CLAIM_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    return _client().chat.completions.create(
        model=MODEL,
        response_model=_PairClaims,
        max_retries=2,
        temperature=0.0,
        messages=messages,
    )


def _numeric_contradiction(a: ClaimExtraction, b: ClaimExtraction) -> bool:
    if not (a.is_definitive and b.is_definitive):
        return False
    if a.stated_value is None or b.stated_value is None:
        return False
    if (a.unit or "") != (b.unit or ""):
        return False
    if a.stated_value == 0:
        return b.stated_value != 0
    delta_pct = abs(b.stated_value - a.stated_value) / abs(a.stated_value) * 100
    return delta_pct > CONTRADICTION_TOLERANCE_PCT


def _hidden_caveat_contradiction(a: ClaimExtraction, b: ClaimExtraction) -> bool:
    """One side approved unconditionally; the other reveals a caveat the
    first never mentioned -- the "yes, approved" / "voids warranty unless"
    pattern, distinct from a numeric mismatch."""
    return (a.is_definitive and not a.has_unstated_caveat and b.has_unstated_caveat) or (
        b.is_definitive and not b.has_unstated_caveat and a.has_unstated_caveat
    )


def _claims_contradict(a: ClaimExtraction, b: ClaimExtraction) -> bool:
    """Deterministic comparison -- the only part of this pipeline that
    decides 'contradiction', mirroring evaluate_requirement()'s delta_pct
    check. Two independent shapes: a numeric mismatch, or a hidden caveat
    (see ClaimExtraction's docstring)."""
    if a.subject.lower() != b.subject.lower():
        return False
    return _numeric_contradiction(a, b) or _hidden_caveat_contradiction(a, b)


def _contradiction_reason(
    rfi_a_id: str, rfi_b_id: str, a: ClaimExtraction, b: ClaimExtraction
) -> str:
    if _numeric_contradiction(a, b):
        return (
            f"{rfi_a_id} states {a.stated_value} {a.unit}, {rfi_b_id} states "
            f"{b.stated_value} {b.unit} for the same subject ({a.subject})."
        )
    caveat_id, plain_id = (rfi_b_id, rfi_a_id) if b.has_unstated_caveat else (rfi_a_id, rfi_b_id)
    return (
        f"{plain_id} answers unconditionally on {a.subject}; {caveat_id} reveals a "
        "caveat/condition on the same subject that the other never mentioned."
    )


def detect_contradictions() -> list[ContradictionFlag]:
    records = load_rfi_log()
    flags: list[ContradictionFlag] = []

    for i, j, similarity in _candidate_pairs():
        try:
            claims = _extract_pair_claims(records[i], records[j])
        except Exception:
            continue  # LLM unavailable/quota exhausted -- skip this pair, don't crash the batch
        if _claims_contradict(claims.claim_a, claims.claim_b):
            flags.append(
                ContradictionFlag(
                    rfi_a_id=records[i].rfi_id,
                    rfi_b_id=records[j].rfi_id,
                    topic_similarity=similarity,
                    claim_a=claims.claim_a,
                    claim_b=claims.claim_b,
                    reason=_contradiction_reason(
                        records[i].rfi_id, records[j].rfi_id, claims.claim_a, claims.claim_b
                    ),
                )
            )
    return flags


def analyse(n_new_duplicates_this_period: int = 0) -> RFIAnalysisResult:
    records = load_rfi_log()
    contradictions = detect_contradictions()
    hours_saved = (
        len(contradictions) * HOURS_PER_FLAGGED_CONTRADICTION
        + n_new_duplicates_this_period * HOURS_PER_AVOIDED_DUPLICATE
    )
    return RFIAnalysisResult(
        total_historical_rfis=len(records),
        contradictions=contradictions,
        hours_saved_estimate=hours_saved,
        hours_saved_methodology=(
            f"{len(contradictions)} contradiction(s) flagged x "
            f"{HOURS_PER_FLAGGED_CONTRADICTION:.1f}h avoided rework/coordination each, plus "
            f"{n_new_duplicates_this_period} duplicate RFI(s) matched instantly instead of "
            f"manually researched x {HOURS_PER_AVOIDED_DUPLICATE:.1f}h each. Hours, not "
            "percentages, because the cost of a missed contradiction is engineer time spent "
            "re-litigating a decision, not a score."
        ),
    )
