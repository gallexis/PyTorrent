
__author__ = 'alexisgallepe'

import time
import PeersManager
import PeerSeeker
import PiecesManager
import Torrent
import Tracker
import logging

class Run(object):
    def __init__(self):
        self.torrent = Torrent.Torrent("i.torrent")
        self.tracker = Tracker.Tracker(self.torrent)
        self.peerSeeker = PeerSeeker.PeerSeeker(self.tracker, self.torrent)
        self.piecesManager = PiecesManager.PiecesManager(self.torrent)
        self.peersManager = PeersManager.PeersManager(self.torrent,self.piecesManager)

        logging.info("Start peers manager")
        self.peersManager.start()

        logging.info("Start peer checker")
        self.peerSeeker.start()

        logging.info("Start pieces manager")
        self.piecesManager.start()

    def start(self):
        old=0.0

        while not self.piecesManager.arePiecesCompleted():
            if len(self.peersManager.unchokedPeers) > 0:

                for piece in self.piecesManager.pieces:
                    if not piece.finished:
                        pieceIndex = piece.pieceIndex

                        peer = self.peersManager.getUnchokedPeer(pieceIndex)
                        if not peer:
                            continue

                        data = self.piecesManager.pieces[pieceIndex].getEmptyBlock()

                        if data:
                            index, offset, length = data
                            self.peersManager.requestNewPiece(peer,index, offset, length)

                        piece.isComplete()

                ##########################
                        for block in piece.blocks:
                            if ( int(time.time()) - block[3] ) > 8 and block[0] == "Pending" :
                                block[0] = "Free"
                                block[3] = 0

                b=0
                for i in range(self.piecesManager.numberOfPieces):
                    for j in range(self.piecesManager.pieces[i].num_blocks):
                        if self.piecesManager.pieces[i].blocks[j][0]=="Full":
                            b+=len(self.piecesManager.pieces[i].blocks[j][2])

                print "Number of peers: ",len(self.peersManager.unchokedPeers)," Completed: ",float((float(b) / self.torrent.totalLength)*100),"%"


               ##########################

            time.sleep(0.1)