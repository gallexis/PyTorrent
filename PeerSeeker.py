__author__ = 'alexisgallepe'

import time
import Peer
from threading import Thread
from pubsub import pub


class PeerSeeker(Thread):
    def __init__(self, newpeersQueue, torrent):
        Thread.__init__(self)
        self.newpeersQueue = newpeersQueue
        self.torrent = torrent
        self.peerFailed = [("","")]

    def run(self):
        while not self.newpeersQueue.empty():
            # TODO : if peerConnected == 50 sleep 50 seconds by adding new event, start,stop,slow ...
            peer = self.newpeersQueue.get()
            if not (peer[0],peer[1]) in self.peerFailed:
                p = Peer.Peer(self.torrent,peer[0],peer[1])
                if not p.connectToPeer(3):
                    self.peerFailed.append((peer[0],peer[1]))
                else:
                    pub.sendMessage('PeersManager.newPeer',peer=p)