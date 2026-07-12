"use client";

import type { Verdict } from "@/lib/types";

const STATUS_STYLES: Record<Verdict["status"], { label: string; className: string }> = {
  PASS: { label: "PASS", className: "bg-compliant/15 text-compliant border-compliant/40" },
  NON_CONFORMANCE: {
    label: "NON-CONFORMANCE",
    className: "bg-deviation/15 text-deviation border-deviation/40",
  },
  INSUFFICIENT_DATA: {
    label: "INSUFFICIENT DATA",
    className: "bg-amber/15 text-amber border-amber/40",
  },
};

interface VerdictCardProps {
  verdict: Verdict;
  extractionConfidence?: number;
}

export function VerdictCard({ verdict, extractionConfidence }: VerdictCardProps) {
  const status = STATUS_STYLES[verdict.status];

  return (
    <div className="flex w-72 flex-col gap-4 rounded border border-neutral-800 bg-panel p-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-neutral-500">{verdict.req_id}</span>
        <span
          className={`rounded border px-2 py-0.5 font-mono text-xs font-semibold ${status.className}`}
        >
          {status.label}
        </span>
      </div>

      <dl className="flex flex-col gap-3 text-sm">
        <div>
          <dt className="text-xs text-neutral-500">Required</dt>
          <dd className="font-mono text-neutral-200">{verdict.required}</dd>
        </div>
        <div>
          <dt className="text-xs text-neutral-500">Submitted</dt>
          <dd className="font-mono text-neutral-200">{verdict.submitted ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-neutral-500">Delta</dt>
          <dd
            className={`font-mono font-semibold ${
              verdict.delta_pct !== null && verdict.delta_pct < 0
                ? "text-deviation"
                : "text-compliant"
            }`}
          >
            {verdict.delta_pct !== null ? `${verdict.delta_pct.toFixed(1)}%` : "—"}
          </dd>
        </div>
        {extractionConfidence !== undefined && (
          <div>
            <dt className="text-xs text-neutral-500">Extraction confidence</dt>
            <dd className="font-mono text-neutral-200">
              {(extractionConfidence * 100).toFixed(0)}%
            </dd>
          </div>
        )}
        {verdict.reason && (
          <div>
            <dt className="text-xs text-neutral-500">Reason</dt>
            <dd className="text-neutral-300">{verdict.reason}</dd>
          </div>
        )}
      </dl>

      <div className="flex flex-col gap-2 border-t border-neutral-800 pt-3">
        <button className="rounded border border-deviation/50 bg-deviation/10 px-3 py-1.5 text-xs font-semibold text-deviation transition hover:bg-deviation/20">
          Flag as RFI
        </button>
        <button className="rounded border border-neutral-700 px-3 py-1.5 text-xs font-semibold text-neutral-300 transition hover:border-neutral-500">
          Accept deviation
        </button>
      </div>
    </div>
  );
}
