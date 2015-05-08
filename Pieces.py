__author__ = 'alexisgallepe'

import Piece


class Pieces(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.pieces = None
        self.numberOfPieces = torrent.length / torrent.pieceLength


    def generatePieces(self):
        pieces = []
        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20
            pieces.append(Piece(i, self.torrent.pieceLength, self.torrent.info_hash[start:end]))

        self.pieces = pieces