from app.models.rfi import ClaimExtraction
from rfi.dedup import _claims_contradict, _hidden_caveat_contradiction, _numeric_contradiction
from rfi.parse import load_rfi_log


def _claim(**overrides: object) -> ClaimExtraction:
    defaults: dict[str, object] = {
        "subject": "chilled_water_supply_temperature",
        "stated_value": 12.0,
        "unit": "C",
        "condition": None,
        "is_definitive": True,
        "has_unstated_caveat": False,
    }
    defaults.update(overrides)
    return ClaimExtraction.model_validate(defaults)


def test_numeric_contradiction_flags_values_beyond_tolerance() -> None:
    a = _claim(stated_value=12.0)
    b = _claim(stated_value=13.0)  # ~8.3% delta, well beyond the 3% tolerance
    assert _numeric_contradiction(a, b) is True


def test_numeric_contradiction_ignores_values_within_tolerance() -> None:
    a = _claim(stated_value=100.0)
    b = _claim(stated_value=101.0)  # 1% delta
    assert _numeric_contradiction(a, b) is False


def test_numeric_contradiction_requires_both_definitive() -> None:
    a = _claim(stated_value=12.0, is_definitive=True)
    b = _claim(stated_value=20.0, is_definitive=False)  # a hedge, not a firm claim
    assert _numeric_contradiction(a, b) is False


def test_numeric_contradiction_requires_matching_units() -> None:
    a = _claim(stated_value=500.0, unit="TR")
    b = _claim(stated_value=500.0, unit="kW")  # same number, incompatible unit
    assert _numeric_contradiction(a, b) is False


def test_hidden_caveat_contradiction_fires_when_one_side_is_unconditional() -> None:
    a = _claim(is_definitive=True, has_unstated_caveat=False)
    b = _claim(is_definitive=True, has_unstated_caveat=True)
    assert _hidden_caveat_contradiction(a, b) is True


def test_hidden_caveat_contradiction_does_not_fire_when_both_have_caveats() -> None:
    a = _claim(is_definitive=True, has_unstated_caveat=True)
    b = _claim(is_definitive=True, has_unstated_caveat=True)
    assert _hidden_caveat_contradiction(a, b) is False


def test_claims_contradict_requires_matching_subject() -> None:
    a = _claim(subject="chilled_water_supply_temperature", stated_value=12.0)
    b = _claim(subject="hvac_setpoint", stated_value=24.0)
    assert _claims_contradict(a, b) is False


def test_claims_contradict_is_case_insensitive_on_subject() -> None:
    a = _claim(subject="Battery_Interval", stated_value=10.0, unit="years")
    b = _claim(subject="battery_interval", stated_value=5.0, unit="years")
    assert _claims_contradict(a, b) is True


def test_load_rfi_log_parses_all_entries_with_required_fields() -> None:
    records = load_rfi_log()
    assert len(records) > 0
    for record in records:
        assert record.rfi_id.startswith("RFI-")
        assert record.question
        assert record.response


def test_load_rfi_log_finds_the_water_temperature_entry() -> None:
    records = {r.rfi_id: r for r in load_rfi_log()}
    assert "RFI-0124" in records
    assert "chilled water" in records["RFI-0124"].title.lower()
