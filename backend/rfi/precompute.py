"""Writes the RFI contradiction analysis to data/rfi_analysis.json so the
API doesn't re-run LLM claim extraction on every request -- same
precompute-everything discipline as cascade/, sld/, and graph/.

Each candidate pair costs one LLM call; if GROQ_API_KEY's daily quota is
exhausted mid-run, detect_contradictions() skips the remaining pairs rather
than crashing (see rfi/dedup.py) -- rerun this script once quota resets to
pick up the rest.
"""

import sys
from pathlib import Path

from rfi.dedup import analyse

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "rfi_analysis.json"


def run(n_new_duplicates_this_period: int = 0) -> None:
    result = analyse(n_new_duplicates_this_period=n_new_duplicates_this_period)
    OUTPUT_PATH.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(
        f"Wrote {len(result.contradictions)} contradiction flag(s) over "
        f"{result.total_historical_rfis} historical RFIs to {OUTPUT_PATH}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    run()
