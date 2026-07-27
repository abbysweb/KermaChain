const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

import type { Stats, Block, Transaction, Peer, MempoolEntry } from "./types";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getStats: () => fetchApi<Stats>("/api/stats"),
  getChain: () => fetchApi<Block[]>("/api/chain"),
  getBlock: (id: string) => fetchApi<Block>(`/api/blocks/${id}`),
  getMempool: () => fetchApi<MempoolEntry[]>("/api/mempool"),
  getPeers: () => fetchApi<Peer[]>("/api/peers"),
  getHealth: () => fetchApi<{ status: string; version: string }>("/api/health"),
};
