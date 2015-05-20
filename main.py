#!/usr/local/bin/python
__author__ = 'alexisgallepe'

import struct

import Torrent
import Tracker
from pubsub import pub
import PeersManager
import NewPeersChecker


if __name__ == '__main__':

    torrent = Torrent.Torrent("w.torrent")
    tk = Tracker.Tracker(torrent)
    peerMngr = PeersManager.PeersManager(torrent)
    pc = NewPeersChecker.NewPeersChecker(tk, torrent)

    pub.subscribe(peerMngr.addPeer, 'newPeer')



    print "start mngr"
    peerMngr.start()

    print "start PeerChecker"
    pc.start()