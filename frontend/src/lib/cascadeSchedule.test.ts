import { describe, expect, it } from "vitest";

import { computeSchedule, interpolateSweep, type CascadeTask, type SweepPoint } from "./cascadeSchedule";

function task(overrides: Partial<CascadeTask> & Pick<CascadeTask, "task_id">): CascadeTask {
  return {
    name: overrides.task_id,
    discipline: "TEST",
    phase: "test",
    duration_mean_days: 10,
    duration_std_days: 1,
    predecessors: [],
    seasonal_window: null,
    is_milestone: true,
    ...overrides,
  };
}

describe("computeSchedule", () => {
  it("computes start/finish for a simple chain A -> B -> C", () => {
    const tasks: CascadeTask[] = [
      task({ task_id: "A", duration_mean_days: 10 }),
      task({ task_id: "B", duration_mean_days: 5, predecessors: ["A"] }),
      task({ task_id: "C", duration_mean_days: 3, predecessors: ["B"] }),
    ];

    const scheduled = computeSchedule(tasks, 0);
    const byId = Object.fromEntries(scheduled.map((t) => [t.task_id, t]));

    expect(byId.A.start_day).toBe(0);
    expect(byId.A.finish_day).toBe(10);
    expect(byId.B.start_day).toBe(10);
    expect(byId.B.finish_day).toBe(15);
    expect(byId.C.start_day).toBe(15);
    expect(byId.C.finish_day).toBe(18);
  });

  it("takes the max of multiple predecessors (the binding constraint)", () => {
    const tasks: CascadeTask[] = [
      task({ task_id: "A", duration_mean_days: 10 }),
      task({ task_id: "B", duration_mean_days: 30 }),
      task({ task_id: "D", duration_mean_days: 2, predecessors: ["A", "B"] }),
    ];

    const scheduled = computeSchedule(tasks, 0);
    const d = scheduled.find((t) => t.task_id === "D")!;

    expect(d.start_day).toBe(30); // B is the binding predecessor, not A
    expect(d.finish_day).toBe(32);
  });

  it("adds the transformer delay (in days) to XFMR-PROCURE specifically", () => {
    const tasks: CascadeTask[] = [
      task({ task_id: "XFMR-PROCURE", duration_mean_days: 10 }),
      task({ task_id: "NEXT", duration_mean_days: 5, predecessors: ["XFMR-PROCURE"] }),
    ];

    const noDelay = computeSchedule(tasks, 0);
    const withDelay = computeSchedule(tasks, 2); // 2 weeks = 14 days

    const nextNoDelay = noDelay.find((t) => t.task_id === "NEXT")!;
    const nextWithDelay = withDelay.find((t) => t.task_id === "NEXT")!;

    expect(nextWithDelay.start_day - nextNoDelay.start_day).toBe(14);
  });

  it("applies the seasonal multiplier only when the task's start falls inside the window", () => {
    const inWindowTasks: CascadeTask[] = [
      task({ task_id: "A", duration_mean_days: 10 }),
      task({
        task_id: "B",
        duration_mean_days: 10,
        predecessors: ["A"],
        seasonal_window: { start_day: 5, end_day: 50, multiplier: 2.0 },
      }),
    ];
    // A finishes at day 10, inside B's [5, 50] window -> B's duration doubles.
    const inWindow = computeSchedule(inWindowTasks, 0);
    expect(inWindow.find((t) => t.task_id === "B")!.finish_day).toBe(10 + 20);

    const outOfWindowTasks: CascadeTask[] = [
      task({ task_id: "A", duration_mean_days: 100 }),
      task({
        task_id: "B",
        duration_mean_days: 10,
        predecessors: ["A"],
        seasonal_window: { start_day: 5, end_day: 50, multiplier: 2.0 },
      }),
    ];
    const outOfWindow = computeSchedule(outOfWindowTasks, 0);
    expect(outOfWindow.find((t) => t.task_id === "B")!.finish_day).toBe(100 + 10);
  });
});

function sweepPoint(overrides: Partial<SweepPoint> & Pick<SweepPoint, "transformer_delay_weeks">): SweepPoint {
  return {
    p50_handover_day: 0,
    p90_handover_day: 0,
    mean_handover_day: 0,
    p_slip: 0,
    histogram_bin_edges: [0, 10, 20],
    histogram_counts: [1, 2],
    ...overrides,
  };
}

describe("interpolateSweep", () => {
  const points: SweepPoint[] = [
    sweepPoint({ transformer_delay_weeks: 0, p_slip: 0.1, p50_handover_day: 200 }),
    sweepPoint({ transformer_delay_weeks: 1, p_slip: 0.3, p50_handover_day: 210 }),
    sweepPoint({ transformer_delay_weeks: 2, p_slip: 0.5, p50_handover_day: 220 }),
  ];

  it("returns the exact point when the delay matches a precomputed step", () => {
    expect(interpolateSweep(points, 1).p_slip).toBeCloseTo(0.3);
  });

  it("linearly interpolates between two adjacent points", () => {
    const mid = interpolateSweep(points, 0.5);
    expect(mid.p_slip).toBeCloseTo(0.2);
    expect(mid.p50_handover_day).toBeCloseTo(205);
  });

  it("clamps to the first point below the sweep range", () => {
    expect(interpolateSweep(points, -5).p_slip).toBeCloseTo(0.1);
  });

  it("clamps to the last point above the sweep range", () => {
    expect(interpolateSweep(points, 50).p_slip).toBeCloseTo(0.5);
  });
});
