// Client-side deterministic forward-pass (mean durations only, no Monte
// Carlo) so the Gantt chart can redraw instantly on every slider tick —
// the actual uncertainty distribution comes from the precomputed sweep
// lookup instead. Mirrors backend/cascade/simulate.py's forward-pass logic.

export interface SeasonalWindow {
  start_day: number;
  end_day: number;
  multiplier: number;
}

export interface CascadeTask {
  task_id: string;
  name: string;
  discipline: string;
  phase: string;
  duration_mean_days: number;
  duration_std_days: number;
  predecessors: string[];
  seasonal_window: SeasonalWindow | null;
  is_milestone: boolean;
}

export interface ScheduledTask extends CascadeTask {
  start_day: number;
  finish_day: number;
}

const TRANSFORMER_DELAY_TASK_ID = "XFMR-PROCURE";

export function computeSchedule(tasks: CascadeTask[], transformerDelayWeeks: number): ScheduledTask[] {
  const byId = new Map(tasks.map((t) => [t.task_id, t]));
  const inDegree = new Map<string, number>();
  const successors = new Map<string, string[]>();

  for (const t of tasks) {
    inDegree.set(t.task_id, t.predecessors.length);
    for (const pred of t.predecessors) {
      const list = successors.get(pred) ?? [];
      list.push(t.task_id);
      successors.set(pred, list);
    }
  }

  const queue: string[] = tasks.filter((t) => t.predecessors.length === 0).map((t) => t.task_id);
  const start = new Map<string, number>();
  const finish = new Map<string, number>();
  const extraDelayDays = transformerDelayWeeks * 7;

  while (queue.length > 0) {
    const id = queue.shift() as string;
    const task = byId.get(id) as CascadeTask;

    const startDay =
      task.predecessors.length === 0
        ? 0
        : Math.max(...task.predecessors.map((p) => finish.get(p) ?? 0));
    start.set(id, startDay);

    let duration = task.duration_mean_days;
    if (id === TRANSFORMER_DELAY_TASK_ID) {
      duration += extraDelayDays;
    }
    if (task.seasonal_window) {
      const { start_day, end_day, multiplier } = task.seasonal_window;
      if (startDay >= start_day && startDay <= end_day) {
        duration *= multiplier;
      }
    }
    finish.set(id, startDay + duration);

    for (const successor of successors.get(id) ?? []) {
      const remaining = (inDegree.get(successor) ?? 0) - 1;
      inDegree.set(successor, remaining);
      if (remaining === 0) {
        queue.push(successor);
      }
    }
  }

  return tasks.map((t) => ({
    ...t,
    start_day: start.get(t.task_id) ?? 0,
    finish_day: finish.get(t.task_id) ?? 0,
  }));
}

export interface SweepPoint {
  transformer_delay_weeks: number;
  p50_handover_day: number;
  p90_handover_day: number;
  mean_handover_day: number;
  p_slip: number;
  histogram_bin_edges: number[];
  histogram_counts: number[];
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Linearly interpolates between the two precomputed sweep points bracketing
 * `delayWeeks`, so a continuously-dragged slider reads a smooth value
 * instead of snapping between the fixed 0.5-week precomputed steps. */
export function interpolateSweep(points: SweepPoint[], delayWeeks: number): SweepPoint {
  const first = points[0];
  const last = points[points.length - 1];
  if (delayWeeks <= first.transformer_delay_weeks) return first;
  if (delayWeeks >= last.transformer_delay_weeks) return last;

  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i];
    const b = points[i + 1];
    if (delayWeeks >= a.transformer_delay_weeks && delayWeeks <= b.transformer_delay_weeks) {
      const span = b.transformer_delay_weeks - a.transformer_delay_weeks;
      const t = span === 0 ? 0 : (delayWeeks - a.transformer_delay_weeks) / span;
      return {
        transformer_delay_weeks: delayWeeks,
        p50_handover_day: lerp(a.p50_handover_day, b.p50_handover_day, t),
        p90_handover_day: lerp(a.p90_handover_day, b.p90_handover_day, t),
        mean_handover_day: lerp(a.mean_handover_day, b.mean_handover_day, t),
        p_slip: lerp(a.p_slip, b.p_slip, t),
        histogram_bin_edges: a.histogram_bin_edges,
        histogram_counts: a.histogram_counts.map((count, idx) =>
          Math.round(lerp(count, b.histogram_counts[idx], t)),
        ),
      };
    }
  }
  return last;
}
