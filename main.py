#!/usr/local/bin/python
__author__ = 'alexisgallepe'

import Torrent
import Tracker
import Peer
import select
from threading import Thread

class PeerManager(Thread):
    def __init__(self,lstPeers):
            Thread.__init__(self)
            self.lstPeers=lstPeers

    def run(self):
        buf = ""
        peers = []
        p = [s.socket for s in self.lstPeers]

        while True:
            try:
                peers, wlist, xlist = select.select(p, [], [], 0.05)
            except Exception, e:
                print e
                break
                pass
            else:
                for peer in peers:
                    # thread managePeer
                    try:
                        msg = peer.recv(4096)
                    except Exception, e:
                        # print "error rec message peer" #if timeout, not an error
                        # self.socket.close()
                        print e
                        break
                    else:
                        if len(msg) == 0: break
                        buf += msg

                    if len(msg) > 0:
                        print self.lstPeers[0].decodeMessagePeer(buf)
                        # return buf
                        pass


if __name__ == '__main__':

    peers =[]

    t = Torrent.Torrent("w.torrent")
    tk = Tracker.Tracker(t)

    peersLst = tk.getPeersFromTrackers()
    peersLst = peersLst[:8]
    print "get peers from tracker"

    for peer in peersLst:
        p = Peer.Peer(t)
        if p.connectToPeer(peer):
            peers.append(p)

    p=PeerManager(peers)
    p.start()

    for p in peers:
        p.sendToPeer(p.handshake)
        print "handshake sent"


