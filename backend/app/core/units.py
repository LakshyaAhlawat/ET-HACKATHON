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
