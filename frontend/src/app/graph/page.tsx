import { GraphExplorer } from "@/components/graph/GraphExplorer";
import type { GraphResult, TraversalResult } from "@/lib/types";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

// A handful of spec clauses whose submittals name a vendor, so each traces
// a full Spec -> Equipment -> Vendor -> Shipment -> ... -> HANDOVER path.
// See backend/graph/build.py's _VENDOR_MAP for why not every clause qualifies.
const EXAMPLE_CLAUSES = ["MECH-3.4.2", "ELEC-3.1.1", "DIV-16-16.1.2", "ELEC-2.8.3"];

async function fetchGraph(): Promise<GraphResult> {
  const res = await fetch(`${API_INTERNAL_URL}/api/graph`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`/api/graph failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

async function fetchTraversal(startReqId: string): Promise<TraversalResult> {
  const res = await fetch(
    `${API_INTERNAL_URL}/api/graph/traverse?start_req_id=${encodeURIComponent(startReqId)}`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    throw new Error(`/api/graph/traverse failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export default async function GraphPage() {
  let graph: GraphResult | null = null;
  let traversals: TraversalResult[] = [];
  let error: string | null = null;

  try {
    graph = await fetchGraph();
    traversals = await Promise.all(EXAMPLE_CLAUSES.map(fetchTraversal));
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  if (error || !graph) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-center">
        <p className="font-mono text-sm text-deviation">
          {error ?? "No graph data returned."}
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-neutral-800 px-6 py-4">
        <h1 className="text-lg font-semibold">Knowledge Graph</h1>
        <p className="font-mono text-xs text-neutral-500">
          {graph.nodes.length} nodes, {graph.edges.length} edges — Spec --REQUIRES--&gt;
          Equipment --SUBMITTED_BY--&gt; Vendor --DELIVERS--&gt; Shipment --BLOCKS--&gt; Task,
          Task being the real 111-task cascade schedule
        </p>
      </header>
      <GraphExplorer graph={graph} traversals={traversals} />
    </main>
  );
}
