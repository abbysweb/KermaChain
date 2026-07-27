"use client";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: string;
  color: "blue" | "emerald" | "violet" | "amber" | "rose";
  subtext?: string;
  tooltip?: string;
}

const colorConfig = {
  blue: {
    iconBg: "bg-[#4f6ef7]/10",
    iconText: "text-[#4f6ef7]",
    ring: "ring-[#4f6ef7]/20",
  },
  emerald: {
    iconBg: "bg-[#10b981]/10",
    iconText: "text-[#10b981]",
    ring: "ring-[#10b981]/20",
  },
  violet: {
    iconBg: "bg-[#8b5cf6]/10",
    iconText: "text-[#8b5cf6]",
    ring: "ring-[#8b5cf6]/20",
  },
  amber: {
    iconBg: "bg-[#f59e0b]/10",
    iconText: "text-[#f59e0b]",
    ring: "ring-[#f59e0b]/20",
  },
  rose: {
    iconBg: "bg-[#f43f5e]/10",
    iconText: "text-[#f43f5e]",
    ring: "ring-[#f43f5e]/20",
  },
};

export function StatCard({ label, value, icon, color, subtext, tooltip }: StatCardProps) {
  const c = colorConfig[color];

  return (
    <div className="glass group relative overflow-hidden rounded-2xl p-5 transition-all duration-300 hover:shadow-lg hover:shadow-black/5 hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            {label}
          </p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtext && (
            <p className="text-xs text-gray-400">{subtext}</p>
          )}
        </div>
        <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl ring-1", c.iconBg, c.ring)}>
          <span className={cn("text-lg", c.iconText)}>{icon}</span>
        </div>
      </div>
      {tooltip && (
        <div className="absolute inset-x-0 bottom-0 translate-y-full bg-gray-900/90 px-4 py-2 text-xs text-white opacity-0 transition-all group-hover:translate-y-0 group-hover:opacity-100">
          {tooltip}
        </div>
      )}
    </div>
  );
}
