# Vendor Submittals — Data Centre EPC Project

Synthesized vendor cut-sheet excerpts. See `README.md` for provenance.

## Vertiv CentraVac Chiller — Product Cut Sheet

Page 3 — Performance Data.
Cooling capacity: 1688 kW.
[FACT req_id=MECH-3.4.2 equipment_class=chiller parameter=cooling_capacity value=1688 unit=kW condition="@35C ambient" source_doc="Vertiv CentraVac cut sheet" source_page=3 confidence=0.95]

Page 6 — Acoustic Data.
Sound pressure level: 84 dB(A) at 1 meter, full load.
[FACT req_id=MECH-3.5.1 equipment_class=chiller parameter=noise_level value=84 unit=dBA condition="@1m full load" source_doc="Vertiv CentraVac cut sheet" source_page=6 confidence=0.93]

## Trane Sintesis Chiller — Product Cut Sheet

Page 12 — Efficiency Data.
IPLV: 6.0 EER.
[FACT req_id=MECH-3.4.3 equipment_class=chiller parameter=iplv value=6.0 unit=dimensionless condition=null source_doc="Trane Sintesis cut sheet" source_page=12 confidence=0.92]

Page 4 — Cooling Loop Interface.
Water inlet temperature maximum: 54°C.
[FACT req_id=MECH-INFO-1 equipment_class=chiller parameter=water_inlet_temp_max value=54 unit=C condition=null source_doc="Trane Sintesis cut sheet" source_page=4 confidence=0.9]

## Condition Monitoring System — Chiller Bearing Baseline

Baseline vibration reading, drive-end bearing.
Vibration: 3.1 mm/s RMS.
[FACT req_id=MECH-3.5.2 equipment_class=chiller parameter=bearing_vibration value=3.1 unit=mm/s condition=null source_doc="CMS baseline report" source_page=1 confidence=0.97]

## Schneider Electric ATS — Product Submittal

Enclosure rating: NEMA 4 (IP65).
[FACT req_id=DIV-16-16.1.2 equipment_class=ats parameter=enclosure_rating value=65 unit=dimensionless condition=null source_doc="Schneider ATS submittal" source_page=2 confidence=0.9]

## Vertiv UPS — Product Submittal

Runtime: 20 minutes. (Ambient temperature and load condition not stated in this submittal.)
[FACT req_id=ELEC-2.8.1 equipment_class=ups parameter=runtime value=20 unit=min condition=null source_doc="Vertiv UPS submittal" source_page=5 confidence=0.88]

Power rating: 250 kVA. (Power factor not stated in this submittal.)
[FACT req_id=ELEC-2.8.2 equipment_class=ups parameter=power_capacity value=250 unit=kVA condition=null source_doc="Vertiv UPS submittal" source_page=5 confidence=0.85]

MTBF: 95,000 hours.
[FACT req_id=ELEC-2.8.3 equipment_class=ups parameter=mtbf value=95000 unit=hr condition=null source_doc="Vertiv UPS submittal" source_page=7 confidence=0.94]

## Generator Package — Project Schedule Submittal

One 2500 kVA generator scheduled; no standby unit listed.
[FACT req_id=ELEC-3.1.1 equipment_class=generator parameter=redundant_units value=1 unit=dimensionless condition=null source_doc="Generator package submittal" source_page=1 confidence=0.96]

## Switchgear Package — Electrical Design Submittal

Single-line diagram submitted. Coordination study: "available upon request,
not included in this package." Breaker CB-05 rated 125A 3-phase; breaker
CB-02 rated 300A, upstream of CB-05.
[FACT req_id=ELEC-4.2.1 equipment_class=switchgear parameter=coordination_study value=0 unit=dimensionless condition="deferred, not included" source_doc="Switchgear package submittal" source_page=1 confidence=0.9]

## Piping Plan — Cooling Loop Submittal

Two chilled water loops shown, both drawing from a single chiller plant
header; no isolation valves shown between the loops.
[FACT req_id=MECH-3.6.1 equipment_class=cooling_loop parameter=redundant_paths value=1 unit=dimensionless condition=null source_doc="Piping plan submittal" source_page=1 confidence=0.88]

## CPU Cooler — Thermal Interface Material Submittal

TIM thermal conductivity: 3.2 W/m·K.
[FACT req_id=MECH-3.7.1 equipment_class=tim parameter=thermal_conductivity value=3.2 unit=W/m/K condition=null source_doc="TIM datasheet" source_page=1 confidence=0.9]

## Cable Submittal — Fire Rating

Power cable submitted for cable-tray runs within 10 meters of IT equipment:
IEC 60332-1 Category B.
[FACT req_id=ELEC-5.1.1 equipment_class=cable parameter=fire_rating_category value=2 unit=dimensionless condition="within 10m of IT equipment" source_doc="Cable submittal" source_page=1 confidence=0.91]

## Chiller Vendor — Documentation Package

Documents provided: product cut sheet, warranty. Certificate of compliance
and test reports were not included in this submission.
[FACT req_id=QUAL-2.3 equipment_class=chiller parameter=required_documents value=2 unit=dimensionless condition="cut sheet + warranty only, missing certificate + test reports" source_doc="Chiller documentation package" source_page=1 confidence=0.93]

## Equipment Procurement Quote

Standard lead time: 18 weeks. Expedite available at 15% premium for a
15-week delivery.
[FACT req_id=PROC-1.1 equipment_class=any parameter=delivery_lead_time value=18 unit=weeks condition="standard; 15% premium for 15wk expedite" source_doc="Procurement quote" source_page=1 confidence=0.92]
