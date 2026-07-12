import re
from typing import Any

import pint

ureg: Any = pint.UnitRegistry()
ureg.define("TR = refrigeration_ton")
# Common EPC/HVAC units pint doesn't ship by default. Missing one of these is
# the same failure mode as TR: a real spec-vs-submittal comparison silently
# turns into INSUFFICIENT_DATA ("incompatible units") even though both sides
# used a standard industry unit.
ureg.define("GPM = gallon / minute")
ureg.define("footcandle = 10.76391041671 * lux = fc")
# A-weighted sound level has no linear relationship to other units (it bakes
# in a frequency-weighting curve) — modeled as its own dimension so dBA-to-dBA
# comparisons work, while conversion to any other unit correctly still fails.
ureg.define("dBA = [sound_level_a]")

# Apparent power (VA/kVA/MVA) and real power (W/kW/MW) share the same SI
# dimension (both reduce to kg*m^2/s^3), so pint's `.to()` will silently
# convert between them numerically as if they were equal — e.g. "1500 kVA"
# would trivially satisfy "1500 kW". They're only actually related by a power
# factor (P = S * PF), which varies per equipment and must come from the
# document text. This must never be a bare pint conversion.
_APPARENT_POWER_UNITS = {"va", "kva", "mva"}
_REAL_POWER_UNITS = {"w", "kw", "mw"}

_POWER_FACTOR_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:lagging|leading)?\s*(?:power factor|pf)\b", re.IGNORECASE
)


def is_power_factor_pair(unit_a: str, unit_b: str) -> bool:
    """True if unit_a/unit_b are one apparent-power and one real-power unit —
    a pair that requires an explicit power factor to compare, not a bare
    pint conversion."""
    a, b = unit_a.strip().lower(), unit_b.strip().lower()
    return (a in _APPARENT_POWER_UNITS and b in _REAL_POWER_UNITS) or (
        a in _REAL_POWER_UNITS and b in _APPARENT_POWER_UNITS
    )


def extract_power_factor(condition: str | None) -> float | None:
    """Extracts a stated power factor, e.g. 0.8 from "@0.8 lagging power
    factor". Returns None if no power factor is stated — callers must treat
    that as INSUFFICIENT_DATA, never assume PF=1."""
    if not condition:
        return None
    match = _POWER_FACTOR_PATTERN.search(condition)
    return float(match.group(1)) if match else None


def convert_apparent_real_power(
    value: float, from_unit: str, to_unit: str, power_factor: float
) -> float:
    """Converts between apparent power (VA/kVA/MVA) and real power (W/kW/MW)
    given an explicit power factor: P = S * PF.

    Pint is used only for the safe part — rescaling SI prefixes (kVA -> MW
    magnitude, etc.), which is dimensionally sound since VA and W share a
    dimension. The power-factor multiplication/division is applied
    separately, since that physical relationship isn't something pint knows.
    """
    from_lower = from_unit.strip().lower()
    to_lower = to_unit.strip().lower()
    prefix_scaled = ureg.Quantity(value, from_unit).to(to_unit).magnitude

    if from_lower in _APPARENT_POWER_UNITS and to_lower in _REAL_POWER_UNITS:
        return float(prefix_scaled * power_factor)
    return float(prefix_scaled / power_factor)
