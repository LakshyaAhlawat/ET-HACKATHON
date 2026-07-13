"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { SLDEdge, SLDNode } from "@/lib/types";

// react-force-graph touches canvas/window at module load — same reason
// react-pdf needed ssr:false in the compliance viewer (see Session 1).
const ForceGraph2D = dynamic(
  () => import("react-force-graph").then((mod) => mod.ForceGraph2D),
  { ssr: false, loading: () => <div className="h-96 w-full" /> },
);

const CLASS_COLORS: Record<string, string> = {
  transformer: "#60A5FA",
  breaker: "#F5A623",
  ats: "#C084FC",
  ups: "#34D399",
  generator: "#F472B6",
  busbar: "#94A3B8",
  it_load: "#22D3EE",
};

interface GraphNode {
  id: string;
  node_class: string;
  tag: string | null;
}

interface GraphLink {
  source: string;
  target: string;
  key: string;
}

interface TopologyGraphProps {
  nodes: SLDNode[];
  edges: SLDEdge[];
  highlightedNodeIds: Set<string>;
  highlightedEdgeKeys: Set<string>;
  spofNodeId: string | null;
  flashSpof: boolean;
}

function edgeKey(a: string, b: string): string {
  return [a, b].sort().join("|");
}

export function TopologyGraph({
  nodes,
  edges,
  highlightedNodeIds,
  highlightedEdgeKeys,
  spofNodeId,
  flashSpof,
}: TopologyGraphProps) {
  const graphData = useMemo(
    () => ({
      nodes: nodes.map(
        (n): GraphNode => ({ id: n.node_id, node_class: n.node_class, tag: n.tag }),
      ),
      links: edges.map(
        (e): GraphLink => ({
          source: e.source_node_id,
          target: e.target_node_id,
          key: edgeKey(e.source_node_id, e.target_node_id),
        }),
      ),
    }),
    [nodes, edges],
  );

  return (
    <div className="h-96 w-full overflow-hidden rounded border border-neutral-800 bg-ink">
      <ForceGraph2D
        graphData={graphData}
        nodeId="id"
        // react-force-graph's generics get erased through next/dynamic's
        // type inference, so accessor params come through untyped — cast
        // to our known shape rather than fight the library's generics.
        nodeLabel={(node: unknown) => {
          const n = node as GraphNode;
          return `${n.node_class}${n.tag ? ` — ${n.tag}` : ""}`;
        }}
        nodeColor={(node: unknown) => {
          const n = node as GraphNode;
          if (n.id === spofNodeId && flashSpof) return "#EF4444";
          if (highlightedNodeIds.has(n.id)) return "#34D399";
          return CLASS_COLORS[n.node_class] ?? "#9CA3AF";
        }}
        nodeRelSize={5}
        linkColor={(link: unknown) =>
          highlightedEdgeKeys.has((link as GraphLink).key) ? "#34D399" : "#3F3F46"
        }
        linkWidth={(link: unknown) =>
          highlightedEdgeKeys.has((link as GraphLink).key) ? 3 : 1
        }
        backgroundColor="#0A0C10"
        width={640}
        height={384}
      />
    </div>
  );
}
