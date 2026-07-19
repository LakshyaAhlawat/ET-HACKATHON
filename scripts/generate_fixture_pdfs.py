"""Generate the demo spec/submittal PDF fixtures used by the compliance viewer.

Five document pairs, covering all 15 planted deviations from
data/benchmark/ground_truth_50.json (grouped by discipline: chiller,
electrical enclosures/switchgear, UPS/power, Tier III redundancy, and
procurement/misc).

Bounding boxes are computed from the actual drawn text position using
standard Helvetica font metrics (ascent 0.718em, descent 0.207em) plus
reportlab's stringWidth() -- not hand-guessed. This reproduces the same
methodology that produced the original DEV_001 bbox in
data/extracted/spec.requirements.json (verified: 695.93/705.18 against a
698pt baseline is exactly baseline-2.07/baseline+7.18, i.e. descent/ascent
at 10pt). No GROQ_API_KEY is configured in this environment, so the real
`ingestion.ingest` pipeline (docling + LLM extraction, see
backend/ingestion/) cannot be run against these PDFs -- this script emits
data/extracted/{spec.requirements,submittal.values}.json directly instead,
standing in for that step for demo purposes.

Only deviations that are genuine scalar comparisons (equipment_class +
parameter + operator + numeric value + unit, matching
backend/app/models/schema.py's Requirement/ExtractedValue) are wired into
the extracted JSON that drives the live deterministic evaluator
(backend/app/services/compliance/evaluator.py). Categorical/structural
deviations (enclosure rating class, redundancy topology, document
checklist completeness, cable fire category) still get real PDF pages with
real text, but are NOT force-fit into fake numeric Requirements -- the
evaluator only compares scalar thresholds, and encoding e.g. "NEMA 4X vs
NEMA 4" as a fake numeric delta would be exactly the kind of guessing
CLAUDE.md's compliance-verifier rules prohibit. Extending the evaluator to
support categorical/enum requirements is a real feature, not something to
fake here.

Usage: pip install -r scripts/requirements.txt && python scripts/generate_fixture_pdfs.py
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRS = [ROOT / "data" / "fixtures", ROOT / "frontend" / "public" / "fixtures"]
EXTRACTED_DIR = ROOT / "data" / "extracted"

FONT_TITLE = "Helvetica-Bold"
FONT_BODY = "Helvetica"
SIZE_TITLE = 11
SIZE_BODY = 10
# Standard Helvetica core-14 metrics, expressed as a fraction of font size.
ASCENT = 0.718
DESCENT = 0.207

PAGE_TOP_TITLE_Y = 750
PAGE_SUBTITLE_Y = 735
FIRST_CLAUSE_Y = 700
CLAUSE_SPACING = 55
FOOTER_Y = 40
LEFT_MARGIN = 72.0


@dataclass
class Wiring:
    """Structured data feeding the live deterministic evaluator. Present
    only for deviations that are genuine scalar comparisons."""

    req_id: str
    equipment_class: str
    parameter: str
    operator: str
    value: float
    unit: str
    condition: str | None
    submitted_value: float
    submitted_unit: str
    submitted_condition: str | None
    extraction_confidence: float


@dataclass
class Clause:
    deviation_id: str
    spec_label: str
    spec_text: str
    submittal_label: str
    submittal_text: str
    wiring: Wiring | None = None
    # Populated after drawing; consumed when writing extracted JSON.
    spec_bbox: tuple[float, float, float, float] | None = field(default=None, init=False)
    submittal_bbox: tuple[float, float, float, float] | None = field(default=None, init=False)


@dataclass
class DocPair:
    key: str
    spec_filename: str
    submittal_filename: str
    spec_title: str
    spec_subtitle: str
    submittal_title: str
    submittal_subtitle: str
    clauses: list[Clause]


DOC_PAIRS: list[DocPair] = [
    DocPair(
        key="chiller",
        spec_filename="spec.pdf",
        submittal_filename="submittal.pdf",
        spec_title="MECHANICAL SPECIFICATION — SECTION 3.4",
        spec_subtitle="Data Centre Chilled Water Plant",
        submittal_title="VENDOR SUBMITTAL — CHILLER MODEL XYZ-500 / TRANE SINTESIS",
        submittal_subtitle="Cut Sheet: Centrifugal Water-Cooled Chillers",
        clauses=[
            # Unchanged from the original single-fixture version: same text,
            # same position, so its bbox lands exactly where
            # data/extracted/*.json already has it recorded.
            Clause(
                deviation_id="DEV_001",
                spec_label="3.4.2  Chiller Cooling Capacity",
                spec_text="Each chiller shall provide not less than 500 TR at 35C ambient.",
                submittal_label="Cooling Capacity",
                submittal_text="480 TR @ 35C Ambient",
                wiring=Wiring(
                    req_id="MECH-3.4.2",
                    equipment_class="chiller",
                    parameter="cooling_capacity",
                    operator=">=",
                    value=500.0,
                    unit="TR",
                    condition="@35C ambient",
                    submitted_value=480.0,
                    submitted_unit="TR",
                    submitted_condition="@ 35C Ambient",
                    extraction_confidence=0.95,
                ),
            ),
            Clause(
                deviation_id="DEV_005",
                spec_label="3.4.3  Chiller Integrated Part Load Value (IPLV)",
                spec_text="Each chiller shall achieve a minimum IPLV of 6.2 EER.",
                submittal_label="Integrated Part Load Value (IPLV)",
                submittal_text="6.0 EER",
                wiring=Wiring(
                    req_id="MECH-3.4.3",
                    equipment_class="chiller",
                    parameter="iplv",
                    operator=">=",
                    value=6.2,
                    unit="",
                    condition=None,
                    submitted_value=6.0,
                    submitted_unit="",
                    submitted_condition=None,
                    extraction_confidence=0.94,
                ),
            ),
            Clause(
                deviation_id="DEV_010",
                spec_label="3.4.4  Chiller Sound Power Level",
                spec_text="Chiller noise shall not exceed 82 dBA at 1 meter, full load.",
                submittal_label="Sound Power Level",
                submittal_text="84 dBA",
                wiring=Wiring(
                    req_id="MECH-3.4.4",
                    equipment_class="chiller",
                    parameter="noise_level",
                    operator="<=",
                    value=82.0,
                    unit="dBA",
                    condition="@1m full load",
                    submitted_value=84.0,
                    submitted_unit="dBA",
                    submitted_condition="@1m full load",
                    extraction_confidence=0.93,
                ),
            ),
            Clause(
                deviation_id="DEV_011",
                spec_label="3.4.5  Chiller Bearing Vibration",
                spec_text="Chiller bearing vibration shall not exceed 2.8 mm/s RMS.",
                submittal_label="Bearing Vibration (CMS Baseline)",
                submittal_text="3.1 mm/s",
                wiring=Wiring(
                    req_id="MECH-3.4.5",
                    equipment_class="chiller",
                    parameter="bearing_vibration",
                    operator="<=",
                    value=2.8,
                    unit="mm/s",
                    condition=None,
                    submitted_value=3.1,
                    submitted_unit="mm/s",
                    submitted_condition=None,
                    extraction_confidence=0.90,
                ),
            ),
        ],
    ),
    DocPair(
        key="electrical",
        spec_filename="spec_electrical.pdf",
        submittal_filename="submittal_electrical.pdf",
        spec_title="ELECTRICAL SPECIFICATION — DIVISION 16",
        spec_subtitle="Enclosures, Switchgear, Cable",
        submittal_title="VENDOR SUBMITTAL — SCHNEIDER ELECTRIC ATS PACKAGE",
        submittal_subtitle="Automatic Transfer Switch / Switchgear Cut Sheet",
        clauses=[
            # Not wired: categorical (NEMA/IP class), not a scalar comparison.
            Clause(
                deviation_id="DEV_002",
                spec_label="16.1.2  Outdoor Enclosure Rating",
                spec_text=(
                    "All outdoor equipment enclosures shall be minimum NEMA 4X "
                    "(IP66 equivalent)."
                ),
                submittal_label="Enclosure Rating",
                submittal_text="NEMA 4 (IP65)",
            ),
            # Not wired: presence/absence of a document, not a scalar value.
            Clause(
                deviation_id="DEV_006",
                spec_label="16.4.2.1  Breaker Coordination Study",
                spec_text=(
                    "Submittal package shall include a coordination study demonstrating "
                    "breaker selectivity."
                ),
                submittal_label="Coordination Study",
                submittal_text="Available upon request — not included in this package",
            ),
            # Not wired: cable category is an ordinal class, not a scalar value.
            Clause(
                deviation_id="DEV_013",
                spec_label="16.9.1  Fire Safety — Cable Rating",
                spec_text=(
                    "Power cable in trays within 10 m of IT equipment shall be rated "
                    "IEC 60332-1 Category A."
                ),
                submittal_label="Cable Fire Rating",
                submittal_text="IEC 60332-1 Category B",
            ),
        ],
    ),
    DocPair(
        key="power",
        spec_filename="spec_power.pdf",
        submittal_filename="submittal_power.pdf",
        spec_title="ELECTRICAL SPECIFICATION — SECTION 2.8",
        spec_subtitle="Uninterruptible Power Supply (UPS)",
        submittal_title="VENDOR SUBMITTAL — VERTIV UPS MODULE",
        submittal_subtitle="Cut Sheet: Modular UPS System",
        clauses=[
            Clause(
                deviation_id="DEV_003",
                spec_label="2.8.1  UPS Runtime",
                spec_text=(
                    "UPS shall provide not less than 20 minutes runtime at full load, "
                    "25C ambient."
                ),
                submittal_label="Runtime",
                submittal_text="20 minutes",
                wiring=Wiring(
                    req_id="ELEC-2.8.1",
                    equipment_class="ups",
                    parameter="runtime",
                    operator=">=",
                    value=20.0,
                    unit="min",
                    condition="@25C ambient, @full load",
                    submitted_value=20.0,
                    submitted_unit="min",
                    submitted_condition=None,
                    extraction_confidence=0.88,
                ),
            ),
            Clause(
                deviation_id="DEV_007",
                spec_label="2.8.2  UPS Power Capacity",
                spec_text="UPS shall provide not less than 250 kW at the specified load.",
                submittal_label="Power Rating",
                submittal_text="250 kVA (power factor not stated)",
                wiring=Wiring(
                    req_id="ELEC-2.8.2",
                    equipment_class="ups",
                    parameter="power_capacity",
                    operator=">=",
                    value=250.0,
                    unit="kW",
                    condition=None,
                    submitted_value=250.0,
                    submitted_unit="kVA",
                    submitted_condition=None,
                    extraction_confidence=0.85,
                ),
            ),
            Clause(
                deviation_id="DEV_014",
                spec_label="2.8.3  UPS Mean Time Between Failure",
                spec_text="UPS modules shall have MTBF of not less than 100,000 hours.",
                submittal_label="MTBF",
                submittal_text="95,000 hours",
                wiring=Wiring(
                    req_id="ELEC-2.8.3",
                    equipment_class="ups",
                    parameter="mtbf",
                    operator=">=",
                    value=100000.0,
                    unit="hour",
                    condition=None,
                    submitted_value=95000.0,
                    submitted_unit="hour",
                    submitted_condition=None,
                    extraction_confidence=0.97,
                ),
            ),
        ],
    ),
    DocPair(
        key="redundancy",
        spec_filename="spec_redundancy.pdf",
        submittal_filename="submittal_redundancy.pdf",
        spec_title="TIER III REDUNDANCY SPECIFICATION",
        spec_subtitle="Power Train and Cooling Topology (per TIA-942)",
        submittal_title="PROJECT SUBMITTAL — REDUNDANCY & DOCUMENTATION PACKAGE",
        submittal_subtitle="Generator Schedule, Piping Plan, Vendor Documents",
        clauses=[
            # Not wired: redundancy count/topology, not a single scalar reading.
            Clause(
                deviation_id="DEV_004",
                spec_label="Tier III Power Train — Generator Redundancy",
                spec_text=(
                    "Facility shall provide N+1 generator redundancy: two independent "
                    "2500 kVA generators, either capable of carrying full IT load."
                ),
                submittal_label="Generator Configuration (Project Schedule)",
                submittal_text="One (1) 2500 kVA diesel generator",
            ),
            Clause(
                deviation_id="DEV_008",
                spec_label="Tier III Cooling — Chilled Water Loop Redundancy",
                spec_text=(
                    "Two independent chilled water loops shall be provided; either loop "
                    "shall independently cool the full facility load."
                ),
                submittal_label="Chilled Water Piping Plan",
                submittal_text="Dual loops from single chiller-plant header, no isolation valves",
            ),
            # Not wired: document checklist, not a scalar value.
            Clause(
                deviation_id="DEV_009",
                spec_label="QUAL-2.3  Submittal Documentation",
                spec_text=(
                    "All vendor submittals shall include certificate of compliance, "
                    "equipment test reports, and warranty documentation."
                ),
                submittal_label="Documents Provided",
                submittal_text=(
                    "Product cut sheet, warranty (certificate of compliance and test "
                    "reports not included)"
                ),
            ),
        ],
    ),
    DocPair(
        key="procurement",
        spec_filename="spec_procurement.pdf",
        submittal_filename="submittal_procurement.pdf",
        spec_title="FACILITIES & PROCUREMENT SPECIFICATION",
        spec_subtitle="IT Hardware Thermal Design, Delivery Terms",
        submittal_title="VENDOR SUBMITTAL — PROCUREMENT PACKAGE",
        submittal_subtitle="Kirloskar / Misc. Equipment Quote",
        clauses=[
            Clause(
                deviation_id="DEV_012",
                spec_label="7.1.1  CPU Thermal Interface Material",
                spec_text=(
                    "CPU thermal interface material (TIM) shall have thermal "
                    "conductivity of not less than 3.5 W/(m*K)."
                ),
                submittal_label="Thermal Interface Material",
                submittal_text="3.2 W/(m*K)",
                wiring=Wiring(
                    req_id="IT-7.1.1",
                    equipment_class="cpu_cooler",
                    parameter="tim_thermal_conductivity",
                    operator=">=",
                    value=3.5,
                    unit="W/(m*K)",
                    condition=None,
                    submitted_value=3.2,
                    submitted_unit="W/(m*K)",
                    submitted_condition=None,
                    extraction_confidence=0.91,
                ),
            ),
            Clause(
                deviation_id="DEV_015",
                spec_label="1.1  Equipment Delivery Lead Time",
                spec_text="Equipment shall be delivered within 16 weeks of order placement.",
                submittal_label="Delivery Lead Time (Vendor Quote)",
                submittal_text="18 weeks standard (15% premium for 15-week expedite)",
                wiring=Wiring(
                    req_id="PROC-1.1",
                    equipment_class="procurement",
                    parameter="lead_time",
                    operator="<=",
                    value=16.0,
                    unit="week",
                    condition=None,
                    submitted_value=18.0,
                    submitted_unit="week",
                    submitted_condition=None,
                    extraction_confidence=0.92,
                ),
            ),
        ],
    ),
]


def _text_bbox(c: Canvas, text: str, x: float, baseline_y: float, font: str, size: float) -> tuple[float, float, float, float]:
    width = c.stringWidth(text, font, size)
    return (x, baseline_y - DESCENT * size, x + width, baseline_y + ASCENT * size)


def _draw_doc(
    c: Canvas,
    title: str,
    subtitle: str,
    footer: str,
    clauses: list[Clause],
    *,
    is_spec: bool,
) -> None:
    c.setFont(FONT_TITLE, 14)
    c.drawString(LEFT_MARGIN, PAGE_TOP_TITLE_Y, title)
    c.setFont(FONT_BODY, 10)
    c.drawString(LEFT_MARGIN, PAGE_SUBTITLE_Y, subtitle)

    y = FIRST_CLAUSE_Y
    for clause in clauses:
        label = clause.spec_label if is_spec else clause.submittal_label
        text = clause.spec_text if is_spec else clause.submittal_text

        c.setFont(FONT_TITLE, SIZE_TITLE)
        c.drawString(LEFT_MARGIN, y, label)

        value_baseline = y - 15
        c.setFont(FONT_BODY, SIZE_BODY)
        c.drawString(LEFT_MARGIN, value_baseline, text)
        bbox = _text_bbox(c, text, LEFT_MARGIN, value_baseline, FONT_BODY, SIZE_BODY)
        if is_spec:
            clause.spec_bbox = bbox
        else:
            clause.submittal_bbox = bbox

        y -= CLAUSE_SPACING

    c.setFont("Helvetica", 8)
    c.drawString(LEFT_MARGIN, FOOTER_Y, footer)
    c.showPage()
    c.save()


def generate_pdfs(doc_pairs: list[DocPair]) -> None:
    for out_dir in OUTPUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        for pair in doc_pairs:
            spec_path = out_dir / pair.spec_filename
            c = canvas.Canvas(str(spec_path), pagesize=LETTER)
            _draw_doc(
                c,
                pair.spec_title,
                pair.spec_subtitle,
                f"{pair.spec_filename} — page 1",
                pair.clauses,
                is_spec=True,
            )

            submittal_path = out_dir / pair.submittal_filename
            c = canvas.Canvas(str(submittal_path), pagesize=LETTER)
            _draw_doc(
                c,
                pair.submittal_title,
                pair.submittal_subtitle,
                f"{pair.submittal_filename} — page 1",
                pair.clauses,
                is_spec=False,
            )
            print(f"Wrote {pair.spec_filename} and {pair.submittal_filename} to {out_dir}")


def write_extracted_json(doc_pairs: list[DocPair]) -> None:
    requirements = []
    values = []
    for pair in doc_pairs:
        for clause in pair.clauses:
            if clause.wiring is None:
                continue
            w = clause.wiring
            assert clause.spec_bbox is not None
            assert clause.submittal_bbox is not None
            requirements.append(
                {
                    "req_id": w.req_id,
                    "equipment_class": w.equipment_class,
                    "parameter": w.parameter,
                    "operator": w.operator,
                    "value": w.value,
                    "unit": w.unit,
                    "condition": w.condition,
                    "source_doc": pair.spec_filename,
                    "source_page": 1,
                    "source_bbox": list(clause.spec_bbox),
                }
            )
            values.append(
                {
                    "equipment_class": w.equipment_class,
                    "parameter": w.parameter,
                    "value": w.submitted_value,
                    "unit": w.submitted_unit,
                    "condition": w.submitted_condition,
                    "source_doc": pair.submittal_filename,
                    "source_page": 1,
                    "source_bbox": list(clause.submittal_bbox),
                    "extraction_confidence": w.extraction_confidence,
                }
            )

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXTRACTED_DIR / "spec.requirements.json").write_text(json.dumps(requirements, indent=2) + "\n")
    (EXTRACTED_DIR / "submittal.values.json").write_text(json.dumps(values, indent=2) + "\n")
    print(
        f"Wrote {len(requirements)} requirements / {len(values)} values to {EXTRACTED_DIR} "
        f"({len(requirements)} of 15 deviations are scalar-wired; the rest are categorical/"
        "structural and only exist as PDF text -- see module docstring)"
    )


def main() -> None:
    generate_pdfs(DOC_PAIRS)
    write_extracted_json(DOC_PAIRS)


if __name__ == "__main__":
    main()
