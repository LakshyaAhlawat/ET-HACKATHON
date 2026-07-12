import pytest

from app.models.schema import ExtractedValue, Requirement
from app.services.compliance.evaluator import evaluate_requirement

SPEC_DOC = "spec.pdf"
SUBMITTAL_DOC = "vendor_submittal.pdf"


def make_requirement(**overrides) -> Requirement:
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
    return Requirement(**defaults)


def make_extracted(**overrides) -> ExtractedValue:
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
    return ExtractedValue(**defaults)


def test_pass_simple_same_unit():
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


def test_non_conformance_simple():
    req = make_requirement()
    ev = make_extracted(value=480.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"
    assert verdict.delta_pct == pytest.approx(-4.0)
    assert verdict.submitted == "480.0 TR"


def test_unit_conversion_kw_pass():
    # 500 TR ~= 1758.43 kW; 1900 kW ~= 540.3 TR -> PASS
    req = make_requirement()
    ev = make_extracted(value=1900.0, unit="kW")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"
    assert verdict.submitted == "1900.0 kW"
    assert verdict.delta_pct == pytest.approx(540.2556831106596 / 500.0 * 100 - 100, rel=1e-6)


def test_unit_conversion_kw_non_conformance():
    # 1700 kW ~= 483.4 TR -> below 500 TR requirement
    req = make_requirement()
    ev = make_extracted(value=1700.0, unit="kW")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"
    assert verdict.delta_pct < 0


def test_condition_required_but_missing_is_insufficient_data():
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition=None)

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submitted is None
    assert verdict.submittal_evidence is None
    assert "@35C ambient" in verdict.reason


def test_condition_mismatch_is_insufficient_data():
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="@25C ambient")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submitted is None


def test_condition_match_pass():
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="@35C ambient")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"
    assert verdict.required == ">= 500.0 TR @35C ambient"
    assert verdict.submitted == "550.0 TR @35C ambient"


def test_condition_match_is_case_and_whitespace_insensitive():
    req = make_requirement(condition="@35C ambient")
    ev = make_extracted(value=550.0, unit="TR", condition="  @35c Ambient ")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_no_matching_equipment_is_insufficient_data():
    req = make_requirement()
    ev = make_extracted(equipment_class="pump", parameter="flow_rate", value=100.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert verdict.submittal_evidence is None
    assert "no submittal data" in verdict.reason.lower()


def test_no_extracted_values_at_all_is_insufficient_data():
    req = make_requirement()

    verdict = evaluate_requirement(req, [])

    assert verdict.status == "INSUFFICIENT_DATA"


def test_incompatible_units_is_insufficient_data():
    req = make_requirement()
    ev = make_extracted(value=550.0, unit="meter")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "INSUFFICIENT_DATA"
    assert "unit" in verdict.reason.lower()


def test_equality_operator_pass():
    req = make_requirement(operator="==", value=500.0)
    ev = make_extracted(value=500.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_equality_operator_non_conformance():
    req = make_requirement(operator="==", value=500.0)
    ev = make_extracted(value=500.5, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"


def test_not_equal_operator():
    req = make_requirement(operator="!=", value=500.0)
    ev = make_extracted(value=500.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "NON_CONFORMANCE"


def test_less_than_or_equal_operator():
    req = make_requirement(operator="<=", value=500.0)
    ev = make_extracted(value=480.0, unit="TR")

    verdict = evaluate_requirement(req, [ev])

    assert verdict.status == "PASS"


def test_picks_highest_confidence_when_multiple_unconditioned_matches():
    req = make_requirement()
    low_conf = make_extracted(value=480.0, unit="TR", extraction_confidence=0.4)
    high_conf = make_extracted(value=550.0, unit="TR", extraction_confidence=0.9)

    verdict = evaluate_requirement(req, [low_conf, high_conf])

    assert verdict.status == "PASS"
    assert verdict.submitted == "550.0 TR"
