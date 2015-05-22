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
    peersManager = PeersManager.PeersManager(torrent)
    pc = PeerSeeker.PeerSeeker(tk, torrent)

    print "Start manager"
    peersManager.start()

    print "Start PeerChecker"
    pc.start()