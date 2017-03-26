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

        # Create events
        pub.subscribe(self.receiveBlockPiece, 'PiecesManager.Piece')
        pub.subscribe(self.updateBitfield, 'PiecesManager.PieceCompleted')

    def updateBitfield(self,pieceIndex):
        self.bitfield[pieceIndex] = 1

    def receiveBlockPiece(self,piece):
        piece_index,piece_offset,piece_data = piece
        self.pieces[int(piece_index)].setBlock(piece_offset,piece_data)


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
            if not piece.finished:
                return False

        self.piecesCompleted = True
        logging.info("File(s) downloaded")
        return True

    def getFiles(self):
        files = []
        pieceOffset = 0
        pieceSizeUsed = 0

        for f in self.torrent.fileNames:

            currentSizeFile = f["length"]
            fileOffset = 0

            while  currentSizeFile > 0:
                idPiece = pieceOffset / self.torrent.pieceLength
                pieceSize = self.pieces[idPiece].pieceSize - pieceSizeUsed

                if currentSizeFile - pieceSize < 0:
                    file = {"length": currentSizeFile,"idPiece":idPiece ,"fileOffset":fileOffset, "pieceOffset":pieceSizeUsed ,"path":f["path"]}
                    pieceOffset +=  currentSizeFile
                    fileOffset +=  currentSizeFile
                    pieceSizeUsed += currentSizeFile
                    currentSizeFile = 0

                else:
                    currentSizeFile -= pieceSize
                    file = {"length":pieceSize,"idPiece":idPiece ,"fileOffset":fileOffset,"pieceOffset":pieceSizeUsed , "path":f["path"]}
                    pieceOffset += pieceSize
                    fileOffset += pieceSize
                    pieceSizeUsed = 0

                files.append(file)
        return files


    def getBlock(self, piece_index,block_offset,block_length):

        for piece in self.pieces:
            if piece_index == piece.pieceIndex:
                if piece.finished:
                    return piece.getBlock(block_offset,block_length)
                else:
                    break

        return None

