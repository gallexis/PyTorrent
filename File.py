__author__ = 'alexisgallepe'

import Piece


class File(object):
    def __init__(self, torrent, fileName, peerManager):
        self.torrent = torrent
        self.fileName = fileName
        self.peerManager = peerManager

        self.fileCompleted = False

        if torrent.length % torrent.pieceLength == 0:
            self.numberOfPieces = torrent.length / torrent.pieceLength
        else:
            self.numberOfPieces = (torrent.length / torrent.pieceLength) + 1

        self.pieces = self.generatePieces()

    def generatePieces(self, pieces=None):
        pieces = []
        for i in range(self.numberOfPieces):
            start = i * 20
            end = start + 20
            pieces.append(Piece.Piece(i, self.torrent.pieceLength, self.torrent.info_hash[start:end]))

        return pieces

    def createFile(self):
        fd = open(self.fileName, "wb")
        data = b""
        for piece in self.pieces:
            data += piece.assembleData()

        fd.write(data)

    def isFileCompleted(self):
        for piece in self.pieces:
            if not piece.isComplete():
                return False

        self.fileCompleted = True
        self.createFile()
        print "file completed"
        return True

    def doAction(self):
        if not self.fileCompleted:
            # pseudo code
            emptyBlock,piece = self.getBlock()
            block = self.peerManager.askForBlock(emptyBlock)
            piece.setBlock(block) # error in args

            self.isFileCompleted()