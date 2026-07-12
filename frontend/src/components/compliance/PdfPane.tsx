"use client";

import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import { bboxToOverlayStyle, type PdfBbox } from "@/lib/pdfOverlay";

// Served as a static asset from public/ (see scripts/copy-pdf-worker.mjs) —
// deliberately not `new URL(..., import.meta.url)`, which pulls the worker
// into webpack's bundle and breaks Terser (the worker is itself an ES module).
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

const PAGE_WIDTH_PX = 480;

type HighlightColor = "amber" | "deviation";

const HIGHLIGHT_CLASSES: Record<HighlightColor, string> = {
  amber: "border-amber shadow-[0_0_0_1px_rgba(245,166,35,0.6)]",
  deviation: "border-deviation shadow-[0_0_0_1px_rgba(239,68,68,0.6)]",
};

interface PdfPaneProps {
  label: string;
  fileUrl: string;
  pageNumber: number;
  bbox: PdfBbox;
  highlight: HighlightColor;
}

export function PdfPane({ label, fileUrl, pageNumber, bbox, highlight }: PdfPaneProps) {
  const [pageSize, setPageSize] = useState<{ widthPt: number; heightPt: number } | null>(null);

  const overlayStyle = pageSize
    ? bboxToOverlayStyle(bbox, {
        pageWidthPt: pageSize.widthPt,
        pageHeightPt: pageSize.heightPt,
        renderedWidthPx: PAGE_WIDTH_PX,
        renderedHeightPx: PAGE_WIDTH_PX * (pageSize.heightPt / pageSize.widthPt),
      })
    : null;

  return (
    <div className="flex flex-col gap-2">
      <div className="font-mono text-xs uppercase tracking-wider text-neutral-500">{label}</div>
      <div className="relative inline-block border border-neutral-800 bg-white">
        <Document file={fileUrl} loading={<PaneLoading />}>
          <Page
            pageNumber={pageNumber}
            width={PAGE_WIDTH_PX}
            onLoadSuccess={(page) =>
              setPageSize({ widthPt: page.originalWidth, heightPt: page.originalHeight })
            }
            renderAnnotationLayer={false}
            renderTextLayer={false}
          />
        </Document>
        {overlayStyle && (
          <div
            className={`pointer-events-none absolute border-2 ${HIGHLIGHT_CLASSES[highlight]}`}
            style={{
              left: overlayStyle.left,
              top: overlayStyle.top,
              width: overlayStyle.width,
              height: overlayStyle.height,
            }}
          />
        )}
      </div>
    </div>
  );
}

function PaneLoading() {
  return (
    <div
      style={{ width: PAGE_WIDTH_PX, height: PAGE_WIDTH_PX * 1.294 }}
      className="flex items-center justify-center bg-panel font-mono text-xs text-neutral-500"
    >
      Loading PDF…
    </div>
  );
}
