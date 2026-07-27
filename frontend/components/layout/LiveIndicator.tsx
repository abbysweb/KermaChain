"use client";

interface LiveIndicatorProps {
  connected?: boolean;
}

export function LiveIndicator({ connected = true }: LiveIndicatorProps) {
  return (
    <div className="glass-subtle flex items-center gap-2 rounded-full px-3 py-1.5">
      <span
        className={`h-2 w-2 rounded-full transition-colors ${
          connected ? "bg-emerald-500 animate-pulse" : "bg-gray-300"
        }`}
      />
      <span className="text-xs font-medium text-gray-600">
        {connected ? "Live" : "Offline"}
      </span>
    </div>
  );
}
