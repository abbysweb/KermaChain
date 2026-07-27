"use client";

import { cn } from "@/lib/utils";

interface StepDiagramProps {
  steps: {
    label: string;
    icon: string;
    desc: string;
    color: "blue" | "emerald" | "violet" | "amber" | "rose";
  }[];
}

const colors = {
  blue: "from-[#4f6ef7] to-[#6366f1] border-[#4f6ef7]/20",
  emerald: "from-[#10b981] to-[#059669] border-[#10b981]/20",
  violet: "from-[#8b5cf6] to-[#7c3aed] border-[#8b5cf6]/20",
  amber: "from-[#f59e0b] to-[#d97706] border-[#f59e0b]/20",
  rose: "from-[#f43f5e] to-[#e11d48] border-[#f43f5e]/20",
};

export function StepDiagram({ steps }: StepDiagramProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="glass-subtle flex flex-col items-center gap-2 rounded-2xl p-4 min-w-[120px] text-center">
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-white text-lg shadow-lg",
                colors[step.color]
              )}
            >
              {step.icon}
            </div>
            <p className="text-xs font-semibold text-gray-800">{step.label}</p>
            <p className="text-[10px] text-gray-400 leading-snug">{step.desc}</p>
          </div>
          {i < steps.length - 1 && (
            <div className="text-gray-300 text-lg">→</div>
          )}
        </div>
      ))}
    </div>
  );
}
