"""Validates extract_requirements() against the hand-labelled clause set.

Usage: python -m ingestion.evaluate_requirements
Reads data/ground_truth/requirement_clauses.json, runs each clause through
the real extractor, and reports per-field matches so a human can review
where the prompt over- or under-extracts. Writes a machine-readable report
to data/benchmark/requirement_extraction_eval.json.
"""

import json
import math
from pathlib import Path
from typing import Any

from app.core.units import ureg
from ingestion.extract import extract_requirements
from ingestion.models import DocChunk

ROOT = Path(__file__).resolve().parent.parent.parent
GROUND_TRUTH_PATH = ROOT / "data" / "ground_truth" / "requirement_clauses.json"
REPORT_PATH = ROOT / "data" / "benchmark" / "requirement_extraction_eval.json"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split()).lower()
    return value


def _values_match(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    """Compares value+unit the same way the real deterministic evaluator
    does: via pint conversion, not string equality on the unit spelling
    (the model writing "seconds" instead of "s" is not a bug — pint parses
    both identically)."""
    e_value, a_value = expected.get("value"), actual.get("value")
    e_unit, a_unit = expected.get("unit") or "", actual.get("unit") or ""
    if e_value is None or a_value is None:
        return False
    if e_unit == "" and a_unit == "":
        return math.isclose(e_value, a_value, rel_tol=1e-6, abs_tol=1e-6)
    try:
        converted = ureg.Quantity(a_value, a_unit).to(e_unit).magnitude
    except Exception:
        # Any pint parse/conversion failure (unrecognized unit, a hyphenated
        # unit string like "foot-candle" parsed as subtraction, etc.) means
        # the units aren't independently verifiable as equivalent — treat as
        # a non-match rather than crashing the eval run.
        return False
    return math.isclose(e_value, converted, rel_tol=1e-6, abs_tol=1e-6)


def _matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    if _normalize(expected.get("equipment_class")) != _normalize(actual.get("equipment_class")):
        return False
    if _normalize(expected.get("parameter")) != _normalize(actual.get("parameter")):
        return False
    if expected.get("operator") != actual.get("operator"):
        return False
    if not _values_match(expected, actual):
        return False
    # Condition is free text; what matters is whether it's attached to the
    # RIGHT constraint (present vs. absent), not exact wording — this still
    # catches the load-bearing bug of a condition leaking onto a sibling
    # constraint that shouldn't have one (see CLAUDE.md).
    return (expected.get("condition") is None) == (actual.get("condition") is None)


def evaluate() -> dict[str, Any]:
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    clause_reports = []
    total_expected = 0
    total_matched = 0

    for clause in ground_truth:
        chunk = DocChunk(
            text=clause["text"],
            source_doc="ground_truth",
            page=1,
            bbox=(0.0, 0.0, 0.0, 0.0),
        )
        extracted = extract_requirements([chunk])
        actual_dicts = [r.model_dump() for r in extracted]
        expected_list = clause["expected_requirements"]

        matched_actual_indices: set[int] = set()
        matches = []
        for expected in expected_list:
            match_idx = next(
                (
                    i
                    for i, actual in enumerate(actual_dicts)
                    if i not in matched_actual_indices and _matches(expected, actual)
                ),
                None,
            )
            if match_idx is not None:
                matched_actual_indices.add(match_idx)
            matches.append({"expected": expected, "matched": match_idx is not None})

        total_expected += len(expected_list)
        total_matched += sum(1 for m in matches if m["matched"])

        clause_reports.append(
            {
                "clause_id": clause["clause_id"],
                "text": clause["text"],
                "expected_count": len(expected_list),
                "extracted_count": len(actual_dicts),
                "matched_count": sum(1 for m in matches if m["matched"]),
                "matches": matches,
                "extracted": actual_dicts,
            }
        )

    report = {
        "total_clauses": len(ground_truth),
        "total_expected_requirements": total_expected,
        "total_matched_requirements": total_matched,
        "accuracy": total_matched / total_expected if total_expected else 0.0,
        "clauses": clause_reports,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    return report


def _print_summary(report: dict[str, Any]) -> None:
    print(f"{'clause':<8} {'expected':>8} {'matched':>8}  text")
    for c in report["clauses"]:
        flag = " " if c["matched_count"] == c["expected_count"] else "!"
        print(
            f"{flag}{c['clause_id']:<7} {c['expected_count']:>8} {c['matched_count']:>8}  "
            f"{c['text'][:70]}"
        )
    print()
    print(
        f"TOTAL: {report['total_matched_requirements']}/{report['total_expected_requirements']} "
        f"requirements matched ({report['accuracy']:.1%})"
    )
    print(f"Full report written to {REPORT_PATH}")


if __name__ == "__main__":
    _print_summary(evaluate())
