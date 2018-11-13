import hashlib

__author__ = 'alexisgallepe'

import time
import bencode
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
        with open(path, 'r') as file:
            contents = file.read()

        self.torrent_file = bencode.bdecode(contents)
        self.piece_length = self.torrent_file['info']['piece length']
        self.pieces = self.torrent_file['info']['pieces']
        raw_info_hash = str(bencode.bencode(self.torrent_file['info']))
        self.info_hash = hashlib.sha1(raw_info_hash).digest()
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
        root = self.torrent_file['info']['name']

        if 'files' in self.torrent_file['info']:
            if not os.path.exists(root):
                os.mkdir(root, 0766 )

            for file in self.torrent_file['info']['files']:
                path_file = os.path.join(root, *file["path"])

                if not os.path.exists(os.path.dirname(path_file)):
                    os.makedirs(os.path.dirname(path_file))

                self.file_names.append({"path": path_file , "length": file["length"]})
                self.total_length += file["length"]

        else:
            self.file_names.append({"path": root , "length": self.torrent_file['info']['length']})
            self.total_length = self.torrent_file['info']['length']

    def get_trakers(self):
        if 'announce-list' in self.torrent_file:
            return self.torrent_file['announce-list']
        else:
            return [[self.torrent_file['announce']]]

    def generate_peer_id(self):
        seed = str(time.time())
        return hashlib.sha1(seed).digest()
