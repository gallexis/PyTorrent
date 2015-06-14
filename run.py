
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
        self.torrent = Torrent.Torrent("w.torrent")
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
        while not self.piecesManager.arePiecesCompleted():
            if len(self.peersManager.unchokedPeers) > 0:

                for piece in self.piecesManager.pieces:
                    if not piece.finished:
                        index = piece.pieceIndex

                        peer = self.peersManager.getUnchokedPeer(index)
                        if not peer:
                            break

                        data = self.piecesManager.pieces[index].getEmptyBlock()

                        while data:
                            index, offset, length = data
                            if not self.peersManager.requestNewPiece(peer,index, offset, length):
                                break

                            data = self.piecesManager.pieces[index].getEmptyBlock()

                self.peersManager.incAllPeersCounter()

                ##########################
                for piece in self.piecesManager.pieces:
                    for block in piece.blocks:
                        if (int(time.time()) - block[3] ) > 8 and block[0] == "Pending" :
                            block[0] = "Free"
                            block[3] = 0

                b=0
                for i in range(self.piecesManager.numberOfPieces):
                    for j in range(self.piecesManager.pieces[i].num_blocks):
                        if self.piecesManager.pieces[i].blocks[j][0]=="Full":
                            b+=len(self.piecesManager.pieces[i].blocks[j][2])

                print( "Number of peers: ",len(self.peersManager.unchokedPeers)," Completed: ",int((float(b) / self.torrent.totalLength)*100),"%")
                ##########################

            time.sleep(1)

