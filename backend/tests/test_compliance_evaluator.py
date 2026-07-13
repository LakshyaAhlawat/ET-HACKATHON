from typing import Any

import pytest

from app.models.schema import ExtractedValue, Requirement
from app.services.compliance.evaluator import evaluate_requirement

SPEC_DOC = "spec.pdf"
SUBMITTAL_DOC = "vendor_submittal.pdf"


def make_requirement(**overrides: Any) -> Requirement:
    defaults = dict(
        req_id="MECH-3.4.2",
        equipment_class="chiller",
        parameter="cooling_capacity",
        operator=">=",
        value=500.0,
        unit="TR",
        condition=None,
        source_doc=SPEC_DOC,
        source_page=12,
        source_bbox=(10.0, 20.0, 200.0, 60.0),
    )
    defaults.update(overrides)
    return Requirement(**defaults)  # type: ignore[arg-type]


def make_extracted(**overrides: Any) -> ExtractedValue:
    defaults = dict(
        equipment_class="chiller",
        parameter="cooling_capacity",
        value=550.0,
        unit="TR",
        condition=None,
        source_doc=SUBMITTAL_DOC,
        source_page=4,
        source_bbox=(15.0, 25.0, 210.0, 65.0),
        extraction_confidence=0.95,
    )
    defaults.update(overrides)
    return ExtractedValue(**defaults)  # type: ignore[arg-type]


def test_pass_simple_same_unit() -> None:
    req = make_requirement()
    ev = make_extracted(value=550.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"
    assert verdict.req_id == "MECH-3.4.2"
    assert verdict.required == ">= 500.0 TR"
    assert verdict.submitted == "550.0 TR"
    assert verdict.delta_pct == pytest.approx(10.0)
    assert verdict.spec_evidence.source_doc == SPEC_DOC
    assert verdict.submittal_evidence is not None
    assert verdict.submittal_evidence.source_doc == SUBMITTAL_DOC


def test_non_conformance_simple() -> None:
    req = make_requirement()
    ev = make_extracted(value=480.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"
    assert verdict.delta_pct == pytest.approx(-4.0)
    assert verdict.submitted == "480.0 TR"


def test_unit_conversion_kw_pass() -> None:
    # 500 TR ~= 1758.43 kW; 1900 kW ~= 540.3 TR -> PASS
    req = make_requirement()
    ev = make_extracted(value=1900.0, unit="kW")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"
    assert verdict.submitted == "1900.0 kW"
    assert verdict.delta_pct == pytest.approx(540.2556831106596 / 500.0 * 100 - 100, rel=1e-6)


def test_unit_conversion_kw_non_conformance() -> None:
    # 1700 kW ~= 483.4 TR -> below 500 TR requirement
    req = make_requirement()
    ev = make_extracted(value=1700.0, unit="kW")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"
    assert verdict.delta_pct is not None
    assert verdict.delta_pct < 0


def test_condition_required_but_missing_is_insufficient_data() -> None:
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition=None)

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submitted is None
    assert verdict.submittal_evidence is None
    assert "@35C ambient" in verdict.reason


def test_condition_mismatch_is_insufficient_data() -> None:
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="@25C ambient")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submitted is None


def test_condition_match_pass() -> None:
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="@35C ambient")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"
    assert verdict.required == ">= 500.0 TR @35C ambient"
    assert verdict.submitted == "550.0 TR @35C ambient"


def test_condition_match_is_case_and_whitespace_insensitive() -> None:
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="  @35c Ambient ")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_condition_match_is_insensitive_to_internal_whitespace() -> None:
    # Two independent LLM extractions of the same physical condition don't
    # reliably agree on whether there's a space right after "@" -- that's
    # formatting noise, not a different condition, and must not by itself
    # turn a real deviation into a false INSUFFICIENT_DATA.
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="@ 35C Ambient")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_no_matching_equipment_is_insufficient_data() -> None:
    req = make_requirement()
    ev = make_extracted(equipment_class="pump", parameter="flow_rate", value=100.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submittal_evidence is None
    assert "no submittal data" in verdict.reason.lower()


def test_no_extracted_values_at_all_is_insufficient_data() -> None:
    req = make_requirement()

    verdict = evaluate_requirement(req, [])

    assert verdict.status == "INSUFFICIENT_DATA"


def test_incompatible_units_is_insufficient_data() -> None:
    req = make_requirement()
    ev = make_extracted(value=550.0, unit="meter")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert "unit" in verdict.reason.lower()


def test_equality_operator_pass() -> None:
    req = make_requirement(operator="==", value=500.0)
    ev = make_extracted(value=500.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_equality_operator_non_conformance() -> None:
    req = make_requirement(operator="==", value=500.0)
    ev = make_extracted(value=500.5, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"


def test_not_equal_operator() -> None:
    req = make_requirement(operator="!=", value=500.0)
    ev = make_extracted(value=500.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"


def test_less_than_or_equal_operator() -> None:
    req = make_requirement(operator="<=", value=500.0)
    ev = make_extracted(value=480.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_picks_highest_confidence_when_multiple_unconditioned_matches() -> None:
    req = make_requirement()
    low_conf = make_extracted(value=480.0, unit="TR", extraction_confidence=0.4)
    high_conf = make_extracted(value=550.0, unit="TR", extraction_confidence=0.9)

    verdict = evaluate_requirement(req, [low_conf, high_conf])

    assert verdict.status == "PASS"
    assert verdict.submitted == "550.0 TR"


def test_1688_kw_resolves_to_480_tr_not_480_kw() -> None:
    # The literal trap from CLAUDE.md: 1688 kW must be unit-converted to ~480
    # TR before comparison (delta ~0%), not compared as a raw magnitude
    # against 480 (which would be wildly, obviously wrong: -71.6%).
    req = make_requirement(operator=">=", value=480.0, unit="TR")
    ev = make_extracted(value=1688.0, unit="kW")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"  # 479.97 TR is a hair under the 480 TR boundary
    assert verdict.delta_pct == pytest.approx(0.0, abs=0.1)


def test_dimensionless_ratio_iplv_pass() -> None:
    req = make_requirement(parameter="iplv", operator=">=", value=6.2, unit="")
    ev = make_extracted(parameter="iplv", value=6.5, unit="")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_dimensionless_ratio_cop_non_conformance() -> None:
    req = make_requirement(parameter="cop", operator=">=", value=3.5, unit="")
    ev = make_extracted(parameter="cop", value=3.2, unit="")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"


def test_kva_to_kw_with_stated_power_factor_pass() -> None:
    # Generator rated >= 1500 kVA @0.8 PF; submittal states 1300 kW @0.8 PF.
    # 1300 kW / 0.8 PF = 1625 kVA >= 1500 -> PASS.
    req = make_requirement(
        equipment_class="generator",
        parameter="prime_power_rating",
        operator=">=",
        value=1500.0,
        unit="kVA",
        condition="@0.8 lagging power factor",
    )
    ev = make_extracted(
        equipment_class="generator",
        parameter="prime_power_rating",
        value=1300.0,
        unit="kW",
        condition="@0.8 lagging power factor",
    )

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_kva_to_kw_without_power_factor_is_insufficient_data() -> None:
    # THE FALSE-PASS TRAP: pint treats kVA and kW as dimensionally identical
    # (both reduce to the same SI power dimension) and would silently permit
    # `.to()` between them with no conversion at all — meaning "1500 kW"
    # would naively satisfy "1500 kVA" even though real vs. apparent power
    # are only related via a power factor. Without a stated PF anywhere, the
    # evaluator must refuse to compare rather than silently treat them as equal.
    req = make_requirement(
        equipment_class="generator",
        parameter="prime_power_rating",
        operator=">=",
        value=1500.0,
        unit="kVA",
        condition=None,
    )
    ev = make_extracted(
        equipment_class="generator",
        parameter="prime_power_rating",
        value=1500.0,
        unit="kW",
        condition=None,
    )

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert "power factor" in verdict.reason.lower()


def test_kw_to_kva_with_stated_power_factor_non_conformance() -> None:
    # Requirement in kW, submittal in kVA. As in a real cut-sheet, kVA/PF are
    # stated together as one rating, so both sides restate the condition —
    # the evaluator must not fall back to an unconditioned value (session
    # rule), so the condition has to match before PF conversion even applies.
    # 1000 kVA * 0.8 PF = 800 kW < 1000 kW required -> NON_CONFORMANCE.
    req = make_requirement(
        equipment_class="generator",
        parameter="prime_power_rating",
        operator=">=",
        value=1000.0,
        unit="kW",
        condition="@0.8 PF",
    )
    ev = make_extracted(
        equipment_class="generator",
        parameter="prime_power_rating",
        value=1000.0,
        unit="kVA",
        condition="@0.8 PF",
    )

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"
