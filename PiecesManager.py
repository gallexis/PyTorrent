__author__ = 'alexisgallepe'

import Piece
from libs import utils
import bitstring
from threading import Thread
from pubsub import pub
import string

class PiecesManager(Thread):
    def __init__(self, torrent):
        Thread.__init__(self)
        self.torrent = torrent
        self.piecesCompleted = False

        if torrent.length % torrent.pieceLength == 0:
            self.numberOfPieces = torrent.length / torrent.pieceLength
        else:
            self.numberOfPieces = (torrent.length / torrent.pieceLength) + 1

        self.bitfield = bitstring.BitArray(self.numberOfPieces)
        self.pieces = self.generatePieces()

        # Create events
        pub.subscribe(self.receiveBlockPiece, 'event.Piece')
        pub.subscribe(self.handlePeerRequests, 'event.PeerRequestsPiece')
        pub.subscribe(self.updateBitfield, 'event.PieceCompleted')

    def updateBitfield(self,pieceIndex):
        self.bitfield[pieceIndex] = 1

    def receiveBlockPiece(self,piece):
        piece_index,piece_offset,piece_data = piece
        self.pieces[int(piece_index)].setBlock(piece_offset,piece_data)

    def handlePeerRequests(self,piece):
        piece_index,piece_offset,piece_data = piece

    def generatePieces(self, pieces=None):
        pieces = []
        pieceSizeLeft = self.torrent.length

        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20

            if (pieceSizeLeft - self.torrent.pieceLength) <= 0:
                pieces.append(Piece.Piece(i, pieceSizeLeft, self.torrent.pieces[start:end]))
            else:
                pieces.append(Piece.Piece(i, self.torrent.pieceLength, self.torrent.pieces[start:end]))

            pieceSizeLeft -= self.torrent.pieceLength

        return pieces

    def createFile(self,fileName):
        fd = open(fileName, "wb")
        data = b""
        for piece in self.pieces:
            data += piece.assembleData()

        fd.write(data)

    def arePiecesCompleted(self):
        for piece in self.pieces:
            if not piece.isComplete():
                return False

        self.piecesCompleted = True
        #self.createFile()
        print "file completed"
        return True

