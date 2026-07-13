"""Generate the demo spec.pdf / submittal.pdf fixtures used by the compliance viewer.

Text is drawn so it sits inside the exact source_bbox coordinates recorded in
data/fixtures/verdict_sample.json — the overlay boxes the frontend draws must
line up with real text, not just an empty page. Re-run this after editing that
JSON's bbox values.

Usage: pip install -r scripts/requirements.txt && python scripts/generate_fixture_pdfs.py
"""

import json
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_JSON = ROOT / "data" / "fixtures" / "verdict_sample.json"
OUTPUT_DIRS = [ROOT / "data" / "fixtures", ROOT / "frontend" / "public" / "fixtures"]


def draw_spec_pdf(path: Path, bbox: tuple[float, float, float, float]) -> None:
    x0, y0, x1, y1 = bbox
    c = canvas.Canvas(str(path), pagesize=LETTER)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 750, "MECHANICAL SPECIFICATION — SECTION 3.4")
    c.setFont("Helvetica", 10)
    c.drawString(72, 735, "Data Centre Chilled Water Plant")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y1 - 15, "3.4.2  Chiller Cooling Capacity")
    c.setFont("Helvetica", 10)
    # "35C ambient" (not "...ambient dry-bulb") deliberately matches the
    # submittal's condition wording below verbatim -- evaluate_requirement()
    # matches condition text after normalization but does not do fuzzy/
    # synonym matching, so two independently-worded phrasings of the same
    # physical condition would otherwise produce INSUFFICIENT_DATA instead
    # of the intended NON_CONFORMANCE. Real spec/submittal pairs really do
    # drift like this; this fixture is written to demo the deviation, not
    # the wording-mismatch case.
    c.drawString(
        x0,
        y0 + 8,
        "Each chiller shall provide not less than 500 TR at 35C ambient.",
    )

    c.setFont("Helvetica", 8)
    c.drawString(72, 40, "spec.pdf — page 1")
    c.showPage()
    c.save()


def draw_submittal_pdf(path: Path, bbox: tuple[float, float, float, float]) -> None:
    x0, y0, x1, y1 = bbox
    c = canvas.Canvas(str(path), pagesize=LETTER)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 750, "VENDOR SUBMITTAL — CHILLER MODEL XYZ-500")
    c.setFont("Helvetica", 10)
    c.drawString(72, 735, "Cut Sheet: Centrifugal Water-Cooled Chiller")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y1 - 15, "Cooling Capacity")
    c.setFont("Helvetica", 10)
    c.drawString(x0, y0 + 8, "480 TR @ 35C Ambient")

    c.setFont("Helvetica", 8)
    c.drawString(72, 40, "submittal.pdf — page 1")
    c.showPage()
    c.save()


def main() -> None:
    fixture = json.loads(FIXTURE_JSON.read_text())
    spec_bbox = tuple(fixture["spec_evidence"]["source_bbox"])
    submittal_bbox = tuple(fixture["submittal_evidence"]["source_bbox"])

    for out_dir in OUTPUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        draw_spec_pdf(out_dir / "spec.pdf", spec_bbox)
        draw_submittal_pdf(out_dir / "submittal.pdf", submittal_bbox)
        print(f"Wrote spec.pdf and submittal.pdf to {out_dir}")


if __name__ == "__main__":
    main()
