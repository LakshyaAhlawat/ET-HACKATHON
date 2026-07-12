import pytest

from app.core.units import (
    convert_apparent_real_power,
    extract_power_factor,
    is_power_factor_pair,
    ureg,
)


def test_tr_to_kw_matches_known_conversion() -> None:
    # 500 TR is the canonical example from CLAUDE.md
    assert ureg.Quantity(500, "TR").to("kW").magnitude == pytest.approx(1758.4265, rel=1e-5)


def test_1688_kw_resolves_to_480_tr_not_480_kw() -> None:
    # The literal trap: naive/no conversion would compare 1688 against 480
    # directly (as if unit were ignored) and get it wrong either way. Correct
    # unit-aware conversion must land on ~480 TR.
    tr = ureg.Quantity(1688, "kW").to("TR").magnitude
    assert tr == pytest.approx(480.0, abs=0.1)


def test_tr_to_btu_per_hour() -> None:
    # 1 TR = 12000 BTU/hr by definition
    assert ureg.Quantity(1, "TR").to("BTU/hour").magnitude == pytest.approx(12000, rel=1e-3)


def test_btu_per_hour_round_trips_through_kw_to_tr() -> None:
    btu_hr = ureg.Quantity(500, "TR").to("BTU/hour").magnitude
    back_to_tr = ureg.Quantity(btu_hr, "BTU/hour").to("TR").magnitude
    assert back_to_tr == pytest.approx(500.0, rel=1e-6)


def test_is_power_factor_pair_detects_kva_kw() -> None:
    assert is_power_factor_pair("kVA", "kW")
    assert is_power_factor_pair("kW", "kVA")
    assert is_power_factor_pair("MVA", "MW")


def test_is_power_factor_pair_false_for_same_family() -> None:
    assert not is_power_factor_pair("kVA", "MVA")
    assert not is_power_factor_pair("kW", "MW")


def test_is_power_factor_pair_false_for_unrelated_units() -> None:
    assert not is_power_factor_pair("TR", "kW")
    assert not is_power_factor_pair("TR", "kVA")


def test_extract_power_factor_from_condition() -> None:
    assert extract_power_factor("@0.8 lagging power factor") == pytest.approx(0.8)
    assert extract_power_factor("at 0.9 PF") == pytest.approx(0.9)
    assert extract_power_factor("0.85 leading power factor") == pytest.approx(0.85)


def test_extract_power_factor_returns_none_when_absent() -> None:
    assert extract_power_factor("@35C ambient") is None
    assert extract_power_factor(None) is None


def test_convert_apparent_to_real_power() -> None:
    # S * PF = P: 1500 kVA at 0.8 PF = 1200 kW
    result = convert_apparent_real_power(1500, "kVA", "kW", power_factor=0.8)
    assert result == pytest.approx(1200.0)


def test_convert_real_to_apparent_power() -> None:
    # P / PF = S: 1200 kW at 0.8 PF = 1500 kVA
    result = convert_apparent_real_power(1200, "kW", "kVA", power_factor=0.8)
    assert result == pytest.approx(1500.0)


def test_convert_apparent_real_power_handles_prefix_scaling() -> None:
    # 1.5 MVA at 0.8 PF = 1200 kW
    result = convert_apparent_real_power(1.5, "MVA", "kW", power_factor=0.8)
    assert result == pytest.approx(1200.0)
