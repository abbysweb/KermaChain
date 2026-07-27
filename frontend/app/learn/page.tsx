"use client";

import { Header } from "@/components/layout/Header";
import { Explainer } from "@/components/educational/Explainer";
import { ConceptCard } from "@/components/educational/ConceptCard";
import { CodeBlock } from "@/components/educational/CodeBlock";
import { StepDiagram } from "@/components/educational/StepDiagram";

export default function LearnPage() {
  return (
    <div className="space-y-8">
      <Header
        title="Learn Blockchain"
        subtitle="Understand the fundamentals of decentralized technology from the ground up"
      />

      {/* Overview */}
      <div className="glass overflow-hidden rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#4f6ef7] to-[#8b5cf6] text-xl text-white shadow-lg shadow-blue-500/20">
            🎓
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Welcome to KermaChain</h2>
            <p className="mt-2 text-sm text-gray-600 leading-relaxed">
              KermaChain is a fully functional blockchain node implementing the <strong>Marabu protocol</strong>,
              designed as an educational tool. This page explains every concept you see in the dashboard.
              Click on any section to expand it and learn more.
            </p>
          </div>
        </div>
      </div>

      {/* Core Concepts Grid */}
      <h3 className="text-sm font-semibold text-gray-800">Core Concepts</h3>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ConceptCard
          title="Blockchain"
          icon="⛓"
          desc="A distributed ledger of blocks linked by cryptographic hashes."
          color="blue"
          details={[
            "Each block references the previous block's hash",
            "Tamper-evident: changing one block invalidates all following blocks",
            "Decentralized: every node keeps its own copy",
            "Immutability through cryptographic chaining",
          ]}
        />
        <ConceptCard
          title="UTXO Model"
          icon="💎"
          desc="Unspent Transaction Outputs — the accounting system used by Bitcoin and Marabu."
          color="emerald"
          details={[
            "Transactions consume existing UTXOs and create new ones",
            "No account balances — only a set of unspent outputs",
            "Prevents double-spending naturally",
            "Each output has a value and a public key (owner)",
          ]}
        />
        <ConceptCard
          title="Ed25519 Cryptography"
          icon="🔐"
          desc="Elliptic-curve signatures used for transaction authentication."
          color="violet"
          details={[
            "32-byte private key → 32-byte public key",
            "Deterministic signatures (same key + msg = same sig)",
            "Fast verification, compact signatures (64 bytes)",
            "Used in Bitcoin (Schnorr) and many modern chains",
          ]}
        />
        <ConceptCard
          title="Proof-of-Work"
          icon="⛏"
          desc="A consensus mechanism where miners solve computational puzzles."
          color="amber"
          details={[
            "Find a nonce where SHA-256(block) < target",
            "Target difficulty adjusts to maintain block interval",
            "50 TMC coinbase reward per block",
            "Secures the network against Sybil attacks",
          ]}
        />
      </div>

      {/* Deep Dives */}
      <h3 className="text-sm font-semibold text-gray-800">Deep Dives</h3>

      <Explainer title="1. How Transactions Work" icon="💸" defaultOpen>
        <StepDiagram
          steps={[
            { label: "Create", icon: "📝", desc: "Select UTXOs, define outputs", color: "emerald" },
            { label: "Sign", icon: "✍", desc: "Sign with Ed25519 private key", color: "blue" },
            { label: "Validate", icon: "✅", desc: "Verify sigs, check UTXO set", color: "violet" },
            { label: "Mempool", icon: "📋", desc: "Store in pending pool", color: "amber" },
            { label: "Confirm", icon: "📦", desc: "Include in next block", color: "rose" },
          ]}
        />
        <div className="mt-4 space-y-3 text-xs text-gray-600 leading-relaxed">
          <p>
            A transaction in the Marabu protocol is a JSON object with <strong>inputs</strong> and <strong>outputs</strong>.
            Each input references a previous output by <code>txid:index</code> (called an outpoint) and includes
            an Ed25519 signature proving ownership.
          </p>
          <CodeBlock title="transaction.json" language="JSON">{`{
  "type": "transaction",
  "inputs": [
    {
      "outpoint": { "txid": "abc123...", "index": 0 },
      "sig": "base64_ed25519_signature"
    }
  ],
  "outputs": [
    { "pubkey": "recipient_pubkey_b64", "value": 7000000000 },
    { "pubkey": "sender_pubkey_b64", "value": 2950000000 }
  ]
}`}</CodeBlock>
          <p>
            The first transaction in every block is always a <strong>coinbase transaction</strong> &mdash;
            it has no inputs and creates new currency (50 TMC reward + fees). This is how new coins enter circulation.
          </p>
        </div>
      </Explainer>

      <Explainer title="2. How Blocks Are Created" icon="📦">
        <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
          <p>
            A block bundles multiple transactions together with metadata. The <strong>block ID</strong> is
            computed by <strong>JCS canonicalizing</strong> the block (sorting keys alphabetically) and then
            computing <strong>SHA-256</strong> of the result.
          </p>
          <CodeBlock title="block.json" language="JSON">{`{
  "type": "block",
  "txids": [
    "coinbase_txid...",
    "tx1...",
    "tx2..."
  ],
  "previd": "previous_block_hash...",
  "created": 1700000000,
  "miner": "miner_public_key",
  "nonce": "000000abcdef...",
  "note": "KermaChain block #42"
}`}</CodeBlock>
          <p>
            The <strong>nonce</strong> is the variable miners change to find a valid hash. The target in Marabu
            is <code>0000abc000...00</code> &mdash; the hash must start with at least 3 zero bytes.
            This is equivalent to approximately 24 leading zero-bits of SHA-256.
          </p>
        </div>
      </Explainer>

      <Explainer title="3. P2P Network Protocol" icon="🌐">
        <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
          <p>
            KermaChain nodes communicate over raw <strong>TCP sockets</strong>. Every message starts with a
            magic byte <code>0x4d</code> (ASCII &lsquo;M&rsquo; for Marabu), followed by a message type, and a JSON payload.
          </p>
          <CodeBlock title="protocol messages" language="JSON">{`// Handshake
{"type": "hello", "version": "2", "agent": "KermaChain/1.0"}

// Object exchange
{"type": "getobject", "objectid": "block_hash..."}
{"type": "object", "object": { block/tx data... }}

// Peer discovery
{"type": "getpeers"}
{"type": "peers", "peers": ["1.2.3.4:18018", ...]}

// Chain synchronization
{"type": "getchaintip"}
{"type": "chaintip", "blockid": "tip_hash...", "height": 42}`}</CodeBlock>
          <p>
            When a node starts, it connects to <strong>bootstrap peers</strong>, exchanges peer lists,
            and requests any objects it doesn&apos;t have. The <strong>longest-chain rule</strong> ensures
            all nodes converge on the same blockchain history.
          </p>
        </div>
      </Explainer>

      <Explainer title="4. Blockchain Validation Rules" icon="✅">
        <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
          <p>Every node must independently verify all data. Here are the key rules:</p>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="rounded-xl bg-white/50 p-3">
              <p className="mb-1 font-semibold text-gray-800">Block Validation</p>
              <ul className="space-y-1">
                <li>• Block ID matches SHA-256 of contents</li>
                <li>• Hash is below the difficulty target</li>
                <li>• Timestamp is within 2 hours of local time</li>
                <li>• Coinbase exists as first transaction</li>
                <li>• Block reward is exactly 50 TMC</li>
              </ul>
            </div>
            <div className="rounded-xl bg-white/50 p-3">
              <p className="mb-1 font-semibold text-gray-800">Transaction Validation</p>
              <ul className="space-y-1">
                <li>• All inputs reference valid UTXOs</li>
                <li>• No double-spending (each input used once)</li>
                <li>• Input sum equals output sum</li>
                <li>• Ed25519 signatures verify against pubkeys</li>
                <li>• Coinbase tx has no inputs</li>
              </ul>
            </div>
          </div>
        </div>
      </Explainer>

      <Explainer title="5. JCS — JSON Canonicalization" icon="🔤">
        <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
          <p>
            To compute deterministic hashes, JSON must be <strong>canonicalized</strong>. KermaChain uses
            <strong> JCS (JSON Canonicalization Scheme, RFC 8785)</strong>:
          </p>
          <ul className="space-y-1.5">
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#4f6ef7]" />
              <span>Keys are sorted alphabetically</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#10b981]" />
              <span>No whitespace or line breaks</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#8b5cf6]" />
              <span>Unicode is NFC-normalized</span>
            </li>
          </ul>
          <CodeBlock title="before vs after" language="JSON">{`// Before (non-canonical)
{"b": 2, "a": {"z": 1, "a": 2}}

// After JCS canonicalization
{"a":{"a":2,"z":1},"b":2}`}</CodeBlock>
          <p>
            This ensures that the same block always produces the same hash, regardless of how it was serialized.
          </p>
        </div>
      </Explainer>

      {/* Technical Stack */}
      <h3 className="text-sm font-semibold text-gray-800">Technology Stack</h3>
      <div className="glass rounded-2xl p-6">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-sm">🐍</div>
            <p className="text-xs font-semibold text-gray-800">Python 3.11+</p>
            <p className="text-[10px] text-gray-400">Backend node</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-sm">⚡</div>
            <p className="text-xs font-semibold text-gray-800">asyncio</p>
            <p className="text-[10px] text-gray-400">Async networking</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-sm">🗄</div>
            <p className="text-xs font-semibold text-gray-800">SQLite</p>
            <p className="text-[10px] text-gray-400">Local storage</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-sm">⚛</div>
            <p className="text-xs font-semibold text-gray-800">Next.js 14</p>
            <p className="text-[10px] text-gray-400">Dashboard UI</p>
          </div>
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
