__author__ = 'alexisgallepe'

import time
import PeersManager
import PeerSeeker
import PiecesManager
import Torrent
import Tracker

class Run(object):
    def __init__(self):
        self.torrent = Torrent.Torrent("w.torrent")
        self.tracker = Tracker.Tracker(self.torrent)
        self.peerSeeker = PeerSeeker.PeerSeeker(self.tracker, self.torrent)
        self.piecesManager = PiecesManager.PiecesManager(self.torrent)
        self.peersManager = PeersManager.PeersManager(self.torrent,self.piecesManager)

        print "Start manager"
        self.peersManager.start()

        print "Start PeerChecker"
        self.peerSeeker.start()

        print "Start PiecesManager"
        self.piecesManager.start()

    def start(self):
        while not self.piecesManager.arePiecesCompleted():

            if len(self.peersManager.unchokedPeers) > 0:
                rarestPiece = self.peersManager.calculRarestPiece()

                if self.piecesManager.pieces[rarestPiece].freeBlockLeft():
                    index, offset, length = self.piecesManager.pieces[rarestPiece].getEmptyBlock()
                    self.peersManager.requestNewPiece(index, offset, length)

            #time.sleep(1)

        # if one file
        if len(self.torrent.names) > 1:
            # nameFiles = torrent['files']['path']
            raise('To be completed')

        else:
            fileName = self.torrent.names[0]
            self.piecesManager.createFile(fileName)
            print "File ",fileName,' created'