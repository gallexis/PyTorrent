__author__ = 'alexisgallepe'

import hashlib
import time
import bencodepy
import logging
import os


class Torrent(object):
    def __init__(self):
        self.torrent_file = {}
        self.total_length = 0
        self.piece_length = 0
        self.pieces = 0
        self.info_hash = ""
        self.peer_id = ""
        self.announce_list = ""
        self.file_names = []
        self.number_of_pieces = 0

    def load_from_path(self, path):
        with open(path, 'rb') as file:
            contents = file.read()

        self.torrent_file = dict(bencodepy.decode(contents))
        self.piece_length = self.torrent_file[b'info'][b'piece length']
        self.pieces = self.torrent_file[b'info'][b'pieces']
        raw_info_hash = str(bencodepy.encode(self.torrent_file[b'info']))
        self.info_hash = hashlib.sha1(raw_info_hash.encode('utf-8')).digest()
        self.peer_id = self.generate_peer_id()
        self.announce_list = self.get_trakers()

        self.init_files()

        if self.total_length % self.piece_length == 0:
            self.number_of_pieces = self.total_length / self.piece_length
        else:
            self.number_of_pieces = (self.total_length / self.piece_length) + 1

        logging.debug(self.announce_list)
        logging.debug(self.file_names)

        assert(self.total_length > 0)
        assert(len(self.file_names) > 0)

        return self

    def init_files(self):
        root = self.torrent_file[b'info'][b'name']

        if 'files' in self.torrent_file[b'info']:
            if not os.path.exists(root):
                os.mkdir(root, 0o0766 )

            for file in self.torrent_file[b'info'][b'files']:
                path_file = os.path.join(root, *file["path"])

                if not os.path.exists(os.path.dirname(path_file)):
                    os.makedirs(os.path.dirname(path_file))

                self.file_names.append({"path": path_file , "length": file["length"]})
                self.total_length += file["length"]

        else:
            self.file_names.append({"path": root , "length": self.torrent_file[b'info'][b'length']})
            self.total_length = self.torrent_file[b'info'][b'length']

    def get_trakers(self):
        if 'announce-list' in self.torrent_file:
            return self.torrent_file['announce-list']
        else:
            return [[self.torrent_file[b'announce']]]

    def generate_peer_id(self):
        seed = str(time.time())
        return hashlib.sha1(seed.encode('utf-8')).digest()
