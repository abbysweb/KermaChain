"use client";

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { BlockCard } from "@/components/blockchain/BlockCard";
import { HeightChart } from "@/components/blockchain/HeightChart";
import { Explainer } from "@/components/educational/Explainer";
import { CodeBlock } from "@/components/educational/CodeBlock";
import type { Block } from "@/lib/types";

const MOCK_CHAIN: Block[] = Array.from({ length: 20 }, (_, i) => ({
  id: `block_${42 - i}_${Math.random().toString(36).slice(2, 10)}`,
  height: 42 - i,
  timestamp: Math.floor(Date.now() / 1000) - (42 - i) * 600,
  txCount: Math.floor(Math.random() * 8) + 1,
  miner: `miner${Math.random().toString(36).slice(2, 8)}`,
  nonce: `000000${Math.random().toString(16).slice(2, 14)}`,
  target: "0000abc00000",
  previd: i === 19 ? null : `block_${41 - i}_${Math.random().toString(36).slice(2, 10)}`,
  txids: [],
}));

export default function ChainPage() {
  const [chain] = useState<Block[]>(MOCK_CHAIN);
  const totalTx = chain.reduce((sum, b) => sum + b.txCount, 0);

  return (
    <div className="space-y-8">
      <Header
        title="Blockchain Explorer"
        subtitle={`${chain.length} blocks mined · ${totalTx} total transactions`}
      />

      <Explainer title="What is a Blockchain?" icon="⛓" defaultOpen>
        <p className="mb-3">
          A blockchain is a <strong>linked list of blocks</strong>, where each block contains:
        </p>
        <ul className="mb-3 space-y-1.5">
          <li className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#4f6ef7]" />
            <span><strong>Block ID</strong> &mdash; a SHA-256 hash of the block contents</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#10b981]" />
            <span><strong>Previd</strong> &mdash; hash of the previous block, forming the chain</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#8b5cf6]" />
            <span><strong>Transactions</strong> &mdash; list of txids included in this block</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f59e0b]" />
            <span><strong>Nonce</strong> &mdash; a number that makes the hash satisfy the difficulty target</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f43f5e]" />
            <span><strong>Coinbase</strong> &mdash; first transaction, rewards the miner with 50 TMC</span>
          </li>
        </ul>
        <CodeBlock title="block.json" language="JSON">{`{
  "id": "00002fa163c...",
  "previd": "00001b2e3f4...",
  "txids": ["abc123...", "def456..."],
  "nonce": "000000abcdef",
  "timestamp": 1700000000,
  "creator": "miner_pubkey"
}`}</CodeBlock>
      </Explainer>

      <HeightChart
        data={chain.map((b) => ({
          height: b.height,
          timestamp: b.timestamp,
          txCount: b.txCount,
        }))}
      />

      <div className="space-y-3">
        {chain.map((block) => (
          <BlockCard key={block.id} block={block} />
        ))}
      </div>
    </div>
  );
}
