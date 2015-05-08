__author__ = 'alexisgallepe'

import math

from bitstring import BitArray

BLOCK_SIZE = 2 ** 14


class Piece(object):
    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.num_blocks = int(math.ceil(float(pieceSize) / BLOCK_SIZE))
        # self.blockTracker = BitArray(self.num_blocks)
        self.blocks = [False] * self.num_blocks

    def add_datas(self, offset, data):

        if offset == 0:
            index = 0
        else:
            index = offset / BLOCK_SIZE

        self.blocks[index] = data