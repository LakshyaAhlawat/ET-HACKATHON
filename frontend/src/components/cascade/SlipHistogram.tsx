"use client";

import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface SlipHistogramProps {
  binEdges: number[];
  counts: number[];
  targetHandoverDay: number;
}

export function SlipHistogram({ binEdges, counts, targetHandoverDay }: SlipHistogramProps) {
  const data = counts.map((count, i) => ({
    binMid: (binEdges[i] + binEdges[i + 1]) / 2,
    count,
  }));

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <XAxis
            dataKey="binMid"
            type="number"
            domain={[binEdges[0], binEdges[binEdges.length - 1]]}
            tickFormatter={(v: number) => `d${Math.round(v)}`}
            stroke="#525252"
            fontSize={10}
            fontFamily="var(--font-jetbrains-mono)"
          />
          <YAxis stroke="#525252" fontSize={10} fontFamily="var(--font-jetbrains-mono)" />
          <ReferenceLine
            x={targetHandoverDay}
            stroke="#F5A623"
            strokeWidth={2}
            strokeDasharray="4 3"
            label={{
              value: "target",
              position: "top",
              fill: "#F5A623",
              fontSize: 10,
              fontFamily: "var(--font-jetbrains-mono)",
            }}
          />
          <Bar dataKey="count" isAnimationActive={false}>
            {data.map((point, i) => (
              <Cell
                key={i}
                fill={point.binMid > targetHandoverDay ? "#EF4444" : "#34D399"}
                fillOpacity={point.binMid > targetHandoverDay ? 0.85 : 0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
