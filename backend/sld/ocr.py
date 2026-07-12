"""Reads tags/ratings text (e.g. "TX-01", "2000 kVA") off an SLD image via
PaddleOCR and associates each text box with its nearest detected symbol.

Offline batch use only, per CLAUDE.md.
"""

import os
from pathlib import Path

from app.models.sld import SLDNode

# PaddleOCR's PP-OCRv6 models crash under MKL-DNN on some Windows CPU builds
# (see ingestion/parse.py for the same fix). Must be set before paddle inits.
os.environ.setdefault("FLAGS_use_mkldnn", "false")


def _bbox_center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return (x0 + x1) / 2, (y0 + y1) / 2


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return float(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5)


def associate_tags(image_path: Path, nodes: list[SLDNode]) -> list[SLDNode]:
    """Runs OCR over the full image and appends each recognized text span to
    whichever detected node's bbox center it's closest to."""
    if not nodes:
        return nodes

    import numpy as np
    from paddleocr import PaddleOCR
    from PIL import Image

    ocr = PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )
    image = np.array(Image.open(image_path).convert("RGB"))
    results = ocr.predict(image)

    updated = [n.model_copy() for n in nodes]
    for page in results:
        texts = page.get("rec_texts", [])
        boxes = page.get("rec_boxes", [])
        for text, box in zip(texts, boxes, strict=True):
            tx0, ty0, tx1, ty1 = (float(v) for v in box)
            text_center = ((tx0 + tx1) / 2, (ty0 + ty1) / 2)

            nearest = min(updated, key=lambda n: _distance(text_center, _bbox_center(n.bbox)))
            nearest.tag = f"{nearest.tag} {text}".strip() if nearest.tag else text

    return updated
