"use client";

import { LiveIndicator } from "./LiveIndicator";

interface HeaderProps {
  title: string;
  subtitle: string;
  connected?: boolean;
}

export function Header({ title, subtitle, connected = true }: HeaderProps) {
  return (
    <div className="mb-8 flex items-start justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        <LiveIndicator connected={connected} />
      </div>
    </div>
  );
}
