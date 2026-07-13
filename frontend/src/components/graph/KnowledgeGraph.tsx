"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { GraphEdge, GraphNode } from "@/lib/types";

// react-force-graph touches canvas/window at module load — same reason
// react-pdf needed ssr:false in the compliance viewer (see Session 1).
const ForceGraph2D = dynamic(
  () => import("react-force-graph").then((mod) => mod.ForceGraph2D),
  { ssr: false, loading: () => <div className="h-[32rem] w-full" /> },
);

const TYPE_COLORS: Record<string, string> = {
  spec: "#F5A623",
  equipment: "#60A5FA",
  vendor: "#C084FC",
  shipment: "#F472B6",
  task: "#94A3B8",
};

interface RenderNode {
  id: string;
  node_type: string;
  label: string;
}

interface RenderLink {
  source: string;
  target: string;
  relation: string;
  key: string;
}

function edgeKey(a: string, b: string): string {
  return [a, b].sort().join("|");
}

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodeIds: Set<string>;
  highlightedEdgeKeys: Set<string>;
}

export function KnowledgeGraph({
  nodes,
  edges,
  highlightedNodeIds,
  highlightedEdgeKeys,
}: KnowledgeGraphProps) {
  const graphData = useMemo(
    () => ({
      nodes: nodes.map(
        (n): RenderNode => ({ id: n.node_id, node_type: n.node_type, label: n.label }),
      ),
      links: edges.map(
        (e): RenderLink => ({
          source: e.source,
          target: e.target,
          relation: e.relation,
          key: edgeKey(e.source, e.target),
        }),
      ),
    }),
    [nodes, edges],
  );

  return (
    <div className="h-[32rem] w-full overflow-hidden rounded border border-neutral-800 bg-ink">
      <ForceGraph2D
        graphData={graphData}
        nodeId="id"
        // react-force-graph's generics get erased through next/dynamic's
        // type inference, so accessor params come through untyped — cast
        // to our known shape rather than fight the library's generics.
        nodeLabel={(node: unknown) => {
          const n = node as RenderNode;
          return `${n.node_type}: ${n.label}`;
        }}
        nodeColor={(node: unknown) => {
          const n = node as RenderNode;
          if (highlightedNodeIds.has(n.id)) return "#34D399";
          return TYPE_COLORS[n.node_type] ?? "#9CA3AF";
        }}
        nodeRelSize={4}
        linkColor={(link: unknown) =>
          highlightedEdgeKeys.has((link as RenderLink).key) ? "#34D399" : "#3F3F46"
        }
        linkWidth={(link: unknown) =>
          highlightedEdgeKeys.has((link as RenderLink).key) ? 3 : 1
        }
        linkDirectionalArrowLength={(link: unknown) =>
          highlightedEdgeKeys.has((link as RenderLink).key) ? 5 : 2
        }
        linkDirectionalArrowRelPos={1}
        backgroundColor="#0A0C10"
        width={720}
        height={512}
      />
    </div>
  );
}
