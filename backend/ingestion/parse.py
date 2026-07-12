"""Deterministic document parsing: PDFs -> page+bbox-anchored DocChunks.

Docling handles spec PDFs (layout-aware prose + section structure). Camelot
handles vendor cut-sheet tables (submittals often mix tables with narrative
text, so submittal parsing also runs Docling text extraction and merges both).
PaddleOCR is the fallback when a page has no extractable digital text layer
(i.e. it's a scan) — triggered automatically, not called directly by callers.

This module only produces text; it does not interpret it. That's extract.py's
job, per CLAUDE.md's architectural rule.
"""

import os
from pathlib import Path

import camelot
from docling.document_converter import DocumentConverter

from ingestion.models import DocChunk

# PaddleOCR's PP-OCRv6 models crash under MKL-DNN on some Windows CPU builds
# (paddle 3.3.1 hits `NotImplementedError` in onednn_instruction.cc). Must be
# set before paddle initializes, so it lives at module scope, not per-call.
os.environ.setdefault("FLAGS_use_mkldnn", "false")

_OCR_RENDER_DPI = 200


def _docling_text_chunks(path: Path) -> list[DocChunk]:
    converter = DocumentConverter()
    result = converter.convert(str(path))

    chunks: list[DocChunk] = []
    for item, _level in result.document.iterate_items():
        text = getattr(item, "text", None)
        if not text or not text.strip():
            continue
        prov = getattr(item, "prov", None)
        if not prov:
            continue
        box = prov[0].bbox
        chunks.append(
            DocChunk(
                text=text,
                source_doc=path.name,
                page=prov[0].page_no,
                bbox=(box.l, box.b, box.r, box.t),
            )
        )
    return chunks


def _camelot_table_chunks(path: Path) -> list[DocChunk]:
    try:
        tables = camelot.read_pdf(str(path), pages="all")  # type: ignore[attr-defined]
    except Exception:
        return []

    chunks: list[DocChunk] = []
    for table in tables:
        rows_text = "\n".join(" | ".join(str(cell) for cell in row) for row in table.data)
        chunks.append(
            DocChunk(
                text=rows_text,
                source_doc=path.name,
                page=table.page,
                bbox=tuple(table._bbox),
                is_table=True,
            )
        )
    return chunks


def _ocr_fallback_chunks(path: Path) -> list[DocChunk]:
    try:
        import numpy as np
        import pypdfium2 as pdfium
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            f"No extractable text layer found in {path.name} and PaddleOCR is not "
            "installed. Install it to OCR scanned pages: "
            "pip install paddleocr paddlepaddle"
        ) from exc

    ocr = PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )
    pdf = pdfium.PdfDocument(str(path))
    px_to_pt = 72 / _OCR_RENDER_DPI

    chunks: list[DocChunk] = []
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        _page_width_pt, page_height_pt = page.get_size()
        image = page.render(scale=_OCR_RENDER_DPI / 72).to_pil()

        for page_result in ocr.predict(np.array(image)):
            texts = page_result["rec_texts"]
            boxes = page_result["rec_boxes"]
            for text, box in zip(texts, boxes, strict=True):
                px0, py0, px1, py1 = box
                chunks.append(
                    DocChunk(
                        text=text,
                        source_doc=path.name,
                        page=page_index + 1,
                        bbox=(
                            px0 * px_to_pt,
                            page_height_pt - (py1 * px_to_pt),
                            px1 * px_to_pt,
                            page_height_pt - (py0 * px_to_pt),
                        ),
                    )
                )
    return chunks


def parse_spec_pdf(path: Path) -> list[DocChunk]:
    """Parse a spec PDF into text chunks via Docling, falling back to OCR
    for pages with no digital text layer."""
    chunks = _docling_text_chunks(path)
    return chunks if chunks else _ocr_fallback_chunks(path)


def parse_submittal_pdf(path: Path) -> list[DocChunk]:
    """Parse a vendor submittal/cut-sheet PDF: tables via Camelot, narrative
    text via Docling, falling back to OCR if neither finds anything."""
    chunks = _camelot_table_chunks(path) + _docling_text_chunks(path)
    return chunks if chunks else _ocr_fallback_chunks(path)
