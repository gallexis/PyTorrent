__author__ = 'alexisgallepe'

import Piece


class File(object):
    def __init__(self, torrent, nameFile):
        self.torrent = torrent
        self.nameFile = nameFile
        self.completeFile = False

        if torrent.length % torrent.pieceLength == 0:
            self.numberOfPieces = torrent.length / torrent.pieceLength
        else:
            self.numberOfPieces = (torrent.length / torrent.pieceLength) + 1

        self.pieces = self.generatePieces()
        self.createFile()

    def generatePieces(self, pieces=None):
        pieces = []
        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20
            pieces.append(Piece.Piece(i, self.torrent.pieceLength, self.torrent.info_hash[start:end]))

        return pieces

    def createFile(self):
        open(self.nameFile, "wb")

    def fileCompleted(self):
        for piece in self.pieces:
            if not piece.isComplete():
                return False

        self.completeFile = True
        return True

    def piecesManager(self):
        while not self.fileCompleted():
            pass
