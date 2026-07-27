import copy
import sqlite3
import traceback

import kerma.constants as const
import kerma.objects as objects


def fetch_object(oid, cur):
    try:
        res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (oid,))
        row = res.fetchone()
        if row:
            return objects.expand_object(row[0])
    except Exception:
        pass
    return None


def fetch_utxo(bid, cur):
    try:
        res = cur.execute("SELECT utxoset FROM utxo WHERE blockid = ?", (bid,))
        row = res.fetchone()
        if row:
            return objects.expand_object(row[0])
    except Exception:
        pass
    return None


def find_all_txs(txids):
    txs = []
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        for txid in txids:
            tx = fetch_object(txid, cur)
            if tx:
                txs.append(tx)
    except Exception:
        pass
    finally:
        con.close()
    return txs


def get_all_txids_in_blocks(blocks):
    txids = []
    for block in blocks:
        if 'txids' in block:
            txids.extend(block['txids'])
    return txids


def get_chain_path(tip, cur):
    path = []
    curr = tip
    while curr is not None:
        path.append(curr)
        block = fetch_object(curr, cur)
        if block is None:
            break
        curr = block.get('previd')
    return list(reversed(path))


def get_lca_and_intermediate_blocks(old_tip: str, new_tip: str):
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        path_old = get_chain_path(old_tip, cur)
        path_new = get_chain_path(new_tip, cur)

        split_idx = 0
        min_len = min(len(path_old), len(path_new))
        while split_idx < min_len and path_old[split_idx] == path_new[split_idx]:
            split_idx += 1

        lca = path_old[split_idx - 1] if split_idx > 0 else None
        disconnect_block_ids = list(reversed(path_old[split_idx:]))
        connect_block_ids = path_new[split_idx:]
        return lca, disconnect_block_ids, connect_block_ids
    except Exception as e:
        print(f"[Mempool DEBUG] LCA Error: {e}")
        return None, [], []
    finally:
        con.close()


find_lca_and_intermediate_blocks = get_lca_and_intermediate_blocks


def rebase_mempool(old_tip, new_tip, mptxids):
    pass


class Mempool:
    def __init__(self, bbid: str, butxo: dict):
        self.base_block_id = bbid
        self.utxo = butxo
        self.txs = []

    def try_add_tx(self, tx: dict) -> bool:
        if 'height' in tx:
            return False

        txid = objects.get_objid(tx)
        try:
            current_txids = [objects.get_objid(t) for t in self.txs]
            if txid in current_txids:
                return True

            temp_utxo = copy.deepcopy(self.utxo)
            objects.update_utxo_and_calculate_fee(tx, temp_utxo)

            self.utxo = temp_utxo
            self.txs.append(tx)
            return True
        except Exception:
            return False

    def rebase_to_block(self, bid: str):
        try:
            new_tip = bid
            if self.base_block_id == new_tip:
                return

            con = sqlite3.connect(const.DB_NAME)
            try:
                cur = con.cursor()
                _, disconnect_ids, connect_ids = get_lca_and_intermediate_blocks(self.base_block_id, new_tip)

                new_utxo = fetch_utxo(new_tip, cur)
                if new_utxo is None:
                    print(f"[Mempool DEBUG] Failed to fetch UTXO for {new_tip}")
                    return

                self.base_block_id = new_tip
                self.utxo = new_utxo
                old_mempool_txs = self.txs
                self.txs = []

                new_chain_txids = set()
                for new_bid in connect_ids:
                    block = fetch_object(new_bid, cur)
                    if block:
                        new_chain_txids.update(block['txids'])

                txs_to_readd = []

                for old_bid in reversed(disconnect_ids):
                    block = fetch_object(old_bid, cur)
                    if block:
                        for tid in block['txids']:
                            t = fetch_object(tid, cur)
                            if t and 'height' not in t:
                                txs_to_readd.append(t)

                txs_to_readd.extend(old_mempool_txs)

                print(f"[Mempool DEBUG] Rebasing to {new_tip[:8]}. Re-adding {len(txs_to_readd)} txs.")

                for tx in txs_to_readd:
                    txid = objects.get_objid(tx)
                    if txid not in new_chain_txids:
                        self.try_add_tx(tx)

            finally:
                con.close()
        except Exception as e:
            print(f"[Mempool DEBUG] Rebase Critical Error: {e}")
            traceback.print_exc()

    def get_txids(self):
        return [objects.get_objid(tx) for tx in self.txs]
