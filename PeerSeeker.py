__author__ = 'alexisgallepe'

import Peer
from threading import Thread
from pubsub import pub


class PeerSeeker(Thread):
    def __init__(self, new_peers_queue, torrent):
        Thread.__init__(self)
        self.new_peers_queue = new_peers_queue
        self.torrent = torrent
        self.rejected_peers = [("", "")]

    def run(self):
        while True:
            # TODO : if peerConnected == 50 sleep 50 seconds by adding new event, start,stop,slow ...
            peer = self.new_peers_queue.get()
            if not (peer[0], peer[1]) in self.rejected_peers:
                p = Peer.Peer(self.torrent, peer[0], peer[1])
                if not p.connect_to_peer(3):
                    self.rejected_peers.append((peer[0], peer[1]))
                else:
                    pub.sendMessage('PeersManager.newPeer', peer=p)
