"use client";

import type { RedundancyResult } from "@/lib/types";

interface RedundancyVerdictProps {
  redundancy: RedundancyResult;
}

export function RedundancyVerdict({ redundancy }: RedundancyVerdictProps) {
  return (
    <div className="flex flex-col gap-2 rounded border border-neutral-800 bg-panel p-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wider text-neutral-500">
          Claimed: {redundancy.claimed_redundancy}
        </span>
        <span
          className={`rounded border px-2 py-0.5 font-mono text-xs font-semibold ${
            redundancy.holds
              ? "border-compliant/40 bg-compliant/15 text-compliant"
              : "border-deviation/40 bg-deviation/15 text-deviation"
          }`}
        >
          {redundancy.holds ? "2N HOLDS" : "SPOF DETECTED"}
        </span>
      </div>
      <p className="text-sm text-neutral-300">{redundancy.reason}</p>
      {redundancy.spof_node_id && (
        <p className="font-mono text-xs text-deviation">
          Single point of failure: {redundancy.spof_node_id}
        </p>
      )}
    </div>
  );
}
