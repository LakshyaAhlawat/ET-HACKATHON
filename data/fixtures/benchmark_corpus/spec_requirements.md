# Specification Requirements — Data Centre EPC Project

Synthesized specification excerpts. See `README.md` in this folder for
provenance. Every clause below states one testable requirement in prose,
tagged with a machine-parseable FACT annotation.

## Mechanical Specification, Division 23

### Clause MECH-3.4.2 — Chiller Cooling Capacity
Chiller cooling capacity shall be not less than 500 TR at 35°C ambient.
[FACT req_id=MECH-3.4.2 equipment_class=chiller parameter=cooling_capacity operator=>= value=500 unit=TR condition="@35C ambient"]

### Clause MECH-3.4.3 — Chiller IPLV
Chiller Integrated Part Load Value (IPLV) shall be not less than 6.2 EER.
[FACT req_id=MECH-3.4.3 equipment_class=chiller parameter=iplv operator=>= value=6.2 unit=dimensionless condition=null]

### Clause MECH-3.5.1 — Chiller Acoustic Limit
Chiller noise level shall not exceed 82 dB(A) at 1 meter under full-load conditions.
[FACT req_id=MECH-3.5.1 equipment_class=chiller parameter=noise_level operator=<= value=82 unit=dBA condition="@1m full load"]

### Clause MECH-3.5.2 — Chiller Bearing Vibration
Chiller bearing vibration shall not exceed 2.8 mm/s RMS.
[FACT req_id=MECH-3.5.2 equipment_class=chiller parameter=bearing_vibration operator=<= value=2.8 unit=mm/s condition=null]

### Clause MECH-3.6.1 — Cooling Loop Redundancy
Two independent chilled water loops are required for Tier III redundancy;
any one loop shall be capable of cooling the entire facility, with isolation
such that a header failure on one loop does not affect the other.
[FACT req_id=MECH-3.6.1 equipment_class=cooling_loop parameter=redundant_paths operator=>= value=2 unit=dimensionless condition=null]

### Clause MECH-3.7.1 — CPU Cooler Thermal Interface Material
Thermal interface material (TIM) thermal conductivity shall be not less than 3.5 W/m·K.
[FACT req_id=MECH-3.7.1 equipment_class=tim parameter=thermal_conductivity operator=>= value=3.5 unit=W/m/K condition=null]

## Electrical Specification, Division 16

### Clause DIV-16 §16.1.2 — Outdoor Enclosure Rating
All outdoor equipment enclosures shall be minimum NEMA 4X (IP66 equivalent).
[FACT req_id=DIV-16-16.1.2 equipment_class=ats parameter=enclosure_rating operator=>= value=66 unit=dimensionless condition=null]

### Clause ELEC-2.8.1 — UPS Runtime
UPS runtime shall be not less than 20 minutes at full load at 25°C ambient.
[FACT req_id=ELEC-2.8.1 equipment_class=ups parameter=runtime operator=>= value=20 unit=min condition="@25C ambient, @full load"]

### Clause ELEC-2.8.2 — UPS Power Capacity
UPS power capacity shall be not less than 250 kW at 0.9 power factor.
[FACT req_id=ELEC-2.8.2 equipment_class=ups parameter=power_capacity operator=>= value=250 unit=kW condition="@0.9 PF"]

### Clause ELEC-2.8.3 — UPS Module MTBF
UPS module Mean Time Between Failure (MTBF) shall be not less than 100,000 hours.
[FACT req_id=ELEC-2.8.3 equipment_class=ups parameter=mtbf operator=>= value=100000 unit=hr condition=null]

### Clause ELEC-3.1.1 — Generator Redundancy
Tier III power train requires N+1 generator redundancy: two independent
generators, each capable of carrying the full IT load, such that any one
generator can carry the load alone.
[FACT req_id=ELEC-3.1.1 equipment_class=generator parameter=redundant_units operator=>= value=2 unit=dimensionless condition=null]

### Clause ELEC-4.2.1 — Switchgear Coordination Study
The electrical design package shall include a breaker coordination study
demonstrating that each upstream breaker clears slower than its downstream
breaker (proper selectivity), submitted with the single-line diagram.
[FACT req_id=ELEC-4.2.1 equipment_class=switchgear parameter=coordination_study operator=== value=1 unit=dimensionless condition="included in submittal package, not deferred"]

### Clause ELEC-5.1.1 — Cable Fire Rating
All power cable in cable trays within 10 meters of IT equipment shall be
rated IEC 60332-1 Category A (non-propagating flame).
[FACT req_id=ELEC-5.1.1 equipment_class=cable parameter=fire_rating_category operator=== value=1 unit=dimensionless condition="within 10m of IT equipment"]

## Quality & Procurement

### Clause QUAL-2.3 — Submittal Documentation
All vendor submittals shall include a certificate of compliance, test
reports for the equipment, and warranty documentation, in addition to the
product cut sheet.
[FACT req_id=QUAL-2.3 equipment_class=any parameter=required_documents operator=== value=4 unit=dimensionless condition="cut sheet + certificate of compliance + test reports + warranty"]

### Clause PROC-1.1 — Equipment Delivery Lead Time
Equipment delivery shall occur within 16 weeks of order placement.
[FACT req_id=PROC-1.1 equipment_class=any parameter=delivery_lead_time operator=<= value=16 unit=weeks condition=null]
