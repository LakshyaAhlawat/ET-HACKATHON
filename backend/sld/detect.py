"""Runs the trained YOLOv8 symbol detector against an SLD image.

Offline batch use only — see precompute.py. Detections ship as JSON;
no live inference happens in the API layer.
"""

from pathlib import Path

from ultralytics import YOLO  # type: ignore[attr-defined]

from app.models.sld import SLDNode
from sld.symbols import CLASSES

MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "sld_runs"
    / "symbol_detector"
    / "weights"
    / "best.pt"
)

_model: YOLO | None = None


def _get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(str(MODEL_PATH))
    return _model


def detect_symbols(image_path: Path, conf_threshold: float = 0.5) -> list[SLDNode]:
    model = _get_model()
    results = model.predict(str(image_path), conf=conf_threshold, verbose=False)
    result = results[0]

    boxes = result.boxes if result.boxes is not None else []
    nodes = []
    for i, box in enumerate(boxes):
        cls_idx = int(box.cls.item())
        conf = float(box.conf.item())
        x0, y0, x1, y1 = (float(v) for v in box.xyxy[0].tolist())
        nodes.append(
            SLDNode(
                node_id=f"det-{i}",
                node_class=CLASSES[cls_idx],
                bbox=(x0, y0, x1, y1),
                confidence=conf,
            )
        )
    return nodes
