import random

__author__ = 'alexisgallepe'

import time
import PeersManager
import PeerSeeker
import PiecesManager
import Torrent
import Tracker


class Run(object):
    def __init__(self):
        self.torrent = Torrent.Torrent("x.torrent")
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

    def run(self,structure,idPiece,numberOfPeers,quo):
        if not self.piecesManager.pieces[idPiece].finished:
            for i in range(numberOfPeers / quo):
                alea =random.randrange(0,numberOfPeers)
                print "alea", alea ,' np', (numberOfPeers)

                try:
                    peer=structure["peers"][alea]
                except:
                    print "BUG alea", alea ,' np', (numberOfPeers)
                    continue

                data = self.piecesManager.pieces[idPiece].getEmptyBlock()
                if data:
                    index, offset, length = data
                    self.peersManager.requestNewPiece(peer,index, offset, length)


    def start(self):
        while not self.piecesManager.arePiecesCompleted():
            if len(self.peersManager.unchokedPeers) > 0:

                piecesByRarestPiece = self.peersManager.rarestPieces.getSortedPieces()

                str = piecesByRarestPiece.pop()
                self.run(str,str["idPiece"],str["numberOfPeers"],1)

                for structure in piecesByRarestPiece:
                    idPiece = structure["idPiece"]
                    numberOfPeers = structure["numberOfPeers"]
                    self.run(structure,idPiece,numberOfPeers,2)

                ##########################
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
                ##########################

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