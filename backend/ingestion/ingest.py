"""Offline batch pipeline: spec/submittal PDFs -> data/extracted/*.json.

Not a live API route — run this ahead of time and ship the JSON, per
CLAUDE.md's "precompute everything" rule.

Usage:
    python -m ingestion.ingest --spec path/to/spec.pdf --submittal path/to/submittal.pdf
"""

import argparse
import json
from pathlib import Path

from ingestion.extract import extract_requirements, extract_values
from ingestion.parse import parse_spec_pdf, parse_submittal_pdf

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "extracted"


def ingest_spec(path: Path, output_dir: Path) -> Path:
    chunks = parse_spec_pdf(path)
    requirements = extract_requirements(chunks)
    out_path = output_dir / f"{path.stem}.requirements.json"
    out_path.write_text(json.dumps([r.model_dump() for r in requirements], indent=2))
    return out_path


def ingest_submittal(path: Path, output_dir: Path) -> Path:
    chunks = parse_submittal_pdf(path)
    values = extract_values(chunks)
    out_path = output_dir / f"{path.stem}.values.json"
    out_path.write_text(json.dumps([v.model_dump() for v in values], indent=2))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec", type=Path, action="append", default=[], help="Spec PDF (repeatable)"
    )
    parser.add_argument(
        "--submittal", type=Path, action="append", default=[], help="Submittal PDF (repeatable)"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for spec_path in args.spec:
        print(f"Wrote {ingest_spec(spec_path, args.output_dir)}")

    for submittal_path in args.submittal:
        print(f"Wrote {ingest_submittal(submittal_path, args.output_dir)}")


if __name__ == "__main__":
    main()
