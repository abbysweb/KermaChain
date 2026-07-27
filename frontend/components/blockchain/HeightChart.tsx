"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface HeightChartProps {
  data: { height: number; timestamp: number; txCount: number }[];
}

export function HeightChart({ data }: HeightChartProps) {
  const chartData = data
    .slice()
    .reverse()
    .map((b) => ({
      height: b.height,
      time: new Date(b.timestamp * 1000).toLocaleTimeString(),
      txCount: b.txCount,
    }));

  return (
    <div className="glass overflow-hidden rounded-2xl p-5">
      <h3 className="mb-4 text-sm font-semibold text-gray-800">
        Chain Growth
      </h3>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorHeight" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4f6ef7" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#4f6ef7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="height"
            stroke="#9ca3af"
            fontSize={10}
            tickLine={false}
          />
          <YAxis stroke="#9ca3af" fontSize={10} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(255,255,255,0.9)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(0,0,0,0.08)",
              borderRadius: "12px",
              fontSize: "12px",
              boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
            }}
            labelStyle={{ color: "#1a1a2e", fontWeight: 600 }}
          />
          <Area
            type="monotone"
            dataKey="height"
            stroke="#4f6ef7"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorHeight)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
