"use client";

import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { MempoolTable } from "@/components/mempool/MempoolTable";
import { StatCard } from "@/components/stats/StatCard";
import { Explainer } from "@/components/educational/Explainer";
import { CodeBlock } from "@/components/educational/CodeBlock";
import { StepDiagram } from "@/components/educational/StepDiagram";
import type { MempoolEntry } from "@/lib/types";

const MOCK_MEMPOOL: MempoolEntry[] = [
  { txid: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6", inputsCount: 2, outputsCount: 3, totalValue: 15000000000 },
  { txid: "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7", inputsCount: 1, outputsCount: 2, totalValue: 8000000000 },
  { txid: "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8", inputsCount: 4, outputsCount: 1, totalValue: 50000000000 },
  { txid: "d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9", inputsCount: 3, outputsCount: 4, totalValue: 22000000000 },
  { txid: "e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0", inputsCount: 1, outputsCount: 1, totalValue: 5000000000 },
];

export default function MempoolPage() {
  const [mempool] = useState<MempoolEntry[]>(MOCK_MEMPOOL);

  const totalValue = mempool.reduce((sum, e) => sum + e.totalValue, 0);
  const totalInputs = mempool.reduce((sum, e) => sum + e.inputsCount, 0);
  const totalOutputs = mempool.reduce((sum, e) => sum + e.outputsCount, 0);

  return (
    <div className="space-y-8">
      <Header
        title="Mempool"
        subtitle="Pending transactions awaiting inclusion in the next block"
      />

      <Explainer title="What is a Mempool?" icon="📋" defaultOpen>
        <StepDiagram
          steps={[
            { label: "Sign Tx", icon: "✍", desc: "Create & sign transaction", color: "emerald" },
            { label: "Broadcast", icon: "📡", desc: "Send to connected peers", color: "blue" },
            { label: "Mempool", icon: "📋", desc: "Node stores it temporarily", color: "violet" },
            { label: "Block", icon: "📦", desc: "Miner picks it from pool", color: "amber" },
          ]}
        />
        <div className="mt-4 rounded-xl bg-white/50 p-4 text-xs text-gray-600 leading-relaxed">
          The <strong>mempool</strong> (memory pool) is where valid transactions wait before being confirmed
          in a block. When a transaction arrives, the node validates it:
          all referenced inputs must be unspent (UTXO model), signatures must verify, and total inputs
          must equal total outputs (no money created out of thin air). If valid, the transaction enters
          the mempool and is broadcast to peers. Miners select transactions from the mempool to include
          in their next block.
        </div>
      </Explainer>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Pending TXs" value={mempool.length} icon="📋" color="emerald" subtext="Awaiting confirmation" />
        <StatCard label="Total Inputs" value={totalInputs} icon="➡" color="blue" subtext="UTXOs being consumed" />
        <StatCard label="Total Value" value={`${(totalValue / 1e9).toFixed(1)}B TMC`} icon="💰" color="amber" subtext="Value in transit" />
      </div>

      <MempoolTable entries={mempool} />

      <Explainer title="How does a transaction work?" icon="💸">
        <CodeBlock title="transaction.json" language="JSON">{`{
  "inputs": [
    {
      "outpoint": {
        "txid": "prev_tx_hash...",
        "index": 0
      },
      "sig": "Ed25519_signature..."
    }
  ],
  "outputs": [
    {
      "pubkey": "recipient_public_key",
      "value": 5000000000
    }
  ]
}`}</CodeBlock>
        <p className="mt-3">
          Each input references an output from a previous transaction (the <strong>UTXO</strong>).
          The signature proves the sender owns the private key. Each output defines a new UTXO
          with a public key and value. The difference between inputs and outputs is the
          transaction fee (goes to the miner).
        </p>
      </Explainer>
    </div>
  );
}
