__author__ = 'alexisgallepe'

import Piece
import bitstring
import logging
from threading import Thread
from pubsub import pub

class PiecesManager(Thread):
    def __init__(self, torrent):
        Thread.__init__(self)
        self.torrent = torrent
        self.piecesCompleted = False

        self.numberOfPieces = torrent.numberOfPieces

        self.bitfield = bitstring.BitArray(self.numberOfPieces)
        self.pieces = self.generatePieces()

        self.files = self.getFiles()

        for file in self.files:
            idPiece = file['idPiece']
            self.pieces[idPiece].files.append(file)

        for p in self.pieces:
            print p.files

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

    def generatePieces(self):
        pieces = []

        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20

            if i == (self.numberOfPieces-1):
                pieceLength = self.torrent.totalLength - (self.numberOfPieces-1) * self.torrent.pieceLength
                pieces.append(Piece.Piece(i, pieceLength, self.torrent.pieces[start:end]))
            else:
                pieces.append(Piece.Piece(i, self.torrent.pieceLength, self.torrent.pieces[start:end]))
        return pieces

    def arePiecesCompleted(self):
        for piece in self.pieces:
            if not piece.isComplete():
                return False

        self.piecesCompleted = True
        logging.info("File(s) downloaded")
        return True

    def createFiles(self):
        if len(self.torrent.fileNames) > 1:
            pass

        else:
            fd = open(self.torrent.fileNames[0]["path"], "wb")
            data = b""
            for piece in self.pieces:
                data += piece.assembleData()

            fd.write(data)


    def getFiles(self):
        files = []
        offset = 0

        for f in self.torrent.fileNames:

            tmpSizeFile = f["length"]
            while tmpSizeFile > 0:
                idPiece = offset / self.torrent.pieceLength
                pieceSize = self.pieces[idPiece].pieceSize

                if tmpSizeFile - pieceSize < 0:
                    file = {"length":tmpSizeFile,"idPiece":idPiece ,"start":offset, "fileDescriptor":f["fd"]}
                    offset += tmpSizeFile
                    tmpSizeFile = 0

                else:
                    tmpSizeFile -= pieceSize
                    file = {"length":pieceSize,"idPiece":idPiece ,"start":offset, "fileDescriptor":f["fd"]}
                    offset += pieceSize

                files.append(file)
        return files
