"""Deterministic FACT-tag extractor for the benchmark corpus.

This mirrors what backend/ingestion/extract.py does in production (Groq +
instructor, canonical-vocabulary prompt) but is regex-based against the
`[FACT ...]` annotations authored into data/fixtures/benchmark_corpus/*.md --
see that folder's README.md for why: the benchmark must reproduce the same
score without depending on live LLM API quota. The compliance judgment
itself (backend/app/services/compliance/evaluator.py) is untouched and
identical to production -- only the perception step is swapped for a
reproducible stand-in.
"""

import re
from functools import lru_cache

from app.models.schema import ExtractedValue, Requirement
from benchmark.corpus import load_corpus_raw_text

_FACT_LINE_RE = re.compile(r"\[FACT\s+([^\]]*)\]")
_KV_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')

_DUMMY_BBOX = (0.0, 0.0, 0.0, 0.0)


def _parse_kv(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for key, raw_value in _KV_RE.findall(body):
        value = raw_value[1:-1] if raw_value.startswith('"') else raw_value
        fields[key] = value
    return fields


def _clean_condition(raw: str | None) -> str | None:
    if raw is None or raw == "null":
        return None
    return raw


@lru_cache(maxsize=1)
def extract_corpus_facts() -> tuple[list[Requirement], list[ExtractedValue]]:
    """Scans the full benchmark corpus for [FACT ...] tags and splits them
    into Requirement (spec side, has `operator=`) and ExtractedValue
    (submittal side, has `source_doc=`) objects."""
    requirements: list[Requirement] = []
    extracted_values: list[ExtractedValue] = []

    for match in _FACT_LINE_RE.finditer(load_corpus_raw_text()):
        fields = _parse_kv(match.group(1))
        condition = _clean_condition(fields.get("condition"))

        if "operator" in fields:
            requirements.append(
                Requirement(
                    req_id=fields["req_id"],
                    equipment_class=fields["equipment_class"],
                    parameter=fields["parameter"],
                    operator=fields["operator"],  # type: ignore[arg-type]
                    value=float(fields["value"]),
                    unit=fields["unit"],
                    condition=condition,
                    source_doc="spec_requirements.md",
                    source_page=1,
                    source_bbox=_DUMMY_BBOX,
                )
            )
        else:
            extracted_values.append(
                ExtractedValue(
                    equipment_class=fields["equipment_class"],
                    parameter=fields["parameter"],
                    value=float(fields["value"]),
                    unit=fields["unit"],
                    condition=condition,
                    source_doc=fields.get("source_doc", "vendor_submittals.md"),
                    source_page=int(fields.get("source_page", 1)),
                    source_bbox=_DUMMY_BBOX,
                    extraction_confidence=float(fields.get("confidence", 0.9)),
                )
            )

    return requirements, extracted_values


def find_requirement(req_id: str) -> Requirement | None:
    requirements, _ = extract_corpus_facts()
    for req in requirements:
        if req.req_id == req_id:
            return req
    return None


def find_extracted_values(req_id: str) -> list[ExtractedValue]:
    """Extracted values are keyed by req_id only for benchmark bookkeeping --
    the real evaluator matches on equipment_class + parameter, exactly as in
    production, via evaluate_requirement()."""
    requirements, values = extract_corpus_facts()
    req = next((r for r in requirements if r.req_id == req_id), None)
    if req is None:
        return []
    return [
        v for v in values
        if v.equipment_class == req.equipment_class and v.parameter == req.parameter
    ]
