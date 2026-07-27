"use client";

import type { Peer } from "@/lib/types";

function timeAgo(ts?: number): string {
  if (!ts) return "N/A";
  const s = Math.floor(Date.now() / 1000 - ts);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

interface PeerGridProps {
  peers: Peer[];
}

export function PeerGrid({ peers }: PeerGridProps) {
  if (peers.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center">
        <p className="text-3xl mb-2">📡</p>
        <p className="text-sm font-medium text-gray-500">No peers connected</p>
        <p className="text-xs text-gray-400 mt-1">Waiting for network discovery</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {peers.map((peer) => (
        <div
          key={`${peer.host}:${peer.port}`}
          className="glass group overflow-hidden rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/10 hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div
                  className={`h-3 w-3 rounded-full ${
                    peer.connected ? "bg-[#10b981]" : "bg-gray-300"
                  }`}
                />
                {peer.connected && (
                  <div className="absolute inset-0 h-3 w-3 animate-ping rounded-full bg-[#10b981] opacity-40" />
                )}
              </div>
              <div>
                <p className="text-sm font-semibold font-mono text-gray-800">
                  {peer.host}
                </p>
                <p className="text-xs text-gray-400">:{peer.port}</p>
              </div>
            </div>
            <div className="text-right">
              <span
                className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                  peer.connected
                    ? "bg-[#10b981]/10 text-[#10b981]"
                    : "bg-gray-100 text-gray-400"
                }`}
              >
                {peer.connected ? "Online" : "Offline"}
              </span>
              <p className="mt-1 text-[10px] text-gray-400">
                {timeAgo(peer.connectedSince)}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
