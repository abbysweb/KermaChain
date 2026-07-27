import os
import json
from kerma.network.peer import Peer


class Peers:
    PEER_DB_FILE = "peers.json"

    def __init__(self):
        self.peers = set()
        self.isDirty = False

        if os.path.isfile(self.PEER_DB_FILE):
            try:
                with open(self.PEER_DB_FILE, 'r') as file:
                    contents = file.read()
                    if contents.strip():
                        dec = json.loads(contents)
                        if isinstance(dec, list):
                            for p in dec:
                                try:
                                    host, port = p.split(':')
                                    self.peers.add(Peer(host, int(port)))
                                except Exception:
                                    pass
            except Exception:
                pass

    def addAll(self, peers):
        for peer in peers:
            self.addPeer(peer)

    def addPeer(self, peer: Peer):
        if peer not in self.peers:
            self.peers.add(peer)
            self.isDirty = True

    def removePeer(self, peer: Peer):
        if peer in self.peers:
            self.peers.remove(peer)
            self.isDirty = True

    def save(self):
        if self.isDirty:
            try:
                with open(self.PEER_DB_FILE, 'w') as file:
                    serialized_peer_list = []
                    for peer in self.peers:
                        serialized_peer_list.append(str(peer))
                    file.write(json.dumps(serialized_peer_list))
                self.isDirty = False
            except Exception:
                pass

    def getPeers(self):
        return self.peers
