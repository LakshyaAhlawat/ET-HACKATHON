"use client";

import { useMemo, useState } from "react";

import { computeSchedule, interpolateSweep, type CascadeTask, type SweepPoint } from "@/lib/cascadeSchedule";
import type { MitigationCandidate } from "@/lib/types";

import { GanttChart } from "./GanttChart";
import { MitigationTable } from "./MitigationTable";
import { SlipHistogram } from "./SlipHistogram";

const MIN_DELAY_WEEKS = 0;
const MAX_DELAY_WEEKS = 8;
const SLIDER_STEP = 0.1;

interface CascadeExplorerProps {
  tasks: CascadeTask[];
  sweepPoints: SweepPoint[];
  targetHandoverDay: number;
  mitigations: MitigationCandidate[];
}

function pSlipColor(pSlip: number): string {
  if (pSlip < 0.15) return "text-compliant";
  if (pSlip < 0.5) return "text-amber";
  return "text-deviation";
}

export function CascadeExplorer({
  tasks,
  sweepPoints,
  targetHandoverDay,
  mitigations,
}: CascadeExplorerProps) {
  const [delayWeeks, setDelayWeeks] = useState(0);

  const milestoneTasks = useMemo(() => tasks.filter((t) => t.is_milestone), [tasks]);

  // Fixed baseline (zero delay) so Gantt bars only ever shift forward from a
  // stable reference, and a fixed max-day scale from the worst case (8
  // weeks) so the chart's timeline doesn't rescale as you drag.
  const baselineSchedule = useMemo(() => computeSchedule(tasks, 0), [tasks]);
  const baselineFinishByTaskId = useMemo(
    () => Object.fromEntries(baselineSchedule.map((t) => [t.task_id, t.finish_day])),
    [baselineSchedule],
  );
  const maxDay = useMemo(() => {
    const worstCase = computeSchedule(tasks, MAX_DELAY_WEEKS);
    return Math.max(...worstCase.map((t) => t.finish_day));
  }, [tasks]);

  const scheduledTasks = useMemo(() => {
    const full = computeSchedule(tasks, delayWeeks);
    const byId = new Set(milestoneTasks.map((t) => t.task_id));
    return full.filter((t) => byId.has(t.task_id));
  }, [tasks, delayWeeks, milestoneTasks]);

  const sweep = useMemo(() => interpolateSweep(sweepPoints, delayWeeks), [sweepPoints, delayWeeks]);

  return (
    <div className="flex flex-col gap-8 p-6">
      <div className="flex flex-col gap-3 rounded border border-neutral-800 bg-panel p-4">
        <div className="flex items-baseline justify-between">
          <label htmlFor="delay-slider" className="font-mono text-xs uppercase tracking-wider text-neutral-500">
            Transformer supply delay
          </label>
          <span className="font-mono text-sm text-neutral-300">{delayWeeks.toFixed(1)} weeks</span>
        </div>
        <input
          id="delay-slider"
          type="range"
          min={MIN_DELAY_WEEKS}
          max={MAX_DELAY_WEEKS}
          step={SLIDER_STEP}
          value={delayWeeks}
          onChange={(e) => setDelayWeeks(parseFloat(e.target.value))}
          className="h-2 w-full cursor-pointer appearance-none rounded-full bg-neutral-800 accent-amber"
        />
        <div className="flex items-center justify-between pt-2">
          <span className="font-mono text-xs text-neutral-500">P(slip past target)</span>
          <span className={`font-mono text-4xl font-bold tabular-nums ${pSlipColor(sweep.p_slip)}`}>
            {(sweep.p_slip * 100).toFixed(1)}%
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 border-t border-neutral-800 pt-3 font-mono text-xs text-neutral-400">
          <div>
            P50 handover: <span className="text-neutral-200">day {sweep.p50_handover_day.toFixed(0)}</span>
          </div>
          <div>
            P90 handover: <span className="text-neutral-200">day {sweep.p90_handover_day.toFixed(0)}</span>
          </div>
          <div>
            Target: <span className="text-amber">day {targetHandoverDay.toFixed(0)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded border border-neutral-800 bg-panel p-4">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-wider text-neutral-500">
            Schedule (milestones)
          </h2>
          <GanttChart
            tasks={scheduledTasks}
            baselineFinishByTaskId={baselineFinishByTaskId}
            maxDay={maxDay}
          />
        </div>
        <div className="rounded border border-neutral-800 bg-panel p-4">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-wider text-neutral-500">
            Handover-date distribution (10,000 runs)
          </h2>
          <SlipHistogram
            binEdges={sweep.histogram_bin_edges}
            counts={sweep.histogram_counts}
            targetHandoverDay={targetHandoverDay}
          />
        </div>
      </div>

      <div>
        <h2 className="mb-3 font-mono text-xs uppercase tracking-wider text-neutral-500">
          Ranked mitigations (baseline: 3-week transformer delay)
        </h2>
        <MitigationTable mitigations={mitigations} />
      </div>
    </div>
  );
}
