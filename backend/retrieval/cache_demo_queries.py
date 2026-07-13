"""Precomputes router classifications for the fixed set of questions the
90-second demo script asks, so the live demo's query-router step never
depends on Groq being reachable (see router.py's module docstring and
data/demo_query_cache.json). Run once whenever the demo script's questions
change: `python -m retrieval.cache_demo_queries`.
"""

import json
import sys

from retrieval.router import DEMO_CACHE_PATH, classify_query

# Keep this list in sync with the demo script (docs/DEMO_SCRIPT.md).
DEMO_QUERIES = [
    "Does the chiller in MECH-3.4.2 meet its cooling capacity requirement?",
    "If the transformer is delayed by 3 weeks, when will handover happen?",
    "Trace the dependency chain from the chiller spec to project handover.",
    "What HVAC setpoint does the spec require for the data hall?",
]


def run() -> None:
    entries = []
    for query in DEMO_QUERIES:
        decision = classify_query(query)
        entries.append({"query": query, "category": decision.category})
        print(f"  {decision.category:16s} <- {query}", file=sys.stderr)

    DEMO_CACHE_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"Wrote {len(entries)} cached classifications to {DEMO_CACHE_PATH}", file=sys.stderr)


if __name__ == "__main__":
    run()
