__author__ = 'alexisgallepe'

import Piece


class File(object):
    def __init__(self, torrent, nameFile):
        self.torrent = torrent
        self.nameFile = nameFile
        self.pieces = None

        if torrent.length % torrent.pieceLength == 0:
            self.numberOfPieces = torrent.length / torrent.pieceLength
        else:
            self.numberOfPieces = (torrent.length / torrent.pieceLength) + 1


    def generatePieces(self):
        pieces = []
        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20
            pieces.append(Piece(i, self.torrent.pieceLength, self.torrent.info_hash[start:end]))

        self.pieces = pieces

    def createFile(self):
        open(self.nameFile, "wb")

    def piecesManager(self):
        pass