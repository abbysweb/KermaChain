"use client";

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { PeerGrid } from "@/components/network/PeerGrid";
import { StatCard } from "@/components/stats/StatCard";
import { Explainer } from "@/components/educational/Explainer";
import { CodeBlock } from "@/components/educational/CodeBlock";
import { StepDiagram } from "@/components/educational/StepDiagram";
import type { Peer } from "@/lib/types";

const MOCK_PEERS: Peer[] = [
  { host: "128.130.122.73", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 7200 },
  { host: "192.168.1.42", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 3600 },
  { host: "10.0.0.15", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 1800 },
  { host: "172.16.0.88", port: 18018, connected: false },
  { host: "203.0.113.50", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 900 },
  { host: "198.51.100.22", port: 18018, connected: true },
  { host: "100.64.0.1", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 450 },
  { host: "10.10.10.10", port: 18018, connected: true, connectedSince: Math.floor(Date.now() / 1000) - 300 },
];

export default function PeersPage() {
  const [peers] = useState<Peer[]>(MOCK_PEERS);
  const connectedCount = peers.filter((p) => p.connected).length;

  return (
    <div className="space-y-8">
      <Header
        title="P2P Network"
        subtitle="Connected nodes in the Marabu blockchain network"
      />

      <Explainer title="How does P2P networking work?" icon="🌐" defaultOpen>
        <StepDiagram
          steps={[
            { label: "Connect", icon: "🔌", desc: "TCP to bootstrap peer", color: "blue" },
            { label: "Handshake", icon: "🤝", desc: "Exchange hello messages", color: "emerald" },
            { label: "Discover", icon: "🔍", desc: "Share peer lists", color: "violet" },
            { label: "Sync", icon: "🔄", desc: "Exchange blocks & txs", color: "amber" },
          ]}
        />
        <div className="mt-4 rounded-xl bg-white/50 p-4 text-xs text-gray-600 leading-relaxed">
          KermaChain uses a <strong>gossip protocol</strong> over TCP. Each node connects to
          bootstrap peers, exchanges peer lists (like a social network), and synchronizes
          the blockchain by requesting unknown objects. Messages use a custom binary format
          with a magic byte (<code>0x4d</code> for &ldquo;Marabu&rdquo;), message type, and JSON payload.
          The node runs a <strong>longest-chain rule</strong>: if a fork is detected, it follows the chain
          with the most cumulative Proof-of-Work.
        </div>
      </Explainer>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total Peers" value={peers.length} icon="🌐" color="violet" subtext="Known nodes" />
        <StatCard label="Connected" value={connectedCount} icon="✅" color="emerald" subtext="Active connections" />
        <StatCard label="Disconnected" value={peers.length - connectedCount} icon="⚠" color="amber" subtext="Need reconnection" />
      </div>

      <PeerGrid peers={peers} />

      <Explainer title="Marabu Protocol Messages" icon="📨">
        <CodeBlock title="message format" language="Binary">{`[0x4d] [type_length] [payload_json]
  ^         ^              ^
magic    msg type       JSON body`}</CodeBlock>
        <div className="mt-3 space-y-2">
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-[#4f6ef7]/10 px-2 py-0.5 text-[10px] font-semibold text-[#4f6ef7]">hello</span>
            <span className="text-xs text-gray-600">Handshake: exchange version & agent info</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-[#10b981]/10 px-2 py-0.5 text-[10px] font-semibold text-[#10b981]">getpeers</span>
            <span className="text-xs text-gray-600">Request known peer addresses</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-[#8b5cf6]/10 px-2 py-0.5 text-[10px] font-semibold text-[#8b5cf6]">getobject</span>
            <span className="text-xs text-gray-600">Request a block or transaction by ID</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-[#f59e0b]/10 px-2 py-0.5 text-[10px] font-semibold text-[#f59e0b]">ihaveobject</span>
            <span className="text-xs text-gray-600">Announce a new block/transaction</span>
          </div>
          <div className="flex items-start gap-3">
            <span className="rounded-full bg-[#f43f5e]/10 px-2 py-0.5 text-[10px] font-semibold text-[#f43f5e]">getchaintip</span>
            <span className="text-xs text-gray-600">Request the current chain head</span>
          </div>
        </div>
      </Explainer>
    </div>
  );
}
