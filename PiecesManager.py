__author__ = 'alexisgallepe'

import Piece
from threading import Thread
from pubsub import pub

class PiecesManager(Thread):
    def __init__(self, torrent, peersManager):
        Thread.__init__(self)
        self.torrent = torrent
        self.peersManager = peersManager

        self.piecesCompleted = False

        if torrent.length % torrent.pieceLength == 0:
            self.numberOfPieces = torrent.length / torrent.pieceLength
        else:
            self.numberOfPieces = (torrent.length / torrent.pieceLength) + 1

        self.pieces = self.generatePieces()

        # Create events
        pub.subscribe(self.receiveBlockPiece, 'event.Piece')
        pub.subscribe(self.handlePeerRequests, 'event.PeerRequestsPiece')
        pub.subscribe(self.updateBitfield, 'event.PieceCompleted')

    def run(self):
        while not self.piecesCompleted:
            # pseudo code
            self.peersManager.askForBlock()

            self.arePiecesCompleted()

    def updateBitfield(self,pieceIndex):
        # TODO
        pass

    def receiveBlockPiece(self,piece):
        piece_index,piece_offset,piece_data = piece
        self.pieces[piece_index].setBlock(piece_offset,piece_data)

    def handlePeerRequests(self,piece):
        piece_index,piece_offset,piece_data = piece


    def generatePieces(self, pieces=None):
        pieces = []
        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20
            pieces.append(Piece.Piece(i, self.torrent.pieceLength, self.torrent.info_hash[start:end]))

        return pieces

    """
    def createFile(self):
        fd = open(self.fileName, "wb")
        data = b""
        for piece in self.pieces:
            data += piece.assembleData()

        fd.write(data)
    """

    def arePiecesCompleted(self):
        for piece in self.pieces:
            if not piece.isComplete():
                return False

        self.piecesCompleted = True
        #self.createFile()
        print "file completed"
        return True

