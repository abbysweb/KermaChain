# KermaChain

A Python P2P blockchain node implementing the Marabu protocol, built as a consolidated project from a series of cryptocurrency assignments. Features a modern Next.js + TypeScript dashboard for real-time monitoring.

---

## Author
**Abdullah Al Mamun**  
M.Sc. & B.Sc. in Software Engineering  
TU Wien (Vienna, Austria) & Daffodil International University  
Email: mamun.swe.de@gmail.com  
GitHub: [github.com/abbysweb](https://github.com/abbysweb)  
ORCID: [0009-0006-7473-0024](https://orcid.org/0009-0006-7473-0024)

---

## Architecture Overview

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Next.js + TypeScript)"]
        Dashboard["Dashboard Page<br/>- Stat Cards (height, peers, mempool, uptime)<br/>- Height Chart + Recent Blocks<br/>- Mempool Table + Peer Grid<br/>- Educational Explainer"]
        API["API Client (lib/api.ts)"]
        WS["WebSocket Hook (lib/ws.ts)"]
        Types["TypeScript Types (lib/types.ts)"]
    end

    subgraph Backend["Backend API (aiohttp + Python)"]
        REST["REST API Server<br/>:3001<br/>- /api/health<br/>- /api/stats<br/>- /api/chain<br/>- /api/blocks/{id}<br/>- /api/mempool<br/>- /api/peers<br/>- /api/objects/{id}"]
        WSS["WebSocket Server<br/>:3001/ws/live<br/>- new_block<br/>- new_tx<br/>- reorg<br/>- peer_update"]
        Node["Node Core<br/>- Blockchain (tip, height)<br/>- Mempool (tx pool, UTXO)<br/>- Validator (pending objects)"]
    end

    subgraph P2P["P2P Network Layer (asyncio)"]
        Proto["Protocol Handler<br/>- Message validation<br/>- hello, getpeers, getchaintip<br/>- getmempool, getobject, ihaveobject"]
        PeerMgr["Peer Manager<br/>- Peer discovery<br/>- Connection pooling<br/>- peers.json persistence"]
        Conns["Active Connections<br/>- TCP readers/writers<br/>- Message queues"]
    end

    subgraph Storage["Storage (SQLite)"]
        DB["Database<br/>- objects (oid, obj)<br/>- utxo (blockid, utxoset)<br/>- heights (blockid, height)"]
    end

    subgraph Core["Core Blockchain Logic"]
        Block["Block Validation<br/>- PoW (BLAKE2s)<br/>- Timestamp ordering<br/>- Coinbase reward"]
        TX["Transaction Validation<br/>- Ed25519 signatures<br/>- UTXO conservation<br/>- Double-spend prevention"]
        UTXO["UTXO Model<br/>- Unspent outputs tracking<br/>- Reorg rebasing"]
    end

    Dashboard --> API
    Dashboard --> WS
    API --> Types
    WS --> Types
    API <--> REST
    WS <--> WSS
    REST <--> Node
    WSS <--> Node
    Node <--> Proto
    Proto <--> PeerMgr
    Proto <--> Conns
    Node <--> DB
    Block <--> Node
    TX <--> Node
    UTXO <--> Node
```

---

## System Sequence Diagram

The following sequence diagram shows the complete flow from node startup through P2P handshake, block propagation, chain reorganization, and real-time dashboard updates.

```mermaid
sequenceDiagram
    autonumber
    participant User as User/Operator
    participant Frontend as Frontend Dashboard (Next.js)
    participant API as Backend REST API (aiohttp :3001)
    participant WS as WebSocket Server (:3001/ws/live)
    participant Node as Node Core (Python)
    participant P2P as P2P Network Layer
    participant Peer1 as Remote Peer A
    participant Peer2 as Remote Peer B
    participant DB as SQLite Database

    Note over User,DB: === NODE STARTUP ===
    User->>Frontend: Open http://localhost:3000
    Frontend->>API: GET /api/health
    API-->>Frontend: {status: "ok", version: "1.0.0"}
    
    User->>Node: python -m kerma.main
    Node->>DB: create_tables() + ensure_genesis()
    DB-->>Node: Genesis block stored (height=0)
    Node->>Node: Initialize blockchain tip
    Node->>P2P: Start TCP server :18018
    Node->>P2P: Bootstrap to seed peers
    P2P->>Peer1: TCP connect :18018
    P2P->>Peer1: hello {version, agent}
    P2P->>Peer1: getpeers
    Peer1-->>P2P: peers [list of 30]
    P2P->>Peer1: getchaintip
    Peer1-->>P2P: chaintip {blockid}
    P2P->>Peer1: getmempool
    Peer1-->>P2P: mempool {txids}
    P2P-->>Node: Peer connections established
    
    Note over User,DB: === DASHBOARD POLLING (every 5s) ===
    Frontend->>API: GET /api/stats
    API->>Node: get_stats()
    Node->>DB: SELECT MAX(height) FROM heights
    DB-->>Node: tip_id, tip_height
    Node-->>API: {height, tipId, peerCount, mempoolSize, uptime}
    API-->>Frontend: JSON response
    
    Frontend->>API: GET /api/chain?limit=10
    API->>Node: blockchain.get_chain(10)
    Node->>DB: SELECT objects + heights (walk previd)
    DB-->>Node: Block data
    Node-->>API: Block array
    API-->>Frontend: Block list with txCount, miner, etc.
    
    Frontend->>API: GET /api/mempool
    API->>Node: mempool.get_entries()
    Node-->>API: TX entries (txid, inputs, outputs, value)
    API-->>Frontend: Mempool table data
    
    Frontend->>API: GET /api/peers
    API->>Node: peers.get_all() + connections
    Node-->>API: Peer list with connected status
    API-->>Frontend: Peer grid data
    
    Frontend->>WS: Connect WebSocket
    WS-->>Frontend: WebSocket open
    
    Note over User,DB: === BLOCK PROPAGATION (mined locally or received) ===
    Peer1->>P2P: ihaveobject {blockid}
    P2P->>DB: SELECT EXISTS(oid)
    alt Block unknown
        P2P->>Peer1: getobject {blockid}
        Peer1-->>P2P: object {block_dict}
        P2P->>Node: _handle_object_msg(block)
        Node->>Node: validate_block() → verify_block_tail()
        Node->>DB: Store block + UTXO + height
        alt New tip (height > current)
            Node->>Node: Update tip, reorg mempool
            Node->>P2P: Broadcast chaintip
            P2P->>Peer1: chaintip {new_blockid}
            P2P->>Peer2: chaintip {new_blockid}
            Node->>WS: broadcast_ws("new_block", block_data)
            WS-->>Frontend: {type: "new_block", data: {...}}
            Frontend->>Frontend: Refresh stats + chain
        end
    end
    
    Note over User,DB: === TRANSACTION PROPAGATION ===
    Peer1->>P2P: ihaveobject {txid}
    P2P->>DB: SELECT EXISTS(oid)
    alt TX unknown
        P2P->>Peer1: getobject {txid}
        Peer1-->>P2P: object {tx_dict}
        P2P->>Node: _handle_object_msg(tx)
        Node->>Node: verify_tx_signature + UTXO conservation
        Node->>DB: Store transaction
        Node->>Node: mempool.try_add_tx()
        Node->>WS: broadcast_ws("new_tx", tx_data)
        WS-->>Frontend: {type: "new_tx", data: {...}}
        Frontend->>Frontend: Update mempool table
    end
    
    Note over User,DB: === CHAIN REORGANIZATION ===
    Peer1->>P2P: chaintip {blockid=E}  (height 5 > local 3)
    P2P->>DB: SELECT EXISTS(oid)
    alt Block E unknown
        P2P->>Peer1: getobject {E}
        Peer1-->>P2P: object {E}
        P2P->>Node: _handle_object_msg(E)
        Node->>DB: Fetch D, E, verify chain
        Node->>DB: Get UTXO for E
        Node->>Node: mempool.rebase_to_block(E)
        Node->>Node: Disconnect C, return its TXs to pool
        Node->>Node: Connect D, E, mark TXs confirmed
        Node->>Node: Re-validate all pending TXs vs UTXO(E)
        Node->>P2P: Broadcast chaintip E
        P2P->>Peer2: chaintip {E}
        Node->>WS: broadcast_ws("reorg", {old_tip: C, new_tip: E})
        WS-->>Frontend: {type: "reorg", data: {...}}
        Frontend->>Frontend: Full refresh (stats, chain, mempool)
    end
    
    Note over User,DB: === PEER DISCOVERY & MAINTENANCE ===
    loop Every 10s (service_loop_delay)
        Node->>Node: resupply_connections()
        alt Connections < threshold (10)
            Node->>PeerMgr: get_available_peers()
            PeerMgr-->>Node: Peer set
            Node->>P2P: Connect to random peers
            P2P->>PeerX: TCP connect + hello + getpeers
        end
        Node->>PeerMgr: save()  // persist peers.json
    end
```

---

## Project Structure

---

## Protocol: Marabu

### Message Types
| Message | Direction | Purpose |
|---------|-----------|---------|
| `hello` | Both | Handshake with version + agent |
| `getpeers` / `peers` | Both | Peer discovery (max 30) |
| `getchaintip` / `chaintip` | Both | Chain tip synchronization |
| `getmempool` / `mempool` | Both | Mempool synchronization |
| `getobject` / `object` | Both | Block/Transaction exchange |
| `ihaveobject` | Both | Object advertisement |
| `error` | Both | Error reporting |

### Block Structure
```json
{
  "type": "block",
  "txids": ["..."],
  "nonce": "0000...",
  "previd": "0000...",
  "created": 1671062400,
  "T": "0000abc000000000000000000000000000000000000000000000000000000000",
  "miner": "MinerName",
  "note": "Optional human-readable note"
}
```

### Transaction Structure
```json
{
  "type": "transaction",
  "inputs": [
    { "sig": "...", "outpoint": { "txid": "...", "index": 0 } }
  ],
  "outputs": [
    { "pubkey": "...", "value": 1000000 }
  ]
}
```
Coinbase transactions have `"height": N` instead of inputs.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQLite3

### 1. Core Node (Python)
```bash
pip install -r requirements.txt
python -m kerma.main
# Or with custom address/port:
python -m kerma.main 0.0.0.0 18018
```

### 2. Backend API Server
```bash
cd backend
pip install -r requirements.txt
python -m kerma.main
# API: http://localhost:3001
# P2P: 0.0.0.0:18018
```

### 3. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:3000
```

### 4. Docker
```bash
docker-compose up -d
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/stats` | Chain height, tip, peers, mempool, uptime |
| `GET /api/chain?limit=50` | Recent blocks |
| `GET /api/blocks/{id}` | Block details |
| `GET /api/mempool` | Pending transactions |
| `GET /api/peers` | Known peers + connection status |
| `GET /api/objects/{id}` | Raw block/transaction |
| `WS /ws/live` | Real-time updates |

---

## Data Flow

### Block Validation Pipeline

```mermaid
flowchart TD
    A["Receive 'object' message<br/>via P2P protocol"] --> B["Parse JSON<br/>validate_object()"]
    B --> C{"obj.type == 'block'?"}
    C -- No --> D["Validate Transaction<br/>validate_transaction()"]
    C -- Yes --> E["Format Validation<br/>validate_block()"]
    
    E --> F{"PoW valid?<br/>id < TARGET"}
    F -- No --> G["Reject: INVALID_BLOCK_POW"]
    F -- Yes --> H{"Timestamp > prev.created?"}
    H -- No --> I["Reject: INVALID_BLOCK_TIMESTAMP"]
    H -- Yes --> J{"previd exists in DB?"}
    J -- No --> K["Request missing parent<br/>getobject(parent_id)"]
    K --> J
    J -- Yes --> L{"All txids in DB?"}
    L -- No --> M["Request missing TXs<br/>getobject(tx_id)"]
    M --> L
    L -- Yes --> N["UTXO Verification<br/>verify_block_tail()"]
    
    N --> O{"Coinbase valid?<br/>height match, reward ≤ max"}
    O -- No --> P["Reject: INVALID_BLOCK_COINBASE"]
    O -- Yes --> Q["Store block, UTXO, height"]
    
    Q --> R{"New height > tip_height?"}
    R -- No --> S["Done: block stored"]
    R -- Yes --> T["Chain Reorg Detected!"]
    T --> U["Update tip_id, tip_height"]
    U --> V["Broadcast chaintip to peers"]
    V --> W["Rebase Mempool<br/>rebase_to_block(new_tip)"]
    W --> X["Re-validate pending TXs<br/>against new UTXO"]
    X --> Y["Keep valid, drop conflicts"]
    Y --> S
    
    D --> Z["Verify signatures<br/>Ed25519"]
    Z --> AA["Check UTXO conservation<br/>inputs ≥ outputs"]
    AA --> AB{"Valid?"}
    AB -- No --> AC["Reject: INVALID_TX_*"]
    AB -- Yes --> AD["Add to mempool<br/>if no conflicts"]
```

### Mempool Rebase on Reorg

```mermaid
flowchart LR
    subgraph OldChain["Old Chain (disconnected)"]
        C1["Block C<br/>TXs: c1, c2"]
    end
    
    subgraph Common["Common Ancestor"]
        B["Block B"]
    end
    
    subgraph NewChain["New Chain (connected)"]
        D1["Block D<br/>TXs: d1"]
        E1["Block E<br/>TXs: e1, e2"]
    end
    
    C1 -.->|disconnect| Pool["Candidate Pool<br/>c1, c2, old_mempool"]
    D1 -.->|connect| Confirmed["Confirmed TXs<br/>d1, e1, e2"]
    E1 -.->|connect| Confirmed
    
    Pool --> Revalidate["Re-validate all<br/>against UTXO(E)"]
    Revalidate --> Valid["Valid TXs<br/>→ mempool"]
    Revalidate --> Invalid["Invalid/Conflicts<br/>→ dropped"]
```

---

## Testing

```bash
# Run all integration tests (requires running node on port 18018)
python -m pytest tests/ -v

# Test coverage:
# - Handshake, getchaintip, getpeers, getmempool
# - Block validation: PoW, timestamps, genesis, parent blocks
```

---

## Configuration

### Core (`kerma/constants.py`)
```python
PORT = 18018
BLOCK_TARGET = "0000abc000000000000000000000000000000000000000000000000000000000"
BLOCK_REWARD = 50_000_000_000_000  # 50 TMC (12 decimals)
GENESIS_BLOCK_ID = "00002fa163c7dab0991544424b9fd302bb1782b185e5a3bbdf12afb758e57dee"
```

### Backend (`backend/kerma/config.py`)
Environment variables:
- `KERMA_PORT` (default: 18018)
- `KERMA_API_PORT` (default: 3001)
- `KERMA_DB` (default: `db.db` in project root)

### Frontend
- `NEXT_PUBLIC_API_URL` (default: `http://localhost:3001`)

---

## Tutorial: Blockchain for Complete Beginners

This section explains KermaChain in plain English — no computer science degree required.

### What Is a Blockchain, Really?

Imagine a **shared Google Sheet** that everyone can see, but **nobody can edit past rows**. Every few minutes, a new row gets added with recent transactions. Once added, it's permanent.

That's a blockchain:
- **Blocks** = rows in the spreadsheet
- **Chain** = each row references the previous one (so you can't change history)
- **Nodes** = computers running this software, all keeping identical copies

### What Is KermaChain?

KermaChain is a **teaching blockchain** — a simplified but real implementation of a cryptocurrency network. It demonstrates all the core concepts:
- Peer-to-peer networking (nodes talk directly, no central server)
- Digital signatures (Ed25519 — same math used by Signal, SSH, Solana)
- Proof-of-Work mining (find a rare hash, like a lottery)
- UTXO model (track unspent coins, not account balances)
- Chain reorganizations (when two miners find blocks simultaneously)

It's built for **learning**, not production use.

---

### The Three Pieces You'll Run

```
┌─────────────────────────────────────────────────────────────┐
│  1. CORE NODE (Python)           │  2. API SERVER (Python)  │
│  kerma/main.py                   │  backend/kerma/main.py   │
│  - Connects to other nodes       │  - REST API on :3001     │
│  - Validates blocks/transactions │  - WebSocket for live UI │
│  - Stores data in SQLite         │  - Reads from SQLite     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ 3. DASHBOARD (JS)   │
                    │ frontend/           │
                    │ - Next.js on :3000  │
                    │ - Calls API + WS    │
                    └─────────────────────┘
```

You can run just the **core node** (headless, for testing), or all three for the full visual experience.

---

### Step-by-Step: Run Everything Locally

#### Prerequisites
- **Python 3.11+** — `python --version`
- **Node.js 18+** — `node --version`
- **Git** — `git --version`

#### 1. Clone & Install
```bash
git clone https://github.com/abbysweb/KermaChain.git
cd KermaChain
```

#### 2. Run the Core Node (Terminal 1)
```bash
# Install Python deps
pip install -r requirements.txt
# cryptography, that's it — we use stdlib for everything else

# Start the P2P node on port 18018
python -m kerma.main
```
You'll see:
```
Starting KermaChain node...
  P2P: 0.0.0.0:18018
  API: 0.0.0.0:3001
Blockchain initialized at height 0, tip 00002fa1...
Listening on 0.0.0.0:18018
```

#### 3. Run the API Server (Terminal 2)
```bash
cd backend
pip install -r requirements.txt
# aiohttp, cryptography

python -m kerma.main
```
This starts the REST API on `http://localhost:3001` and WebSocket on `ws://localhost:3001/ws/live`.

#### 4. Run the Dashboard (Terminal 3)
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:3000** — you'll see the live dashboard.

---

### What You'll See on the Dashboard

| Section | What It Shows |
|---------|---------------|
| **Stat Cards** | Chain height, connected peers, mempool size, uptime |
| **Height Chart** | Visual timeline of blocks |
| **Recent Blocks** | Each block: height, miner, tx count, timestamp |
| **Mempool** | Pending transactions waiting to be mined |
| **Peers** | Known nodes, green = connected |
| **Explainer** | Click to expand — animated step diagram |

The dashboard **polls the API every 5 seconds** and listens on WebSocket for instant updates when a new block or transaction arrives.

---

### Key Concepts Explained

#### 1. UTXO (Unspent Transaction Output) — "Digital Cash"
Unlike a bank (account model: "Alice has $100"), Bitcoin/KermaChain uses **UTXO**:
- You don't have a balance. You have **discrete coins**.
- Transaction: "I spend coin #A123 and #B456, create new coins #C789 (to Bob) and #D012 (change to me)"
- Prevents double-spending: each coin can only be spent once

#### 2. Ed25519 Signatures — "Unforgeable ID"
Every transaction input must be signed by the private key matching the output's public key. The math (elliptic curve) makes it **impossible to forge** without the private key.

#### 3. Proof-of-Work — "The Lottery"
To add a block, you must find a **nonce** (random number) such that:
```
hash(block_data + nonce) < TARGET
```
The target is a very small number (starts with many zeros). This takes millions of tries — **work** that proves you spent compute power.

#### 4. Chain Reorganization — "The Fork"
Two miners find valid blocks at the same height. Network splits temporarily. When the next block arrives, **longest chain wins**. The losing block's transactions go back to the mempool.

#### 5. Mempool — "Waiting Room"
Valid transactions sit here until a miner includes them in a block. On reorg, they're re-validated against the new chain tip.

---

### Project Structure — What's Where?

```
KermaChain/
├── kerma/                    # CORE NODE (run this for headless)
│   ├── main.py              # Entry point, connection handling
│   ├── constants.py         # Genesis block, ports, targets
│   ├── objects.py           # Block/TX validation, UTXO, signatures
│   ├── mempool.py           # Transaction pool + reorg rebasing
│   ├── validator.py         # Pending object tracker (timeouts)
│   ├── network/
│   │   ├── protocol.py      # Message building/parsing
│   │   ├── peer.py          # Peer address class
│   │   ├── peers.py         # Peer persistence (peers.json)
│   │   └── exceptions.py    # Faulty vs non-faulty errors
│   └── storage/
│       ├── db.py            # SQLite schema + genesis init
│       └── jcs.py           # JSON Canonicalization (RFC 8785)
│
├── backend/                  # API SERVER
│   └── kerma/
│       ├── main.py          # aiohttp server entry
│       ├── config.py        # Dataclass config
│       ├── api/server.py    # REST + WebSocket routes
│       ├── core/            # Block, TX, Blockchain, Mempool, UTXO
│       ├── network/         # Async node, peer manager
│       ├── storage/         # Database wrapper
│       └── crypto/          # Hashing, JCS, Ed25519 verify
│
├── frontend/                 # DASHBOARD (Next.js 14 + TS)
│   ├── app/page.tsx         # Main dashboard
│   ├── components/          # StatCard, BlockCard, HeightChart, etc.
│   └── lib/                 # API client, WebSocket hook, types
│
├── tests/                    # Integration tests (pytest)
│   ├── test_full.py         # Handshake, getchaintip, peers, mempool
│   └── test_transactions.py # Block validation: PoW, timestamps, genesis
│
└── README.md                # You are here
```

---

### Running the Tests

Requires the **core node running on port 18018** (Terminal 1 above):

```bash
python -m pytest tests/ -v
```

Tests cover:
- Handshake + basic RPC (getchaintip, getpeers, getmempool)
- Block validation: invalid PoW, future timestamp, fake genesis, missing parent

---

### Common Issues

| Problem | Fix |
|---------|-----|
| `Address already in use` | Kill old process: `taskkill /PID <pid> /F` (Windows) or `lsof -ti:18018 \| xargs kill` (Mac/Linux) |
| Frontend shows mock data | Ensure API server (Terminal 2) is running on :3001 |
| `ModuleNotFoundError: kerma` | Run from project root, or `pip install -e .` |
| WebSocket fails in browser | Check CORS — API allows all origins by default |

---

### Next Steps for Learning

1. **Read the code** — Start with `kerma/objects.py` (validation logic)
2. **Add a feature** — Try implementing a simple mining endpoint
3. **Break things** — Send malformed blocks via the tests, see how validation catches them
4. **Scale up** — Run multiple nodes on different ports, watch them sync

---

### Why "KermaChain"?

**Kerma** = "Kernel" + "Karma" — the core engine of actions and consequences in a blockchain.

---

## License

MIT License - See LICENSE file for details.