"use client";

import { cn } from "@/lib/utils";

interface ConceptCardProps {
  title: string;
  icon: string;
  desc: string;
  color: "blue" | "emerald" | "violet" | "amber";
  details: string[];
}

const accents = {
  blue: "border-[#4f6ef7]/20 hover:border-[#4f6ef7]/40",
  emerald: "border-[#10b981]/20 hover:border-[#10b981]/40",
  violet: "border-[#8b5cf6]/20 hover:border-[#8b5cf6]/40",
  amber: "border-[#f59e0b]/20 hover:border-[#f59e0b]/40",
};

const iconBg = {
  blue: "bg-[#4f6ef7]/10 text-[#4f6ef7]",
  emerald: "bg-[#10b981]/10 text-[#10b981]",
  violet: "bg-[#8b5cf6]/10 text-[#8b5cf6]",
  amber: "bg-[#f59e0b]/10 text-[#f59e0b]",
};

export function ConceptCard({ title, icon, desc, color, details }: ConceptCardProps) {
  return (
    <div
      className={cn(
        "glass overflow-hidden rounded-2xl border p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5",
        accents[color]
      )}
    >
      <div className="flex items-start gap-4">
        <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-lg", iconBg[color])}>
          {icon}
        </div>
        <div className="space-y-2">
          <h3 className="text-sm font-bold text-gray-900">{title}</h3>
          <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
          <ul className="space-y-1">
            {details.map((d, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                <span className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-gray-300" />
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
