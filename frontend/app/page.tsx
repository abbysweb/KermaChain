"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { StatCard } from "@/components/stats/StatCard";
import { BlockCard } from "@/components/blockchain/BlockCard";
import { HeightChart } from "@/components/blockchain/HeightChart";
import { MempoolTable } from "@/components/mempool/MempoolTable";
import { PeerGrid } from "@/components/network/PeerGrid";
import { Explainer } from "@/components/educational/Explainer";
import { StepDiagram } from "@/components/educational/StepDiagram";
import { useWebSocket } from "@/lib/ws";
import type { Stats, Block, MempoolEntry, Peer } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

function formatUptime(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [mempool, setMempool] = useState<MempoolEntry[]>([]);
  const [peers, setPeers] = useState<Peer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [statsRes, blocksRes, mempoolRes, peersRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats`).then(r => r.json()),
        fetch(`${API_BASE}/api/chain?limit=10`).then(r => r.json()),
        fetch(`${API_BASE}/api/mempool`).then(r => r.json()),
        fetch(`${API_BASE}/api/peers`).then(r => r.json()),
      ]);
      setStats(statsRes);
      setBlocks(blocksRes);
      setMempool(mempoolRes);
      setPeers(peersRes);
      setError(null);
    } catch (e) {
      setError("Failed to fetch data from API");
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const onWsMessage = useCallback((msg: { type: string; data: unknown }) => {
    if (msg.type === "stats" || msg.type === "chain" || msg.type === "mempool" || msg.type === "peers") {
      fetchAll();
    }
  }, [fetchAll]);

  const { connected } = useWebSocket(onWsMessage);

  if (loading) {
    return (
      <div className="space-y-8">
        <Header title="Dashboard" subtitle="Loading KermaChain node data..." connected={connected} />
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4f6ef7]"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="space-y-8">
        <Header title="Dashboard" subtitle="Error loading data" connected={connected} />
        <div className="glass rounded-2xl p-8 text-center text-red-500">
          {error || "Failed to load data"}
          <button onClick={fetchAll} className="mt-4 px-4 py-2 bg-[#4f6ef7] text-white rounded-lg hover:bg-[#4f6ef7]/90">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <Header
        title="Dashboard"
        subtitle="Real-time overview of the KermaChain Marabu blockchain node"
        connected={connected}
      />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Chain Height"
          value={stats.height}
          icon="⛓"
          color="blue"
          subtext={`Tip: ${stats.tipId.slice(0, 12)}...`}
          tooltip="The current number of blocks in the longest chain"
        />
        <StatCard
          label="Peers"
          value={stats.peerCount}
          icon="🌐"
          color="violet"
          subtext="Connected nodes"
          tooltip="Number of active P2P connections to other Marabu nodes"
        />
        <StatCard
          label="Mempool"
          value={stats.mempoolSize}
          icon="📋"
          color="emerald"
          subtext="Pending transactions"
          tooltip="Transactions waiting to be included in the next block"
        />
        <StatCard
          label="Uptime"
          value={formatUptime(stats.uptime)}
          icon="⏱"
          color="amber"
          subtext={`${stats.blocksTotal} blocks total`}
          tooltip="How long this node has been running"
        />
      </div>

      {/* How it works */}
      <Explainer title="How does this blockchain work?" icon="💡" defaultOpen>
        <StepDiagram
          steps={[
            { label: "Transaction", icon: "💸", desc: "User signs a tx with Ed25519", color: "emerald" },
            { label: "Mempool", icon: "📋", desc: "Tx enters the pending pool", color: "violet" },
            { label: "Block", icon: "📦", desc: "Miner bundles txs into a block", color: "blue" },
            { label: "PoW", icon: "⛏", desc: "Find nonce below target hash", color: "amber" },
            { label: "Broadcast", icon: "📡", desc: "Share block to all peers", color: "rose" },
          ]}
        />
        <div className="mt-4 rounded-xl bg-white/50 p-4 text-xs text-gray-600 leading-relaxed">
          <strong>KermaChain</strong> implements the <strong>Marabu protocol</strong>, a simplified academic blockchain.
          Each block contains a list of transactions, a reference to the previous block (creating the chain),
          a Proof-of-Work nonce, and a coinbase reward. Nodes communicate over TCP, exchanging objects
          (blocks and transactions) using a custom message protocol. The UTXO model tracks unspent outputs
          to prevent double-spending.
        </div>
      </Explainer>

      {/* Charts + Recent blocks */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <HeightChart
          data={blocks.map((b) => ({
            height: b.height,
            timestamp: b.timestamp,
            txCount: b.txCount,
          }))}
        />
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-800">Recent Blocks</h3>
          {blocks.map((b) => (
            <BlockCard key={b.id} block={b} compact />
          ))}
        </div>
      </div>

      {/* Mempool + Network */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-800">Mempool</h3>
          <MempoolTable entries={mempool} />
        </div>
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-800">Connected Peers</h3>
          <PeerGrid peers={peers} />
        </div>
      </div>

      {/* Author */}
      <div className="glass rounded-2xl p-6">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#4f6ef7] to-[#8b5cf6] text-sm font-bold text-white shadow-lg shadow-blue-500/20">
              AM
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900">Abdullah Al Mamun</p>
              <p className="text-xs text-gray-500">
                M.Sc. & B.Sc. Software Engineering &mdash; TU Wien & Daffodil International University
              </p>
            </div>
          </div>
          <div className="flex gap-4 text-xs text-gray-400">
            <a href="https://github.com/abbysweb" target="_blank" rel="noopener noreferrer" className="hover:text-[#4f6ef7] transition-colors font-medium">GitHub</a>
            <a href="https://orcid.org/0009-0006-7473-0024" target="_blank" rel="noopener noreferrer" className="hover:text-[#4f6ef7] transition-colors font-medium">ORCID</a>
            <a href="mailto:mamun.swe.de@gmail.com" className="hover:text-[#4f6ef7] transition-colors font-medium">Email</a>
          </div>
        </div>
      </div>
    </div>
  );
}