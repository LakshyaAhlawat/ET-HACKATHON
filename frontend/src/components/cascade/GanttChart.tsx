"use client";

import type { ScheduledTask } from "@/lib/cascadeSchedule";

const CHART_WIDTH_PX = 720;
const ROW_HEIGHT_PX = 18;
// Shift beyond which a bar is fully red — calibrated to the ~8-week sweep range.
const MAX_SHIFT_DAYS_FOR_FULL_RED = 45;

interface GanttChartProps {
  tasks: ScheduledTask[];
  baselineFinishByTaskId: Record<string, number>;
  maxDay: number;
}

function barColor(shiftDays: number): string {
  const t = Math.max(0, Math.min(1, shiftDays / MAX_SHIFT_DAYS_FOR_FULL_RED));
  // Interpolate compliant green -> amber -> deviation red as the shift grows.
  if (t < 0.5) {
    return mix("#34D399", "#F5A623", t / 0.5);
  }
  return mix("#F5A623", "#EF4444", (t - 0.5) / 0.5);
}

function mix(colorA: string, colorB: string, t: number): string {
  const a = parseInt(colorA.slice(1), 16);
  const b = parseInt(colorB.slice(1), 16);
  const ar = (a >> 16) & 0xff;
  const ag = (a >> 8) & 0xff;
  const ab = a & 0xff;
  const br = (b >> 16) & 0xff;
  const bg = (b >> 8) & 0xff;
  const bb = b & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `rgb(${r}, ${g}, ${bl})`;
}

export function GanttChart({ tasks, baselineFinishByTaskId, maxDay }: GanttChartProps) {
  const pxPerDay = CHART_WIDTH_PX / maxDay;

  return (
    <div className="overflow-x-auto">
      <div style={{ width: CHART_WIDTH_PX + 220 }}>
        {tasks.map((task) => {
          const baselineFinish = baselineFinishByTaskId[task.task_id] ?? task.finish_day;
          const shiftDays = Math.max(0, task.finish_day - baselineFinish);
          const left = task.start_day * pxPerDay;
          const width = Math.max(2, (task.finish_day - task.start_day) * pxPerDay);

          return (
            <div
              key={task.task_id}
              className="flex items-center gap-2"
              style={{ height: ROW_HEIGHT_PX }}
            >
              <div
                className="w-52 shrink-0 truncate font-mono text-[10px] text-neutral-400"
                title={task.name}
              >
                {task.name}
              </div>
              <div className="relative flex-1" style={{ height: ROW_HEIGHT_PX - 4 }}>
                <div
                  className="absolute top-0 h-full rounded-sm transition-[left,width] duration-75 ease-out"
                  style={{
                    left,
                    width,
                    backgroundColor: barColor(shiftDays),
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
