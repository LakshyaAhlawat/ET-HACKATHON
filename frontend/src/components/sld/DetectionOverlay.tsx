"use client";

import { useState } from "react";

import type { SLDNode } from "@/lib/types";

const CLASS_COLORS: Record<string, string> = {
  transformer: "#60A5FA",
  breaker: "#F5A623",
  ats: "#C084FC",
  ups: "#34D399",
  generator: "#F472B6",
  busbar: "#94A3B8",
  it_load: "#22D3EE",
};

interface DetectionOverlayProps {
  imageSrc: string;
  nodes: SLDNode[];
  highlightedNodeIds: Set<string>;
  spofNodeId: string | null;
  flashSpof: boolean;
}

export function DetectionOverlay({
  imageSrc,
  nodes,
  highlightedNodeIds,
  spofNodeId,
  flashSpof,
}: DetectionOverlayProps) {
  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number } | null>(null);
  const [displayWidth, setDisplayWidth] = useState(600);

  const scale = naturalSize ? displayWidth / naturalSize.w : 1;
  const displayHeight = naturalSize ? naturalSize.h * scale : 0;

  return (
    <div
      className="relative inline-block border border-neutral-800 bg-white"
      style={{ width: displayWidth, height: displayHeight || undefined }}
      ref={(el) => {
        if (el && el.clientWidth > 0) setDisplayWidth(el.clientWidth);
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imageSrc}
        alt="Single-line diagram"
        className="block w-full"
        onLoad={(e) => {
          const img = e.currentTarget;
          setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
        }}
      />
      {naturalSize &&
        nodes.map((node) => {
          const [x0, y0, x1, y1] = node.bbox;
          const isSpof = node.node_id === spofNodeId;
          const isHighlighted = highlightedNodeIds.has(node.node_id);
          const color = isSpof && flashSpof ? "#EF4444" : isHighlighted ? "#34D399" : CLASS_COLORS[node.node_class] ?? "#9CA3AF";

          return (
            <div
              key={node.node_id}
              className="absolute rounded-sm border-2 transition-colors duration-150"
              title={`${node.node_class}${node.tag ? ` — ${node.tag}` : ""} (${(node.confidence * 100).toFixed(0)}%)`}
              style={{
                left: x0 * scale,
                top: y0 * scale,
                width: (x1 - x0) * scale,
                height: (y1 - y0) * scale,
                borderColor: color,
                boxShadow: isSpof && flashSpof ? `0 0 8px 2px ${color}` : undefined,
              }}
            />
          );
        })}
    </div>
  );
}
