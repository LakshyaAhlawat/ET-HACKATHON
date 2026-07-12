export type PdfBbox = readonly [x0: number, y0: number, x1: number, y1: number];

export interface PdfPageGeometry {
  /** Native PDF page width, in points. */
  pageWidthPt: number;
  /** Native PDF page height, in points. */
  pageHeightPt: number;
  /** Rendered width of the page in the DOM, in CSS pixels. */
  renderedWidthPx: number;
  /** Rendered height of the page in the DOM, in CSS pixels. */
  renderedHeightPx: number;
}

export interface OverlayStyle {
  left: number;
  top: number;
  width: number;
  height: number;
}

/**
 * Converts a PDF-space bounding box (bottom-left origin, points) into a CSS
 * overlay rect (top-left origin, pixels) positioned within a rendered page.
 *
 * PDF y increases upward from the page bottom; CSS `top` increases downward
 * from the page top. Scaling alone is not enough — the y-axis must be
 * flipped against the page height, or the box renders at the mirrored
 * vertical position.
 */
export function bboxToOverlayStyle(bbox: PdfBbox, page: PdfPageGeometry): OverlayStyle {
  const [x0, y0, x1, y1] = bbox;
  const scaleX = page.renderedWidthPx / page.pageWidthPt;
  const scaleY = page.renderedHeightPx / page.pageHeightPt;

  return {
    left: x0 * scaleX,
    top: (page.pageHeightPt - y1) * scaleY,
    width: (x1 - x0) * scaleX,
    height: (y1 - y0) * scaleY,
  };
}
