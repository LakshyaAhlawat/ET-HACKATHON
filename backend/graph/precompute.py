"""Writes the full knowledge graph to data/graph.json so the frontend graph
screen can render it without hitting the API on every load -- same
precompute-everything discipline as cascade/ and sld/."""

import sys
from pathlib import Path

from graph.build import full_graph

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "graph.json"


def run() -> None:
    result = full_graph()
    OUTPUT_PATH.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(
        f"Wrote {len(result.nodes)} nodes, {len(result.edges)} edges to {OUTPUT_PATH}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    run()
