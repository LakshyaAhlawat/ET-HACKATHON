import { SldExplorer } from "@/components/sld/SldExplorer";
import type { SldTopologyResult } from "@/lib/types";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

async function fetchTopologies(): Promise<SldTopologyResult[]> {
  const res = await fetch(`${API_INTERNAL_URL}/api/sld/topologies`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`/api/sld/topologies failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export default async function SldPage() {
  let topologies: SldTopologyResult[] = [];
  let error: string | null = null;

  try {
    topologies = await fetchTopologies();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  if (error || topologies.length === 0) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-center">
        <p className="font-mono text-sm text-deviation">
          {error ?? "No SLD topology data returned."}
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-neutral-800 px-6 py-4">
        <h1 className="text-lg font-semibold">SLD Redundancy Analyser</h1>
        <p className="font-mono text-xs text-neutral-500">
          {topologies.length} diagrams — YOLOv8 detections + Hough wire connectivity + NetworkX
          2N reachability
        </p>
      </header>
      <SldExplorer topologies={topologies} />
    </main>
  );
}
