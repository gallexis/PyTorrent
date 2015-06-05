__author__ = 'alexisgallepe'

import time
import PeersManager
import PeerSeeker
import PiecesManager
import Torrent
import Tracker


class Run(object):
    def __init__(self):
        self.torrent = Torrent.Torrent("z.torrent")
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

                rarestP = min(self.peersManager.piecesByPeer)
                rarestP = self.peersManager.piecesByPeer.index(rarestP)

                if not self.piecesManager.pieces[rarestP].finished:
                    data = self.piecesManager.pieces[rarestP].getEmptyBlock()
                    if data:
                        index, offset, length = data
                        self.peersManager.requestNewPiece(index, offset, length)

                for piece in self.piecesManager.pieces:
                    for block in piece.blocks:
                        if (int(time.time()) - block[3] ) > 10 and block[0] == "Pending" :
                            block[0] = "Free"
                            block[3] = int(time.time())

                b=0
                for i in range(self.piecesManager.numberOfPieces):
                    for j in range(self.piecesManager.pieces[i].num_blocks):
                        if self.piecesManager.pieces[i].blocks[j][0]=="Full":
                            b+=len(self.piecesManager.pieces[i].blocks[j][2])

                print "Nb peers: ",len(self.peersManager.unchokedPeers)," File: ",self.torrent.length,"Received: ",b


            #print len(self.peersManager.unchokedPeers)
            time.sleep(1)


        # if one file
        if len(self.torrent.names) > 1:
            # nameFiles = torrent['files']['path']
            raise('To be completed')

        else:
            fileName = self.torrent.names[0]
            self.piecesManager.createFile(fileName)
            print "File ",fileName,' created'