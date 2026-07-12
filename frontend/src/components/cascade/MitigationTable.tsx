"use client";

import type { MitigationCandidate } from "@/lib/types";

function formatInr(amount: number): string {
  if (amount === 0) return "Rs 0 (free)";
  return `Rs ${amount.toLocaleString("en-IN")}`;
}

interface MitigationTableProps {
  mitigations: MitigationCandidate[];
}

export function MitigationTable({ mitigations }: MitigationTableProps) {
  return (
    <div className="overflow-x-auto rounded border border-neutral-800">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-xs uppercase tracking-wider text-neutral-500">
            <th className="px-3 py-2">Intervention</th>
            <th className="px-3 py-2">Cost</th>
            <th className="px-3 py-2">P(slip) before</th>
            <th className="px-3 py-2">P(slip) after</th>
            <th className="px-3 py-2">Delta</th>
          </tr>
        </thead>
        <tbody>
          {mitigations.map((m) => (
            <tr
              key={m.intervention_id}
              className={`border-b border-neutral-900 last:border-0 ${
                m.is_zero_cost ? "bg-compliant/10" : ""
              }`}
            >
              <td className="px-3 py-2">
                <div className="font-medium text-neutral-200">
                  {m.name}
                  {m.is_zero_cost && (
                    <span className="ml-2 rounded border border-compliant/40 bg-compliant/15 px-1.5 py-0.5 font-mono text-[10px] text-compliant">
                      ZERO-COST
                    </span>
                  )}
                </div>
                <div className="mt-0.5 text-xs text-neutral-500">{m.description}</div>
              </td>
              <td className="px-3 py-2 font-mono text-neutral-300">{formatInr(m.cost_inr)}</td>
              <td className="px-3 py-2 font-mono text-neutral-300">
                {(m.baseline_p_slip * 100).toFixed(1)}%
              </td>
              <td className="px-3 py-2 font-mono text-compliant">
                {(m.mitigated_p_slip * 100).toFixed(1)}%
              </td>
              <td className="px-3 py-2 font-mono font-semibold text-compliant">
                -{(m.delta_p_slip * 100).toFixed(1)}pp
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
