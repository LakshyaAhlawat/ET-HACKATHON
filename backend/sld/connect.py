"""Builds the wire connectivity graph: OpenCV Hough line detection +
morphology finds wires, then edges connect whichever two detected symbols
each wire segment runs between. Nodes = detections, edges = wires.
"""

from pathlib import Path

import cv2
import numpy as np

from app.models.sld import SLDEdge, SLDNode

INK_THRESHOLD = 128  # separates dark ink (symbols/wires) from the light grid
MASK_PADDING = 4
HOUGH_THRESHOLD = 30
MIN_LINE_LENGTH = 20
MAX_LINE_GAP = 15
MAX_ENDPOINT_DISTANCE = 45.0


def _bbox_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return (x0 + x1) / 2, (y0 + y1) / 2


def _distance_to_bbox(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> float:
    x0, y0, x1, y1 = bbox
    dx = max(x0 - point[0], 0.0, point[0] - x1)
    dy = max(y0 - point[1], 0.0, point[1] - y1)
    return float((dx**2 + dy**2) ** 0.5)


def _nearest_node(
    point: tuple[float, float], nodes: list[SLDNode], max_distance: float = MAX_ENDPOINT_DISTANCE
) -> SLDNode | None:
    best_node: SLDNode | None = None
    best_dist = max_distance
    for node in nodes:
        dist = _distance_to_bbox(point, node.bbox)
        if dist < best_dist:
            best_dist = dist
            best_node = node
    return best_node


def _mask_out_nodes(binary: np.ndarray, nodes: list[SLDNode]) -> np.ndarray:
    masked = binary.copy()
    for node in nodes:
        x0, y0, x1, y1 = node.bbox
        cv2.rectangle(
            masked,
            (int(x0) - MASK_PADDING, int(y0) - MASK_PADDING),
            (int(x1) + MASK_PADDING, int(y1) + MASK_PADDING),
            0,  # type: ignore[call-overload]
            thickness=-1,
        )
    return masked


def build_connectivity_graph(image_path: Path, nodes: list[SLDNode]) -> list[SLDEdge]:
    """Detects wire lines outside the (masked-out) symbol bounding boxes and
    connects whichever two nodes each line's endpoints fall nearest to."""
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    # Ink (symbols + wires) -> white; light background grid -> black.
    _, binary = cv2.threshold(image, INK_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    wires_only = _mask_out_nodes(binary, nodes)

    kernel = np.ones((3, 3), np.uint8)
    wires_only = cv2.morphologyEx(wires_only, cv2.MORPH_CLOSE, kernel)

    lines = cv2.HoughLinesP(
        wires_only,
        1,
        np.pi / 180,
        threshold=HOUGH_THRESHOLD,
        minLineLength=MIN_LINE_LENGTH,
        maxLineGap=MAX_LINE_GAP,
    )

    edge_pairs: set[tuple[str, str]] = set()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = (float(v) for v in line[0])
            node_a = _nearest_node((x1, y1), nodes)
            node_b = _nearest_node((x2, y2), nodes)
            if node_a and node_b and node_a.node_id != node_b.node_id:
                edge_pairs.add(tuple(sorted((node_a.node_id, node_b.node_id))))  # type: ignore[arg-type]

    return [
        SLDEdge(source_node_id=a, target_node_id=b, confidence=1.0) for a, b in sorted(edge_pairs)
    ]
