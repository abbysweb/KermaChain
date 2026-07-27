# Action: Initial Codebase Merge (Tasks 1-5)

**Date:** 2026-07-27
**Phase:** Pre-project
**Status:** Complete

## What Changed
- Merged 5 cryptocurrency assignment codebases into single project "KermaChain"
- Task 1 (P2P networking skeleton) → superseded by Task 5
- Task 2 (Transaction validation) → subset of Task 5
- Task 3 (Block validation, UTXO) → subset of Task 5
- Task 4 (Pending block validator) → subset of Task 5
- Task 5 (Full node with mempool rebase) → base for merged project

## Why
- Consolidate incremental assignments into coherent portfolio project
- Single codebase easier to maintain and present

## Files Created
- `kerma/__init__.py` — package init
- `kerma/constants.py` — configuration constants
- `kerma/objects.py` — validation + UTXO logic (from Task 5)
- `kerma/mempool.py` — mempool with rebasing (from Task 5)
- `kerma/validator.py` — pending object tracker (from Task 5)
- `kerma/network/peer.py` — peer representation
- `kerma/network/peers.py` — peer persistence
- `kerma/network/protocol.py` — message handling (extracted from Task 5 main.py)
- `kerma/network/exceptions.py` — exception hierarchy
- `kerma/storage/db.py` — SQLite initialization
- `kerma/storage/jcs.py` — JSON Canonicalization

## Decisions Made
- Used Task 5 codebase as base (most complete implementation)
- Flattened message/msgexceptions.py → network/exceptions.py
- Extracted protocol logic from monolithic main.py into protocol.py
- Kept Task 5's 3-table DB schema (objects, utxo, heights)

## Follow-up
- Complete OOP redesign (Phase 2)
- Add REST API layer (Phase 3)
- Build frontend dashboard (Phase 4)
