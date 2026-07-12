"""Offline batch script: runs detect -> ocr -> connect -> redundancy on all
5 evaluation SLDs and ships the results as JSON, per CLAUDE.md's "precompute
everything" rule. Also renders each topology's image into frontend/public/
so the frontend can draw the YOLO boxes over the actual raw diagram.

Usage: python -m sld.precompute
"""

import json
from pathlib import Path
from typing import Any

from app.models.sld import RedundancyResult, SLDNode
from sld.connect import build_connectivity_graph
from sld.detect import detect_symbols
from sld.ocr import associate_tags
from sld.redundancy import analyse_redundancy
from sld.topology import all_topologies, render_topology

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = ROOT / "frontend" / "public" / "sld"
RESULTS_PATH = ROOT / "data" / "sld_results.json"

CONF_THRESHOLD = 0.4


def process_topology(image_path: Path, topology_id: str) -> dict[str, Any]:
    nodes: list[SLDNode] = detect_symbols(image_path, conf_threshold=CONF_THRESHOLD)
    nodes = associate_tags(image_path, nodes)
    edges = build_connectivity_graph(image_path, nodes)
    redundancy: RedundancyResult = analyse_redundancy(
        nodes, edges, claimed_redundancy="2N", source_doc=topology_id
    )
    return {
        "topology_id": topology_id,
        "image_path": f"/sld/{topology_id}.png",
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
        "redundancy": redundancy.model_dump(),
    }


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for topology in all_topologies():
        image = render_topology(topology)
        image_path = IMAGE_DIR / f"{topology.topology_id}.png"
        image.save(image_path)

        result = process_topology(image_path, topology.topology_id)
        result["name"] = topology.name
        results.append(result)
        print(
            f"{topology.topology_id}: {len(result['nodes'])} nodes, "
            f"{len(result['edges'])} edges, holds={result['redundancy']['holds']}"
        )

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {len(results)} topology results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
