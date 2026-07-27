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

```
KermaChain/
├── kerma/                          # Core blockchain node (Python)
│   ├── main.py                     # Entry point, P2P connection handling
│   ├── constants.py                # Genesis block, network config, targets
│   ├── objects.py                  # Block/TX validation, UTXO, Ed25519 sigs
│   ├── mempool.py                  # Transaction pool with reorg rebasing
│   ├── validator.py                # Pending object dependency tracking
│   ├── network/
│   │   ├── protocol.py             # Message construction/validation
│   │   ├── peer.py                 # Peer representation
│   │   ├── peers.py                # Peer persistence (peers.json)
│   │   └── exceptions.py           # Faulty/Non-faulty node exceptions
│   └── storage/
│       ├── db.py                   # SQLite schema + genesis init
│       └── jcs.py                  # JSON Canonicalization (RFC 8785)
│
├── backend/                        # Async REST API + WebSocket server
│   └── kerma/
│       ├── main.py                 # API server entry point
│       ├── config.py               # Dataclass configuration
│       ├── crypto/                 # Hashing, signing, JCS
│       ├── core/                   # Blockchain, Block, TX, Mempool, UTXO
│       ├── network/                # Async node, protocol, peer manager
│       ├── storage/                # Database abstraction
│       └── api/                    # aiohttp REST + WebSocket
│
├── frontend/                       # Next.js 14 Dashboard (TypeScript)
│   ├── app/
│   │   ├── page.tsx                # Main dashboard (real API data)
│   │   └── layout.tsx              # Root layout
│   ├── components/
│   │   ├── stats/StatCard.tsx      # Metric cards
│   │   ├── blockchain/             # BlockCard, HeightChart
│   │   ├── mempool/MempoolTable.tsx
│   │   ├── network/PeerGrid.tsx
│   │   ├── educational/            # Explainer, StepDiagram
│   │   └── layout/Header.tsx
│   ├── lib/
│   │   ├── api.ts                  # API client
│   │   ├── types.ts                # TypeScript interfaces
│   │   └── ws.ts                   # WebSocket hook
│   └── ...
│
├── tests/                          # Integration tests (pytest)
└── docs/                           # Development history
```

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
1. **Receive** `object` message → parse JSON
2. **Format validation** (`validate_block`) → structure, PoW, timestamp, previd
3. **Dependency check** → fetch missing parent block + transactions
4. **UTXO verification** → apply transactions to parent UTXO set
5. **Coinbase validation** → height match, reward ≤ block_reward + fees
6. **Store** → objects, UTXO, height tables
7. **Chain tip update** → if height > current tip, reorg + rebroadcast
8. **Mempool rebase** → re-validate pending TXs against new UTXO

### Mempool Rebase on Reorg
```
Old tip: A ← B ← C (height 3)
New tip: A ← B ← D ← E (height 4)

1. Find LCA (B)
2. Disconnect C → return its TXs to candidate pool
3. Connect D, E → mark their TXs as confirmed
4. Re-validate all candidates against new UTXO (E)
5. Keep valid, drop conflicts
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

## Development History

See [`docs/`](docs/) for the assignment progression:
- `001-initial-merge.md` - Initial consolidation
- `002-oop-refactor.md` - Object-oriented refactor

---

## License

MIT License - See LICENSE file for details.