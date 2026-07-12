from typing import Any

from ingestion.evaluate_requirements import _matches, _values_match


def _req(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "equipment_class": "chiller",
        "parameter": "cooling_capacity",
        "operator": ">=",
        "value": 500.0,
        "unit": "TR",
        "condition": "@35C ambient",
    }
    base.update(overrides)
    return base


def test_values_match_identical_unit() -> None:
    assert _values_match(_req(value=500.0, unit="TR"), _req(value=500.0, unit="TR"))


def test_values_match_via_pint_conversion_kw_vs_tr() -> None:
    # 500 TR == 500 * 3.5168528... kW exactly, per the TR alias in app.core.units
    assert _values_match(_req(value=500.0, unit="TR"), _req(value=1758.4266666666667, unit="kW"))


def test_values_match_gpm_alias() -> None:
    assert _values_match(_req(value=750.0, unit="GPM"), _req(value=750.0, unit="GPM"))


def test_values_match_dba_same_unit() -> None:
    assert _values_match(_req(value=85.0, unit="dBA"), _req(value=85.0, unit="dBA"))


def test_values_do_not_match_different_magnitude() -> None:
    assert not _values_match(_req(value=500.0, unit="TR"), _req(value=480.0, unit="TR"))


def test_values_do_not_match_incompatible_units() -> None:
    assert not _values_match(_req(value=500.0, unit="TR"), _req(value=500.0, unit="meter"))


def test_values_match_unitless() -> None:
    assert _values_match(_req(value=6.2, unit=""), _req(value=6.2, unit=""))


def test_matches_full_requirement() -> None:
    assert _matches(_req(), _req())


def test_matches_fails_on_equipment_class_mismatch() -> None:
    assert not _matches(_req(equipment_class="chiller"), _req(equipment_class="pump"))


def test_matches_fails_on_parameter_mismatch() -> None:
    assert not _matches(_req(parameter="cooling_capacity"), _req(parameter="iplv"))


def test_matches_fails_on_operator_mismatch() -> None:
    assert not _matches(_req(operator=">="), _req(operator="<="))


def test_matches_is_condition_presence_based_not_exact_text() -> None:
    # Different wording, both non-None -> still matches. This is the
    # documented tradeoff: exact condition phrasing isn't required, but a
    # condition leaking onto/off of a constraint (None vs non-None) still
    # fails the match.
    assert _matches(
        _req(condition="@35C ambient"),
        _req(condition="at 35 degrees C ambient temperature"),
    )


def test_matches_fails_when_condition_present_on_only_one_side() -> None:
    assert not _matches(_req(condition="@35C ambient"), _req(condition=None))
    assert not _matches(_req(condition=None), _req(condition="@35C ambient"))
