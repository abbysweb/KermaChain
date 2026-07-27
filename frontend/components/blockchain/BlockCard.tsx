"use client";

import Link from "next/link";
import type { Block } from "@/lib/types";

function timeAgo(ts: number): string {
  const s = Math.floor(Date.now() / 1000 - ts);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

function truncate(id: string, n = 8): string {
  return id.length > n * 2 ? `${id.slice(0, n)}...${id.slice(-n)}` : id;
}

interface BlockCardProps {
  block: Block;
  compact?: boolean;
}

export function BlockCard({ block, compact = false }: BlockCardProps) {
  return (
    <Link href={`/block/${block.id}`}>
      <div className="glass group cursor-pointer overflow-hidden rounded-2xl p-4 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-0.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#4f6ef7]/10 ring-1 ring-[#4f6ef7]/20 text-sm font-bold text-[#4f6ef7] transition-colors group-hover:bg-[#4f6ef7] group-hover:text-white">
              #{block.height}
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">
                Block {block.height}
              </p>
              <p className="text-xs font-mono text-gray-400">
                {truncate(block.id)}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-medium text-gray-600">
              {block.txCount} tx{block.txCount !== 1 ? "s" : ""}
            </p>
            <p className="text-xs text-gray-400">{timeAgo(block.timestamp)}</p>
          </div>
        </div>
        {!compact && (
          <div className="mt-3 flex gap-6 border-t border-gray-100 pt-3">
            <div>
              <p className="text-[10px] font-medium uppercase text-gray-400">Miner</p>
              <p className="text-xs font-mono text-gray-600">
                {truncate(block.miner, 6)}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-medium uppercase text-gray-400">Nonce</p>
              <p className="text-xs font-mono text-gray-600">
                {truncate(block.nonce, 6)}
              </p>
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}
