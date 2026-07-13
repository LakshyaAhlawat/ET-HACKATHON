# Multi-Discipline Reference Notes

Synthesized cross-discipline reference material supporting multi-hop
questions. See `README.md` for provenance.

## Tier III Power Train — Vendors and Lead Times

The Tier III power train's critical-path equipment and suppliers:
Schneider Electric supplies the ATS, lead time 14 weeks. Caterpillar
supplies the generator, lead time 16 weeks. Vertiv supplies the UPS, lead
time 12 weeks. These three procurements run in parallel, so the
critical-path lead time is the maximum of the three: 16 weeks
(Caterpillar generator).

## Cooling Loop — Chiller / Cooling Tower Interface

Trane chiller specifies a maximum water inlet temperature of 54°C. Marley
cooling tower specifies a minimum water exit temperature of 32°C at design
ambient of 35°C. A typical chiller approach temperature (inlet minus
outlet) is around 6°C, which leaves limited margin between Marley's 32°C
exit and Trane's inlet tolerance — a detailed cooling load and
balance-point calculation is required before combining the two vendors'
equipment in one loop.

## Building Code Safety Systems and UPS Backup

The local building code requires emergency power backup for all safety
systems. The facility's safety systems are emergency lighting, fire
suppression control, and HVAC safety interlocks. The UPS load inventory
for this project has not yet been cross-referenced against this full
safety-system list to confirm all three are covered.

## Transformer Expedite Cost vs. Monsoon Schedule Impact

Expediting the transformer delivery from 18 weeks to 14 weeks costs ₹45
lakh. If the transformer delay instead pushes commissioning into the
monsoon window, testing duration increases by approximately 4 weeks; each
week of extended schedule costs approximately ₹45 lakh in crew and
facility rental.

## Chiller Failure — Downstream Schedule Dependencies

The chiller is a single point of failure in the cooling loop. Tasks that
depend on chiller operation: cooling system test, integrated systems test
(IST), and commissioning. A chiller failure requiring replacement carries
a lead time of at least 4 weeks, which delays all three downstream tasks
by the same amount.

## Tier III Fast-Transfer Requirement

Per the project's Tier III SLA, upon ATS failure the facility must fail
over to the backup generator within 4 milliseconds. Achieving this
requires: dual independent ATS units in series, fast-transfer logic in the
facility PLC, a generator rated to accept load within 2–3 milliseconds,
and a static transfer switch (STS) bypass path.

## Chiller Warranty — Water Quality Requirement

The chiller warranty is void if water quality does not meet ISO 11162
(particle count, pH, corrosion inhibitor concentration). Responsibility
for verifying water treatment before commissioning: the mechanical
engineering team pre-commissioning, and the facility operations team on an
ongoing basis, coordinating with the chiller vendor and the water
treatment vendor. Verification is via water sampling and lab analysis.

## Spare Parts — Critical Path Inventory

Three pieces of equipment are on the critical path for spare parts during
operations: generator fuel filters (consumable, recommended 1-month stock
on-site), UPS battery cells (high lead time, recommended 1 full set
on-site), and the ATS control board (long lead time, recommended 1 spare
on-site).

## Thermal Design — Ambient Rise Impact

If data hall ambient rises 2°C above design (from 24°C to 26°C) while the
target IT equipment inlet temperature remains 27°C, the chilled water
supply temperature typically needs to be reduced by 2–3°C (for example,
from 12°C to 9°C) to compensate — which may approach or exceed the
chiller's rated capacity margin.

## Change Order — IT Capacity Increase Cascading Impact

A change order that increases IT equipment capacity by 15% requires
resizing the cooling loop (chiller, cooling tower, and pump capacity) by
roughly 15–20%, along with re-engineering the electrical load
calculations. If any resized component exceeds its vendor's original
lead-time-committed capacity band, re-procurement is required, typically
adding 6–8 weeks to the schedule.
