"""LLM perception layer: turns raw spec/submittal text into typed constraints.

Per CLAUDE.md's architectural rule, this module only *perceives* — it reads
prose and produces structured `Requirement` / `ExtractedValue` records. It
never judges compliance. `req_id` (when stated) and the numeric/unit/operator
fields come from the model; `source_doc` / `source_page` / `source_bbox`
always come from the input chunk, never from the model, so provenance can't
be hallucinated.

Offline batch usage only — see ingest.py for the CLI that writes
data/extracted/*.json. Not a live API route.
"""

import os
from typing import Literal

import instructor
from groq import Groq
from pydantic import BaseModel, Field

from app.models.schema import ExtractedValue, Requirement
from ingestion.models import DocChunk

MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3


def _client() -> instructor.Instructor:
    api_key = os.environ["GROQ_API_KEY"]
    return instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.TOOLS)


class _ExtractedRequirement(BaseModel):
    """LLM-facing shape for a single constraint. No provenance fields — those
    are attached deterministically from the source chunk after extraction."""

    req_id: str | None = Field(
        description=(
            "Clause identifier exactly as written, e.g. '3.4.2' or 'MECH-3.4.2'. "
            "null if the clause has no visible identifier."
        )
    )
    equipment_class: str = Field(description="Lowercase snake_case, e.g. 'chiller', 'ups'")
    parameter: str = Field(description="Lowercase snake_case, e.g. 'cooling_capacity'")
    operator: Literal[">=", "<=", "==", "in", "!="]
    value: float
    unit: str = Field(description="Unit exactly as stated, e.g. 'TR', 'kVA', '%'. '' if unitless.")
    condition: str | None = Field(
        description=(
            "The specific qualifying condition for THIS constraint only, e.g. "
            "'@35C ambient'. null if this constraint has no attached condition — "
            "do not copy a condition from a neighboring constraint in the same clause."
        )
    )


class _RequirementBatch(BaseModel):
    requirements: list[_ExtractedRequirement]


class _ExtractedValueLLM(BaseModel):
    equipment_class: str = Field(description="Lowercase snake_case, e.g. 'chiller', 'ups'")
    parameter: str = Field(description="Lowercase snake_case, e.g. 'cooling_capacity'")
    value: float
    unit: str = Field(description="Unit exactly as stated. '' if unitless.")
    condition: str | None = Field(
        description="The qualifying condition this value was measured/stated under, if any."
    )
    extraction_confidence: float = Field(
        ge=0.0, le=1.0, description="How confident you are this value was read correctly."
    )


class _ValueBatch(BaseModel):
    values: list[_ExtractedValueLLM]


_CANONICAL_VOCABULARY = """\
Canonical equipment_class vocabulary — ALWAYS reuse one of these if the
equipment matches, even if the text uses a more specific or verbose noun
phrase (e.g. "diesel generator set" / "standby generator" -> "generator",
"automatic transfer switch" -> "ats", "air handling unit" -> "ahu",
"chilled water pump" -> "pump", "raised floor system" -> "raised_floor",
"lightning protection system" -> "lightning_protection"):
chiller, generator, ups, transformer, busway, cable, crac, ahu, pdu, battery,
pump, fire_pump, ats, raised_floor, smoke_detector, lightning_protection,
emergency_lighting, whitespace

The same join-key risk applies to `parameter`. Prefer the shortest common
engineering name over a literal restatement of the clause's wording, e.g.
prefer "fuel_runtime" over "fuel_storage_tank_runtime", "load_acceptance_time"
over "full_load_acceptance_time", "power_rating" over "prime_power_rating"
unless "prime" is itself the distinguishing spec (standby vs. prime rating).

This vocabulary is shared with the extractor reading the OTHER document in
the same compliance check (spec vs. submittal) — if you invent a different
name for the same equipment or parameter, the two documents can never be
matched, and the check will silently report INSUFFICIENT_DATA. Only invent a
new snake_case equipment_class if none of the above plausibly fits.
"""

_REQUIREMENT_SYSTEM_PROMPT = """\
You extract engineering constraints from data-centre EPC specification clauses.

Rules:
- One clause can contain MULTIPLE independent constraints. Split them into
  separate entries. Do not merge unrelated parameters into one entry.
- A condition (ambient temperature, load %, power factor, measurement point,
  etc.) attaches ONLY to the constraint it grammatically modifies. If a clause
  has two constraints and only one has a stated condition, leave the other
  constraint's condition as null. Never let a condition leak across constraints.
- Infer the operator from the phrasing: "not less than" / "minimum of" /
  "at least" -> ">="; "not exceeding" / "maximum of" / "not more than" -> "<=";
  a single fixed nominal value (e.g. tolerance "X +/- Y") -> "==".
- Record the unit exactly as written in the text. Do not convert units.
- Use lowercase snake_case for equipment_class and parameter.
- If the clause states a req_id/clause number (e.g. "3.4.2"), extract it
  verbatim. Otherwise leave req_id null.
- Extract only what the text states. Never invent a constraint that isn't there.

""" + _CANONICAL_VOCABULARY + """
Example 1:
Clause: "Each chiller shall be capable of delivering not less than 500 TR at
35C ambient, with a minimum IPLV of 6.2."
Output:
[
  {"req_id": null, "equipment_class": "chiller", "parameter": "cooling_capacity",
   "operator": ">=", "value": 500.0, "unit": "TR", "condition": "@35C ambient"},
  {"req_id": null, "equipment_class": "chiller", "parameter": "iplv",
   "operator": ">=", "value": 6.2, "unit": "", "condition": null}
]
Note IPLV has NO condition, even though it's in the same sentence as the
ambient-conditioned capacity constraint — the ambient condition modifies
capacity, not IPLV.

Example 2:
Clause: "3.4.2 Transformers shall be rated not less than 2000 kVA with an
impedance of 6% plus or minus 0.5%."
Output:
[
  {"req_id": "3.4.2", "equipment_class": "transformer", "parameter": "power_rating",
   "operator": ">=", "value": 2000.0, "unit": "kVA", "condition": null},
  {"req_id": "3.4.2", "equipment_class": "transformer", "parameter": "impedance",
   "operator": "==", "value": 6.0, "unit": "%", "condition": null}
]
"""

_VALUE_SYSTEM_PROMPT = """\
You extract stated equipment values from vendor submittal / cut-sheet text.

Rules:
- Record values exactly as stated; do not convert units.
- A condition (ambient temperature, load %, measurement point, etc.) attaches
  only to the value it modifies.
- Use lowercase snake_case for equipment_class and parameter, matching the
  vocabulary a spec would use (e.g. "cooling_capacity", not "capacity").
- Set extraction_confidence lower (< 0.7) when the text is ambiguous, uses
  non-standard phrasing, or the value/unit pairing is unclear.
- Extract only what the text states. Never invent a value that isn't there.

""" + _CANONICAL_VOCABULARY + """
Example:
Text: "Cooling Capacity: 480 TR @ 35C Ambient"
Output:
[
  {"equipment_class": "chiller", "parameter": "cooling_capacity", "value": 480.0,
   "unit": "TR", "condition": "@35C ambient", "extraction_confidence": 0.95}
]
"""


def extract_requirements(spec_chunks: list[DocChunk]) -> list[Requirement]:
    """Extract typed Requirements from parsed spec text chunks. One offline
    LLM call per chunk; provenance is attached from the chunk, not the model."""
    client = _client()
    results: list[Requirement] = []

    for chunk in spec_chunks:
        batch = client.chat.completions.create(
            model=MODEL,
            response_model=_RequirementBatch,
            max_retries=MAX_RETRIES,
            messages=[
                {"role": "system", "content": _REQUIREMENT_SYSTEM_PROMPT},
                {"role": "user", "content": chunk.text},
            ],
        )
        for i, req in enumerate(batch.requirements):
            results.append(
                Requirement(
                    req_id=req.req_id or f"{chunk.source_doc}-p{chunk.page}-{i}",
                    equipment_class=req.equipment_class,
                    parameter=req.parameter,
                    operator=req.operator,
                    value=req.value,
                    unit=req.unit,
                    condition=req.condition,
                    source_doc=chunk.source_doc,
                    source_page=chunk.page,
                    source_bbox=chunk.bbox,
                )
            )

    return results


def extract_values(submittal_chunks: list[DocChunk]) -> list[ExtractedValue]:
    """Extract typed ExtractedValues from parsed submittal text/table chunks."""
    client = _client()
    results: list[ExtractedValue] = []

    for chunk in submittal_chunks:
        batch = client.chat.completions.create(
            model=MODEL,
            response_model=_ValueBatch,
            max_retries=MAX_RETRIES,
            messages=[
                {"role": "system", "content": _VALUE_SYSTEM_PROMPT},
                {"role": "user", "content": chunk.text},
            ],
        )
        for val in batch.values:
            results.append(
                ExtractedValue(
                    equipment_class=val.equipment_class,
                    parameter=val.parameter,
                    value=val.value,
                    unit=val.unit,
                    condition=val.condition,
                    source_doc=chunk.source_doc,
                    source_page=chunk.page,
                    source_bbox=chunk.bbox,
                    extraction_confidence=val.extraction_confidence,
                )
            )

    return results
