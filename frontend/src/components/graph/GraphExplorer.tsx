"use client";

import { useMemo, useState } from "react";

import type { GraphResult, TraversalResult } from "@/lib/types";

import { KnowledgeGraph } from "./KnowledgeGraph";

const STEP_MS = 450;

function pathEdgeKeys(pathNodeIds: string[]): string[] {
  const keys: string[] = [];
  for (let i = 0; i < pathNodeIds.length - 1; i++) {
    keys.push([pathNodeIds[i], pathNodeIds[i + 1]].sort().join("|"));
  }
  return keys;
}

interface GraphExplorerProps {
  graph: GraphResult;
  traversals: TraversalResult[];
}

export function GraphExplorer({ graph, traversals }: GraphExplorerProps) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [revealCount, setRevealCount] = useState(0);

  const traversal = traversals[selectedIdx];

  function tracePath() {
    setRevealCount(0);
    const steps = traversal.path_node_ids.length;
    for (let i = 1; i <= steps; i++) {
      setTimeout(() => setRevealCount(i), i * STEP_MS);
    }
  }

  const revealedNodeIds = useMemo(
    () => new Set(traversal.path_node_ids.slice(0, revealCount)),
    [traversal, revealCount],
  );
  const revealedEdgeKeys = useMemo(
    () => new Set(pathEdgeKeys(traversal.path_node_ids.slice(0, revealCount))),
    [traversal, revealCount],
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-wrap items-center gap-3">
        {traversals.map((t, idx) => (
          <button
            key={t.start_node_id ?? idx}
            onClick={() => {
              setSelectedIdx(idx);
              setRevealCount(0);
            }}
            className={`rounded border px-3 py-1.5 font-mono text-xs transition ${
              idx === selectedIdx
                ? "border-amber bg-amber/15 text-amber"
                : "border-neutral-800 text-neutral-400 hover:border-neutral-600"
            }`}
          >
            {t.start_node_id ?? "?"}
          </button>
        ))}
        <button
          onClick={tracePath}
          disabled={traversal.path_node_ids.length === 0}
          className="ml-auto rounded border border-compliant/50 bg-compliant/10 px-4 py-1.5 font-mono text-xs font-semibold text-compliant transition hover:bg-compliant/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Trace: Spec &rarr; Equipment &rarr; Vendor &rarr; Shipment &rarr; Handover
        </button>
      </div>

      <p className="font-mono text-xs text-neutral-500">{traversal.reason}</p>

      <KnowledgeGraph
        nodes={graph.nodes}
        edges={graph.edges}
        highlightedNodeIds={revealedNodeIds}
        highlightedEdgeKeys={revealedEdgeKeys}
      />

      <div className="flex flex-wrap gap-2">
        {traversal.nodes.map((node, idx) => (
          <span
            key={node.node_id}
            className={`rounded border px-2 py-1 font-mono text-xs transition ${
              idx < revealCount
                ? "border-compliant/40 bg-compliant/15 text-compliant"
                : "border-neutral-800 text-neutral-500"
            }`}
          >
            {node.node_type}: {node.label}
          </span>
        ))}
      </div>
    </div>
  );
}
