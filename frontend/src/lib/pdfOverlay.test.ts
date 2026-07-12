import { describe, expect, it } from "vitest";

import { bboxToOverlayStyle } from "./pdfOverlay";

describe("bboxToOverlayStyle", () => {
  it("maps a full-page bbox to the full rendered page at scale 1", () => {
    const style = bboxToOverlayStyle([0, 0, 612, 792], {
      pageWidthPt: 612,
      pageHeightPt: 792,
      renderedWidthPx: 612,
      renderedHeightPx: 792,
    });

    expect(style).toEqual({ left: 0, top: 0, width: 612, height: 792 });
  });

  it("flips the y-axis: a bbox near the PDF bottom lands near the CSS bottom", () => {
    // y0/y1 close to 0 (bottom of PDF page) should produce a large `top`
    // (near the bottom of the CSS box), not a small one.
    const style = bboxToOverlayStyle([10, 20, 200, 60], {
      pageWidthPt: 612,
      pageHeightPt: 792,
      renderedWidthPx: 612,
      renderedHeightPx: 792,
    });

    expect(style.top).toBeCloseTo(792 - 60);
    expect(style.height).toBeCloseTo(40);
    expect(style.left).toBeCloseTo(10);
    expect(style.width).toBeCloseTo(190);
  });

  it("a bbox near the PDF top lands near the CSS top", () => {
    const style = bboxToOverlayStyle([10, 760, 200, 780], {
      pageWidthPt: 612,
      pageHeightPt: 792,
      renderedWidthPx: 612,
      renderedHeightPx: 792,
    });

    expect(style.top).toBeCloseTo(792 - 780);
    expect(style.height).toBeCloseTo(20);
  });

  it("scales proportionally when the rendered page is not 1:1 with PDF points", () => {
    // Rendered at 1.5x the native PDF point size (e.g. react-pdf `scale={1.5}`).
    const style = bboxToOverlayStyle([72, 690, 540, 730], {
      pageWidthPt: 612,
      pageHeightPt: 792,
      renderedWidthPx: 612 * 1.5,
      renderedHeightPx: 792 * 1.5,
    });

    expect(style.left).toBeCloseTo(72 * 1.5);
    expect(style.width).toBeCloseTo((540 - 72) * 1.5);
    expect(style.top).toBeCloseTo((792 - 730) * 1.5);
    expect(style.height).toBeCloseTo((730 - 690) * 1.5);
  });

  it("handles independent x/y scale factors (non-uniform rendering)", () => {
    const style = bboxToOverlayStyle([0, 0, 100, 50], {
      pageWidthPt: 200,
      pageHeightPt: 100,
      renderedWidthPx: 400, // scaleX = 2
      renderedHeightPx: 300, // scaleY = 3
    });

    expect(style).toEqual({ left: 0, top: 150, width: 200, height: 150 });
  });

  it("matches the fixture spec_evidence bbox against the demo PDF page size", () => {
    const style = bboxToOverlayStyle([72, 690, 540, 730], {
      pageWidthPt: 612,
      pageHeightPt: 792,
      renderedWidthPx: 612,
      renderedHeightPx: 792,
    });

    expect(style).toEqual({ left: 72, top: 62, width: 468, height: 40 });
  });
});
