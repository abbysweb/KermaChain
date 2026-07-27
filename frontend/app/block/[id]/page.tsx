"use client";

import { use } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Explainer } from "@/components/educational/Explainer";
import type { Block } from "@/lib/types";

const MOCK_BLOCK: Block = {
  id: "00002fa163c7dab0991544424b9fd302bb1782b185e5a3bbdf12afb758e57dee",
  height: 42,
  timestamp: Math.floor(Date.now() / 1000) - 120,
  txCount: 5,
  miner: "miner_a1b2c3d4e5f6",
  nonce: "000000abcdef1234",
  target: "0000abc000000000000000000000000000000000000000000000000000000000",
  previd: "00001b2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
  txids: [
    "tx_coinbase_a1b2c3d4",
    "tx_transfer_e5f6g7h8",
    "tx_transfer_i9j0k1l2",
    "tx_transfer_m3n4o5p6",
    "tx_transfer_q7r8s9t0",
  ],
};

export default function BlockDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const block = MOCK_BLOCK;

  return (
    <div className="space-y-8">
      <Link
        href="/chain"
        className="inline-flex items-center gap-1 text-xs font-medium text-gray-400 hover:text-[#4f6ef7] transition-colors"
      >
        ← Back to Blockchain
      </Link>

      <Header
        title={`Block #${block.height}`}
        subtitle={`Mining this block: finding a nonce that produces a hash below the target`}
      />

      <div className="glass overflow-hidden rounded-2xl">
        <div className="border-b border-gray-100 px-6 py-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Block Details</h3>
        </div>
        <div className="divide-y divide-gray-50 p-6 space-y-4">
          <DetailRow label="Block ID" value={block.id} mono />
          <DetailRow label="Height" value={String(block.height)} />
          <DetailRow label="Timestamp" value={new Date(block.timestamp * 1000).toLocaleString()} />
          <DetailRow label="Miner" value={block.miner} mono />
          <DetailRow label="Nonce" value={block.nonce} mono highlight />
          <DetailRow label="Target" value={block.target} mono />
          <DetailRow label="Previous Block" value={block.previd || "Genesis (no parent)"} mono />
          <DetailRow label="Transactions" value={`${block.txCount} transaction(s)`} />
        </div>
      </div>

      <Explainer title="How does Proof-of-Work mining work?" icon="⛏" defaultOpen>
        <div className="rounded-xl bg-white/50 p-4 text-xs text-gray-600 leading-relaxed">
          <strong>Proof-of-Work</strong> is a consensus mechanism where miners compete to find a special
          number called a <strong>nonce</strong>. They repeatedly hash the block contents (including the nonce)
          using <strong>SHA-256</strong> until the resulting hash is numerically smaller than the <strong>target</strong>.
          The target starts with many zeros &mdash; the more zeros, the harder it is to find.
          The first miner to find a valid nonce broadcasts the block and receives a <strong>50 TMC coinbase reward</strong>.
          This process secures the network because an attacker would need more computational power
          than all honest miners combined.
        </div>
      </Explainer>

      {block.txids.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-800">
            Transactions ({block.txCount})
          </h3>
          <div className="glass overflow-hidden rounded-2xl divide-y divide-gray-50">
            {block.txids.map((txid, i) => (
              <div key={txid} className="flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-white/40">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gray-100 text-[10px] font-bold text-gray-400">
                  {i === 0 ? "💎" : i}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-xs text-[#10b981] truncate">{txid}</p>
                  <p className="text-[10px] text-gray-400">
                    {i === 0 ? "Coinbase (miner reward)" : `Transfer #${i}`}
                  </p>
                </div>
                <div className="text-right">
                  <span className="rounded-full bg-[#f59e0b]/10 px-2 py-0.5 text-[10px] font-semibold text-[#f59e0b]">
                    {i === 0 ? "50 TMC" : `${(Math.random() * 10).toFixed(2)} TMC`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono = false,
  highlight = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-4">
      <span className="text-xs font-medium text-gray-400 w-32 shrink-0">{label}</span>
      <span
        className={`text-sm break-all ${
          mono ? "font-mono text-gray-700" : "text-gray-900"
        } ${highlight ? "text-[#f43f5e] font-semibold" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
