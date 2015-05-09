__author__ = 'alexisgallepe'

import math

import utils


BLOCK_SIZE = 2 ** 14


class Piece(object):
    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.num_blocks = int(math.ceil(float(pieceSize) / BLOCK_SIZE))
        # self.blockTracker = BitArray(self.num_blocks)
        self.blocks = self.initBlocks()

    def initBlocks(self):
        print "init Blocks"

        # block -> (    Statut_Block    ,BLOCK_SIZE,data)
        #            (Free|Pending|Full)      1      2
        blocks = [["Free", BLOCK_SIZE, ""]] * (self.num_blocks - 1)
        # size of last block
        blocks[self.num_blocks] = ["Free", int(float(self.pieceSize) % BLOCK_SIZE), ""]
        return blocks

    def add_datas(self, offset, data):
        if offset == 0:
            index = 0
        else:
            index = offset / BLOCK_SIZE
        self.blocks[index][2] = data
        self.blocks[index][0] = "Full"

        if self.isComplete():
            self.finished = True

    def getEmptyBlock(self):
        for i in range(len(self.blocks)):
            if self.blocks[i][0] == "Free":
                self.blocks[i][0] = "Pending"
                # index, begin(offset), blockSize
                return self.pieceIndex, i * BLOCK_SIZE, self.blocks[i][1]

        raise Exception("No block left, Piece is complete or blocks pending remaining")

    def isComplete(self):
        # If there is at least one block Free|Pending -> Piece not complete -> return false
        for block in self.blocks:
            if block[0] == "Free" or block[0] == "Pending":
                return False

        # Before returning True, we must check if hashes matches
        return self.isHashPieceCorrect()

    def isHashPieceCorrect(self):
        buf = ""
        for block in self.blocks:
            buf += block[2]

        if utils.sha1_hash(buf) == self.pieceHash:
            return True
        else:
            print "error Piece Hash "
            print utils.sha1_hash(buf)
            print self.pieceHash
            self.blocks = self.initBlocks()
            return False

