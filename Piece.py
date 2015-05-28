__author__ = 'alexisgallepe'

import math

from libs import utils
from pubsub import pub

BLOCK_SIZE = 2 ** 14


class Piece(object):
    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.pieceData = b""
        self.num_blocks = int(math.ceil(float(pieceSize) / BLOCK_SIZE))
        self.blocks = []

        self.initBlocks()

    # TODO : add timestamp for pending blocks
    def initBlocks(self):
        self.blocks = []
        if self.num_blocks > 1:
            # block -> (    Statut_Block    ,BLOCK_SIZE,data)
            #            (Free|Pending|Full)
            blocks = [["Free", BLOCK_SIZE, b""]] * (self.num_blocks - 1)
            # size of last block
            blocks[self.num_blocks] = ["Free", int(float(self.pieceSize) % BLOCK_SIZE), b""]
        else:
            blocks = ["Free", int(self.pieceSize), b""]
        self.blocks.append(blocks)

    def setBlock(self, offset, data):
        if offset == 0:
            index = 0
        else:
            index = offset / BLOCK_SIZE
        self.blocks[index][2] = data
        self.blocks[index][0] = "Full"

        if self.isComplete():
            self.finished = True

    def getEmptyBlock(self):
        if not self.isComplete():
            for i in range(len(self.blocks)):
                if self.blocks[i][0] == "Free":
                    self.blocks[i][0] = "Pending"
                    # index, begin(offset), blockSize
                    return self.pieceIndex, i * BLOCK_SIZE, self.blocks[i][1]

    def freeBlockLeft(self):
        for block in self.blocks:
            if block[0] == "Free":
                return True
        return False

    def isComplete(self):
        # If there is at least one block Free|Pending -> Piece not complete -> return false
        for block in self.blocks:
            if block[0] == "Free" or block[0] == "Pending":
                return False

        # Before returning True, we must check if hashes matches
        data = self.assembleData()
        if self.isHashPieceCorrect(data):
            self.pieceData = data
            pub.sendMessage('event.PieceCompleted',pieceIndex=self.pieceIndex)
            return True
        else:
            return False

    def assembleData(self):
        buf = b""
        for block in self.blocks:
            buf += block[2]
        return buf

    def isHashPieceCorrect(self,data):
        if utils.sha1_hash(data) == self.pieceHash:
            return True
        else:
            print "error Piece Hash "
            print "h1",utils.sha1_hash(data)
            print "self h2", self.pieceHash
            self.blocks = self.initBlocks()
            return False