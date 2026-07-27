import pytest
import time
from tests.test_transactions import (
    connect_to_node, wait_for_msg, send_msg, get_objid, mine_block, GENESIS_ID
)


class TestIntegration:
    def test_handshake(self):
        s = connect_to_node("Integration Test")
        assert s is not None, "Cannot connect to node"
        msg = wait_for_msg(s, ['peers', 'getpeers', 'getchaintip', 'getmempool', 'error'], timeout=3)
        s.close()

    def test_getchaintip(self):
        s = connect_to_node("Chaintip Test")
        assert s is not None
        send_msg(s, {"type": "getchaintip"})
        msg = wait_for_msg(s, ['chaintip'], timeout=3)
        s.close()
        assert msg is not None, "No chaintip response"
        assert 'blockid' in msg

    def test_getpeers(self):
        s = connect_to_node("Peers Test")
        assert s is not None
        send_msg(s, {"type": "getpeers"})
        msg = wait_for_msg(s, ['peers'], timeout=3)
        s.close()
        assert msg is not None, "No peers response"
        assert isinstance(msg.get('peers'), list)

    def test_getmempool(self):
        s = connect_to_node("Mempool Test")
        assert s is not None
        send_msg(s, {"type": "getmempool"})
        msg = wait_for_msg(s, ['mempool'], timeout=3)
        s.close()
        assert msg is not None, "No mempool response"
        assert isinstance(msg.get('txids'), list)
