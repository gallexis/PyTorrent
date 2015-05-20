#!/usr/local/bin/python
__author__ = 'alexisgallepe'

import struct

import Torrent
import Tracker
from pubsub import pub
import PeersManager
import PeerSeeker


if __name__ == '__main__':

    torrent = Torrent.Torrent("w.torrent")
    tk = Tracker.Tracker(torrent)
    peerMngr = PeersManager.PeersManager(torrent)
    pc = PeerSeeker.PeerSeeker(tk, torrent)

    pub.subscribe(peerMngr.addPeer, 'newPeer')

    print "start mngr"
    peerMngr.start()

    print "start PeerChecker"
    pc.start()