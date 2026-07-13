import math
from collections.abc import Callable

import pint

from app.core.units import (
    convert_apparent_real_power,
    extract_power_factor,
    is_power_factor_pair,
    ureg,
)
from app.models.schema import ExtractedValue, Requirement, SourceRegion, Verdict

_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">=": lambda actual, target: actual >= target,
    "<=": lambda actual, target: actual <= target,
    "==": lambda actual, target: math.isclose(actual, target, rel_tol=1e-9, abs_tol=1e-9),
    "!=": lambda actual, target: not math.isclose(actual, target, rel_tol=1e-9, abs_tol=1e-9),
}


def _normalize_condition(condition: str | None) -> str | None:
    """Case- and whitespace-insensitive, including whitespace *inside* the
    string (e.g. "@35C ambient" vs "@ 35C Ambient" from two independent LLM
    extractions of the same physical condition) -- collapsing runs to a
    single space isn't enough, since "@" with or without a following space
    still produces a different token count after a plain .split()."""
    if condition is None:
        return None
    return "".join(condition.split()).lower()


def _format_quantity(value: float, unit: str, condition: str | None) -> str:
    text = f"{value} {unit}"
    if condition:
        text = f"{text} {condition}"
    return text


def _spec_evidence(req: Requirement) -> SourceRegion:
    return SourceRegion(
        source_doc=req.source_doc,
        source_page=req.source_page,
        source_bbox=req.source_bbox,
    )


def _submittal_evidence(ev: ExtractedValue) -> SourceRegion:
    return SourceRegion(
        source_doc=ev.source_doc,
        source_page=ev.source_page,
        source_bbox=ev.source_bbox,
    )


def _insufficient_data(req: Requirement, reason: str, required_text: str) -> Verdict:
    return Verdict(
        req_id=req.req_id,
        status="INSUFFICIENT_DATA",
        required=required_text,
        submitted=None,
        delta_pct=None,
        reason=reason,
        spec_evidence=_spec_evidence(req),
        submittal_evidence=None,
    )


def evaluate_requirement(
    requirement: Requirement, extracted_values: list[ExtractedValue]
) -> Verdict:
    """Deterministically compare a spec requirement against extracted submittal values.

    Returns PASS / NON_CONFORMANCE / INSUFFICIENT_DATA. Never guesses: any missing
    or ambiguous condition, unmatched equipment/parameter, or incompatible unit
    yields INSUFFICIENT_DATA rather than a hallucinated pass.
    """
    required_text = f"{requirement.operator} {requirement.value} {requirement.unit}"
    if requirement.condition:
        required_text = f"{required_text} {requirement.condition}"

    candidates = [
        ev
        for ev in extracted_values
        if ev.equipment_class == requirement.equipment_class
        and ev.parameter == requirement.parameter
    ]
    if not candidates:
        return _insufficient_data(
            requirement,
            reason=(
                f"No submittal data found for {requirement.equipment_class}.{requirement.parameter}"
            ),
            required_text=required_text,
        )

    req_condition = _normalize_condition(requirement.condition)
    if req_condition is not None:
        candidates = [
            ev for ev in candidates if _normalize_condition(ev.condition) == req_condition
        ]
        if not candidates:
            return _insufficient_data(
                requirement,
                reason=(
                    f"Submittal does not state a value for {requirement.equipment_class}."
                    f"{requirement.parameter} under condition '{requirement.condition}'"
                ),
                required_text=required_text,
            )

    match = max(candidates, key=lambda ev: ev.extraction_confidence)

    if is_power_factor_pair(match.unit, requirement.unit):
        power_factor = extract_power_factor(requirement.condition) or extract_power_factor(
            match.condition
        )
        if power_factor is None:
            # THE FALSE-PASS TRAP: apparent power (kVA) and real power (kW)
            # share a pint dimension, so a bare conversion would silently
            # treat "1500 kVA" and "1500 kW" as equal. Without a stated power
            # factor we cannot relate them — refuse rather than guess.
            return _insufficient_data(
                requirement,
                reason=(
                    f"Cannot compare '{match.unit}' to '{requirement.unit}' for "
                    f"{requirement.equipment_class}.{requirement.parameter} without a stated "
                    "power factor"
                ),
                required_text=required_text,
            )
        actual_value = convert_apparent_real_power(
            match.value, match.unit, requirement.unit, power_factor
        )
    else:
        try:
            actual_value = ureg.Quantity(match.value, match.unit).to(requirement.unit).magnitude
        except pint.errors.DimensionalityError:
            return _insufficient_data(
                requirement,
                reason=(
                    f"Submittal unit '{match.unit}' is not compatible with required unit "
                    f"'{requirement.unit}' for {requirement.equipment_class}."
                    f"{requirement.parameter}"
                ),
                required_text=required_text,
            )
        except pint.errors.UndefinedUnitError as exc:
            return _insufficient_data(
                requirement,
                reason=f"Unrecognized unit while comparing submittal to requirement: {exc}",
                required_text=required_text,
            )

    if requirement.operator not in _OPERATORS:
        return _insufficient_data(
            requirement,
            reason=f"Operator '{requirement.operator}' is not supported for scalar comparison",
            required_text=required_text,
        )

    passes = _OPERATORS[requirement.operator](actual_value, requirement.value)
    delta_pct = (actual_value - requirement.value) / requirement.value * 100

    return Verdict(
        req_id=requirement.req_id,
        status="PASS" if passes else "NON_CONFORMANCE",
        required=required_text,
        submitted=_format_quantity(match.value, match.unit, match.condition),
        delta_pct=delta_pct,
        reason="",
        spec_evidence=_spec_evidence(requirement),
        submittal_evidence=_submittal_evidence(match),
    )
