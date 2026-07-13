# PR-Curve Negative-Class Controls

**Not part of the official 50-question ground-truth key.** The key's 15
planted deviations are all `NON_CONFORMANCE` or `INSUFFICIENT_DATA` — there
is no compliant (`PASS`) case among them, so on their own they cannot
populate the negative class a precision/recall curve needs (there's nothing
for the evaluator to falsely flag). These five control cases are
synthesized, clearly compliant, and added solely so
`benchmark/scoring.py` has true negatives to score false-positive rate
against. See `data/benchmark/pr_curve_controls.json` for the manifest and
`README.md` in this folder for the wider provenance disclosure.

### Clause CTRL-1 — Generator Prime Power
Diesel generator prime power rating shall be not less than 1500 kVA at 0.8
lagging power factor.
[FACT req_id=CTRL-1 equipment_class=generator parameter=prime_power_rating operator=>= value=1500 unit=kVA condition="@0.8 lagging PF"]

Submittal: Caterpillar generator, prime power rating 1600 kVA at 0.8
lagging power factor.
[FACT req_id=CTRL-1 equipment_class=generator parameter=prime_power_rating value=1600 unit=kVA condition="@0.8 lagging PF" source_doc="Caterpillar generator submittal" source_page=1 confidence=0.95]

### Clause CTRL-2 — Busway Current Rating
Busway shall be rated for continuous current of not less than 4000A.
[FACT req_id=CTRL-2 equipment_class=busway parameter=continuous_current operator=>= value=4000 unit=A condition=null]

Submittal: Busway continuous current rating 4500A.
[FACT req_id=CTRL-2 equipment_class=busway parameter=continuous_current value=4500 unit=A condition=null source_doc="Busway submittal" source_page=1 confidence=0.95]

### Clause CTRL-3 — UPS Input THDi
UPS input total harmonic distortion (THDi) shall not exceed 5% at full
load.
[FACT req_id=CTRL-3 equipment_class=ups parameter=input_thdi operator=<= value=5 unit=percent condition="@full load"]

Submittal: UPS input THDi measured at 3.2% at full load.
[FACT req_id=CTRL-3 equipment_class=ups parameter=input_thdi value=3.2 unit=percent condition="@full load" source_doc="UPS THDi test report" source_page=1 confidence=0.95]

### Clause CTRL-4 — Transformer Impedance
Distribution transformer impedance shall be not less than 5.5% and not
more than 6.5%.
[FACT req_id=CTRL-4 equipment_class=transformer parameter=impedance operator=>= value=5.5 unit=percent condition=null]

Submittal: Transformer impedance rated at 6.0%.
[FACT req_id=CTRL-4 equipment_class=transformer parameter=impedance value=6.0 unit=percent condition=null source_doc="Transformer test certificate" source_page=1 confidence=0.95]

### Clause CTRL-5 — CRAC Sensible Cooling Capacity
CRAC unit sensible cooling capacity shall be not less than 120 kW per unit.
[FACT req_id=CTRL-5 equipment_class=crac parameter=sensible_cooling_capacity operator=>= value=120 unit=kW condition=null]

Submittal: CRAC unit sensible cooling capacity rated at 125 kW.
[FACT req_id=CTRL-5 equipment_class=crac parameter=sensible_cooling_capacity value=125 unit=kW condition=null source_doc="CRAC unit submittal" source_page=1 confidence=0.95]
