"use client";

import { useMemo, useState } from "react";

import type { SldTopologyResult } from "@/lib/types";

import { DetectionOverlay } from "./DetectionOverlay";
import { RedundancyVerdict } from "./RedundancyVerdict";
import { TopologyGraph } from "./TopologyGraph";

type Phase = "idle" | "path_a" | "path_b" | "collide" | "settled";

const STEP_MS = 800;

function pathEdgeKeys(path: string[]): string[] {
  const keys: string[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    keys.push([path[i], path[i + 1]].sort().join("|"));
  }
  return keys;
}

interface SldExplorerProps {
  topologies: SldTopologyResult[];
}

export function SldExplorer({ topologies }: SldExplorerProps) {
  const [selectedId, setSelectedId] = useState(topologies[0]?.topology_id);
  const [phase, setPhase] = useState<Phase>("idle");

  const topology = topologies.find((t) => t.topology_id === selectedId) ?? topologies[0];
  const [pathA, pathB] = topology.redundancy.traced_paths;

  function tracePaths() {
    setPhase("path_a");
    const timers: ReturnType<typeof setTimeout>[] = [];
    timers.push(setTimeout(() => setPhase("path_b"), STEP_MS));
    if (!topology.redundancy.holds && topology.redundancy.spof_node_id) {
      timers.push(setTimeout(() => setPhase("collide"), STEP_MS * 2));
      timers.push(setTimeout(() => setPhase("settled"), STEP_MS * 3));
    } else {
      timers.push(setTimeout(() => setPhase("settled"), STEP_MS * 2));
    }
  }

  const highlightedNodeIds = useMemo(() => {
    const ids = new Set<string>();
    if (phase === "idle") return ids;
    if (pathA) pathA.forEach((id) => ids.add(id));
    if (phase !== "path_a" && pathB) pathB.forEach((id) => ids.add(id));
    return ids;
  }, [phase, pathA, pathB]);

  const highlightedEdgeKeys = useMemo(() => {
    const keys = new Set<string>();
    if (phase === "idle") return keys;
    if (pathA) pathEdgeKeys(pathA).forEach((k) => keys.add(k));
    if (phase !== "path_a" && pathB) pathEdgeKeys(pathB).forEach((k) => keys.add(k));
    return keys;
  }, [phase, pathA, pathB]);

  const flashSpof = phase === "collide" || phase === "settled";

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-wrap items-center gap-3">
        {topologies.map((t) => (
          <button
            key={t.topology_id}
            onClick={() => {
              setSelectedId(t.topology_id);
              setPhase("idle");
            }}
            className={`rounded border px-3 py-1.5 font-mono text-xs transition ${
              t.topology_id === selectedId
                ? "border-amber bg-amber/15 text-amber"
                : "border-neutral-800 text-neutral-400 hover:border-neutral-600"
            }`}
          >
            {t.topology_id}
          </button>
        ))}
        <button
          onClick={tracePaths}
          disabled={!pathA || !pathB}
          className="ml-auto rounded border border-compliant/50 bg-compliant/10 px-4 py-1.5 font-mono text-xs font-semibold text-compliant transition hover:bg-compliant/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Trace paths: IT-load &rarr; source
        </button>
      </div>

      <h2 className="font-mono text-sm text-neutral-400">{topology.name}</h2>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-2">
          <h3 className="font-mono text-xs uppercase tracking-wider text-neutral-500">
            Raw SLD — YOLO detections
          </h3>
          <DetectionOverlay
            imageSrc={topology.image_path}
            nodes={topology.nodes}
            highlightedNodeIds={highlightedNodeIds}
            spofNodeId={topology.redundancy.spof_node_id}
            flashSpof={flashSpof}
          />
        </div>
        <div className="flex flex-col gap-2">
          <h3 className="font-mono text-xs uppercase tracking-wider text-neutral-500">
            Extracted topology — force graph
          </h3>
          <TopologyGraph
            nodes={topology.nodes}
            edges={topology.edges}
            highlightedNodeIds={highlightedNodeIds}
            highlightedEdgeKeys={highlightedEdgeKeys}
            spofNodeId={topology.redundancy.spof_node_id}
            flashSpof={flashSpof}
          />
        </div>
      </div>

      <RedundancyVerdict redundancy={topology.redundancy} />
    </div>
  );
}
