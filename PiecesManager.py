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
        self.is_full = False
        self.number_of_pieces = torrent.number_of_pieces
        self.bitfield = bitstring.BitArray(self.number_of_pieces)
        self.pieces = self.generate_pieces()
        self.files = self.get_files()

        for file in self.files:
            id_piece = file['idPiece']
            self.pieces[id_piece].files.append(file)

        # Create events
        pub.subscribe(self.receive_block_piece, 'PiecesManager.Piece')
        pub.subscribe(self.update_bitfield, 'PiecesManager.PieceCompleted')

    def update_bitfield(self, piece_index):
        self.bitfield[piece_index] = 1

    def receive_block_piece(self, piece):
        piece_index, piece_offset, piece_data = piece
        self.pieces[int(piece_index)].set_block(piece_offset, piece_data)

    def generate_pieces(self):
        pieces = []

        for i in range(self.number_of_pieces):
            start = i * 20
            end = start + 20

            if i == (self.number_of_pieces - 1):
                piece_length = self.torrent.total_length - (self.number_of_pieces - 1) * self.torrent.piece_length
                pieces.append(Piece.Piece(i, piece_length, self.torrent.pieces[start:end]))
            else:
                pieces.append(Piece.Piece(i, self.torrent.piece_length, self.torrent.pieces[start:end]))
        return pieces

    def pieces_full(self):
        for piece in self.pieces:
            if not piece.is_full:
                return False

        self.is_full = True
        logging.info("File(s) downloaded successfully.")
        return True

    def get_files(self):
        files = []
        piece_offset = 0
        piece_size_used = 0

        for f in self.torrent.file_names:
            current_size_file = f["length"]
            file_offset = 0

            while current_size_file > 0:
                id_piece = piece_offset / self.torrent.piece_length
                piece_size = self.pieces[id_piece].piece_size - piece_size_used

                if current_size_file - piece_size < 0:
                    file = {"length": current_size_file, "idPiece": id_piece, "fileOffset": file_offset,
                            "pieceOffset": piece_size_used, "path": f["path"]}
                    piece_offset += current_size_file
                    file_offset += current_size_file
                    piece_size_used += current_size_file
                    current_size_file = 0

                else:
                    current_size_file -= piece_size
                    file = {"length": piece_size, "idPiece": id_piece, "fileOffset": file_offset,
                            "pieceOffset": piece_size_used, "path": f["path"]}
                    piece_offset += piece_size
                    file_offset += piece_size
                    piece_size_used = 0

                files.append(file)
        return files

    def get_block(self, piece_index, block_offset, block_length):
        for piece in self.pieces:
            if piece_index == piece.piece_index:
                if piece.is_full:
                    return piece.get_block(block_offset, block_length)
                else:
                    break

        return None
