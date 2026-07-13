# RFI Log — Data Centre EPC Project

Synthesized RFI (Request for Information) log. See `README.md` for
provenance. Each entry is a question/response pair as logged during design
review. Two RFIs (RFI-0201-A on transformer oil and RFI-0201-B on UPS
battery replacement) were logged in the same week and share a number
prefix in this synthesized log — a real-world RFI numbering collision,
preserved here exactly as it appears in the ground-truth key rather than
silently fixed.

## RFI-0124 (2024-03-15) — Chilled Water Supply Temperature
Question: What is the required chilled water supply temperature setpoint
for the cooling loop?
Response: 12°C ± 1°C.

## RFI-0287 (2024-09-22) — Chiller Sizing vs. Supply Temperature
Question: Chiller is sized for 13°C supply temperature — can we operate at
13°C instead of 12°C?
Response: Chiller sizing assumes 13°C; IT equipment inlet limits have not
been re-confirmed against this value.

## RFI-0089 (2024-01-12) — Generator Biodiesel Fuel
Question: Can the backup generator run on biodiesel fuel?
Response: Yes, ISO 8675 biodiesel approved.

## RFI-0156 (2024-05-08) — Biodiesel Warranty Impact
Question: Does biodiesel fuel affect the generator warranty?
Response: Biodiesel use voids manufacturer warranty unless biodiesel is
specified in the original equipment submittal.

## RFI-0201-A (2024-04-30) — Transformer Oil Type
Question: Is eco-friendly (vegetable-based) transformer oil acceptable?
Response: Yes, vegetable oil acceptable per IEEE C57.147.

## RFI-0245 (2024-07-11) — Transformer Oil Temperature Rating
Question: Does eco-friendly oil reduce transformer life?
Response: Yes — vegetable oil has a lower temperature rating (65°C rise vs.
55°C for mineral oil), requiring derating.

## RFI-0076 (2024-02-14) — HVAC Setpoint
Question: What HVAC temperature setpoint is required for data hall
ambient?
Response: 24°C ± 2°C (allowable range 22–26°C).

## RFI-0167-A (2024-06-20) — HVAC Setpoint Relaxation
Question: Can we loosen the setpoint to 26–28°C to save energy?
Response: Energy savings possible, but IT equipment inlet temperatures may
exceed 30°C, risking thermal shutdown. Recommendation: maintain 24°C ± 2°C
per specification.

## RFI-0098 (2024-03-05) — UPS Battery Chemistry
Question: What UPS battery chemistry is approved?
Response: Valve-regulated lead-acid (VRLA) or lithium-ion, vendor's choice.

## RFI-0178 (2024-07-01) — Lithium-Ion Battery Replacement Interval
Question: Lithium-ion UPS battery — how often must it be replaced?
Response: 10-year design life; replacement every 10 years.

## RFI-0201-B (2024-08-15) — VRLA Battery Replacement Interval
Question: VRLA batteries — what is the replacement interval?
Response: 5-year design life; replacement every 5 years.

## RFI-0132 (2024-04-10) — CRAC Control Strategy
Question: What control strategy is used for CRAC units?
Response: Temperature-based on-off control; CRAC shuts down below 20°C
supply air, energises above 24°C.

## RFI-0219 (2024-08-30) — CRAC Variable-Capacity Mode
Question: Can CRAC units run in variable-capacity mode for efficiency?
Response: Yes, modulating valve control available at an additional cost of
₹8 lakh per unit.

## RFI-0145 (2024-05-22) — Monitoring Dashboard Scope
Question: What systems require real-time monitoring dashboards?
Response: Power (UPS, generator, ATS status), cooling (chiller, CRAC
temperatures), and IT environmental sensors.

## RFI-0236 (2024-09-01) — Fire and Security Monitoring Scope
Question: Do fire suppression and security systems also need monitoring
dashboards?
Response: Fire suppression monitoring is required per fire code; security
is a separate system, not included in the environmental dashboard.

## RFI-0167-B (2024-06-18) — IST Responsibility
Question: Who is responsible for conducting the Integrated Systems Test
(IST)?
Response: EPC contractor plus equipment manufacturer representatives.

## RFI-0251 (2024-09-10) — Facility Team Participation in IST
Question: Can the facility operations team participate in IST, or does it
compromise independent verification?
Response: Facility team observes but does not conduct the test. An
independent third-party agency can be hired for additional verification.

## RFI-0189 (2024-07-15) — Test Record Retention
Question: How long must IST test records and logs be retained?
Response: Per TIA-942 Tier III: minimum 10 years for major systems, 5 years
for auxiliary systems.

## RFI-0267 (2024-09-25) — Digital vs. Paper Test Records
Question: Can test records be stored digitally, or must paper copies be
retained?
Response: Digital records are acceptable if certified and access-controlled;
paper copies are recommended for critical tests.

## RFI-0213 (2024-08-02) — Change Approval Authority
Question: Who can approve design changes after equipment is ordered?
Response: Change Control Board (CCB), comprising client, EPC, and major
equipment vendors.

## RFI-0284 (2024-10-05) — Minor Change Threshold
Question: If a change is minor (e.g., +5% load increase), does it require
full CCB approval?
Response: Yes — any change with ≥1% cost or schedule impact requires CCB
approval; "minor" is not separately defined.
