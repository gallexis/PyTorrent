__author__ = 'alexisgallepe'

import peer
from threading import Thread
from pubsub import pub


class PeersSeeker(Thread):
    def __init__(self, new_peers_queue, torrent):
        Thread.__init__(self)
        self.new_peers_queue = new_peers_queue
        self.torrent = torrent
        self.rejected_peers = []  # list of ('ip', 'port')

    def run(self):
        while True:
            # TODO : if peerConnected == 50 sleep 50 seconds by adding new event, start,stop,slow ...
            new_peer = self.new_peers_queue.get()
            if not (new_peer[0], new_peer[1]) in self.rejected_peers:
                p = peer.Peer(self.torrent, new_peer[0], new_peer[1])
                if not p.connect_to_peer():
                    self.rejected_peers.append((new_peer[0], new_peer[1]))
                else:
                    pub.sendMessage('PeersManager.newPeer', peer=p)
