"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface ExplainerProps {
  title: string;
  icon: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function Explainer({ title, icon, children, defaultOpen = false }: ExplainerProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="glass overflow-hidden rounded-2xl transition-all duration-300">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-white/40"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{icon}</span>
          <span className="text-sm font-semibold text-gray-800">{title}</span>
        </div>
        <span
          className={cn(
            "text-gray-400 transition-transform duration-200",
            open && "rotate-180"
          )}
        >
          ▼
        </span>
      </button>
      {open && (
        <div className="border-t border-gray-100 px-4 py-4 text-sm text-gray-600 leading-relaxed animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}
