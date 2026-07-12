"use client";

import dynamic from "next/dynamic";

import type { Verdict } from "@/lib/types";

import { VerdictCard } from "./VerdictCard";

// react-pdf touches browser-only APIs (canvas, DOMMatrix) at module load via
// pdfjs-dist, which crashes under Next.js SSR even inside a client component
// (client components are still server-rendered on first pass). Must load
// client-side only.
const PdfPane = dynamic(() => import("./PdfPane").then((mod) => mod.PdfPane), {
  ssr: false,
  loading: () => (
    <div className="flex w-[480px] items-center justify-center font-mono text-xs text-neutral-600">
      Loading viewer…
    </div>
  ),
});

interface ComplianceViewerProps {
  verdict: Verdict;
  extractionConfidence?: number;
}

export function ComplianceViewer({ verdict, extractionConfidence }: ComplianceViewerProps) {
  return (
    <div className="flex gap-6 overflow-x-auto p-6">
      <PdfPane
        label={`Spec — ${verdict.spec_evidence.source_doc}`}
        fileUrl={`/fixtures/${verdict.spec_evidence.source_doc}`}
        pageNumber={verdict.spec_evidence.source_page}
        bbox={verdict.spec_evidence.source_bbox}
        highlight="amber"
      />

      <VerdictCard verdict={verdict} extractionConfidence={extractionConfidence} />

      {verdict.submittal_evidence ? (
        <PdfPane
          label={`Submittal — ${verdict.submittal_evidence.source_doc}`}
          fileUrl={`/fixtures/${verdict.submittal_evidence.source_doc}`}
          pageNumber={verdict.submittal_evidence.source_page}
          bbox={verdict.submittal_evidence.source_bbox}
          highlight="deviation"
        />
      ) : (
        <div className="flex w-[480px] items-center justify-center rounded border border-dashed border-neutral-800 font-mono text-xs text-neutral-600">
          No submittal evidence
        </div>
      )}
    </div>
  );
}
