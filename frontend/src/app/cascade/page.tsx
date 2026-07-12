import { CascadeExplorer } from "@/components/cascade/CascadeExplorer";
import type { CascadeTask, SweepPoint } from "@/lib/cascadeSchedule";
import type { MitigationCandidate } from "@/lib/types";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

interface CascadeLookup {
  target_handover_day: number;
  points: SweepPoint[];
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_INTERNAL_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export default async function CascadePage() {
  let tasks: CascadeTask[] = [];
  let lookup: CascadeLookup | null = null;
  let mitigations: MitigationCandidate[] = [];
  let error: string | null = null;

  try {
    [tasks, lookup, mitigations] = await Promise.all([
      fetchJson<CascadeTask[]>("/api/cascade/tasks"),
      fetchJson<CascadeLookup>("/api/cascade/lookup"),
      fetchJson<MitigationCandidate[]>("/api/cascade/mitigations"),
    ]);
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  if (error || !lookup) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-center">
        <p className="font-mono text-sm text-deviation">
          {error ?? "No cascade data returned."}
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-neutral-800 px-6 py-4">
        <h1 className="text-lg font-semibold">Cascade Simulator</h1>
        <p className="font-mono text-xs text-neutral-500">
          {tasks.length} tasks — drag the slider to see the handover-date risk propagate live
        </p>
      </header>
      <CascadeExplorer
        tasks={tasks}
        sweepPoints={lookup.points}
        targetHandoverDay={lookup.target_handover_day}
        mitigations={mitigations}
      />
    </main>
  );
}
