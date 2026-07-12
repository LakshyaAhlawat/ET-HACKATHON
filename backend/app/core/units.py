from typing import Any

import pint

ureg: Any = pint.UnitRegistry()
ureg.define("TR = refrigeration_ton")
