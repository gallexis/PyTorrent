import hashlib

__author__ = 'alexisgallepe'

import math
import time
import logging

from pubsub import pub

BLOCK_SIZE = 2 ** 14


class Piece(object):
    def __init__(self, piece_index, piece_size, piece_hash):
        self.piece_index = piece_index
        self.piece_size = piece_size
        self.piece_hash = piece_hash
        self.is_full = False
        self.files = []
        self.raw_data = b""
        self.number_of_blocks = int(math.ceil(float(piece_size) / BLOCK_SIZE))
        self.blocks = []

        self.init_blocks()

    def init_blocks(self):
        self.blocks = []

        if self.number_of_blocks > 1:
            for i in range(self.number_of_blocks):
                self.blocks.append(["Free", BLOCK_SIZE, b"", 0])

            # Last block of last piece, the special block
            if (self.piece_size % BLOCK_SIZE) > 0:
                self.blocks[self.number_of_blocks - 1][1] = self.piece_size % BLOCK_SIZE

        else:
            self.blocks.append(["Free", int(self.piece_size), b"", 0])

    def update_block_status(self):  # if block is pending for too long : set it free
        for block in self.blocks:
            if (int(time.time()) - block[3]) > 8 and block[0] == "Pending":
                block[0] = "Free"
                block[3] = 0

    def set_block(self, offset, data):
        if not self.all_blocks_full():
            if offset == 0:
                index = 0
            else:
                index = offset / BLOCK_SIZE

            self.blocks[index][2] = data
            self.blocks[index][0] = "Full"

    def get_block(self, block_offset, block_length):
        return self.raw_data[block_offset:block_length]

    def get_empty_block(self):
        if not self.is_full:
            block_index = 0
            for block in self.blocks:
                if block[0] == "Free":
                    block[0] = "Pending"
                    block[3] = int(time.time())
                    return self.piece_index, block_index * BLOCK_SIZE, block[1]
                block_index += 1

        return False

    def all_blocks_full(self):
        for block in self.blocks:
            if block[0] == "Free" or block[0] == "Pending":
                return False
        return True

    def set_to_full(self):
        data = self.merge_blocks()
        if self.hash_is_correct(data):
            self.is_full = True
            self.raw_data = data
            self.write_piece_on_disk()
            pub.sendMessage('PiecesManager.PieceCompleted', piece_index=self.piece_index)

    def write_piece_on_disk(self):
        for file in self.files:
            path_file = file["path"]
            file_offset = file["fileOffset"]
            piece_offset = file["pieceOffset"]
            length = file["length"]

            try:
                f = open(path_file, 'r+b')  # Already existing file
            except IOError:
                f = open(path_file, 'wb')  # New file
            except Exception as e:
                logging.error("Can't write to file : %s" % e.message)
                return

            f.seek(file_offset)
            f.write(self.raw_data[piece_offset:piece_offset + length])
            f.close()

    def merge_blocks(self):
        buf = b""
        for block in self.blocks:
            buf += block[2]
        return buf

    def hash_is_correct(self, piece_raw_data):
        hashed_piece_raw_data = hashlib.sha1(piece_raw_data).digest()
        if hashed_piece_raw_data == self.piece_hash:
            return True
        else:
            logging.warning("Error Piece Hash")
            logging.debug("{} : {}".format(hashed_piece_raw_data, self.piece_hash))
            self.init_blocks()
            return False
