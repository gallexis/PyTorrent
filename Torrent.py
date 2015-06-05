__author__ = 'alexisgallepe'

import time

import bencode

from libs.utils import sha1_hash


class Torrent(object):
    def __init__(self, path):
        with open(path, 'r') as f:
            contents = f.read()
        self.torrentFile = bencode.bdecode(contents)

        self.names = []

        root = self.torrentFile['info']['name']

        if 'files' in self.torrentFile['info']:
            for file in self.torrentFile['files']:
                self.names.append(root+'/'+file['path'])

        else:
            self.names.append(root)

        print self.names

        if 'announce-list' in self.torrentFile:
            self.announceList = self.torrentFile['announce-list']
        else:
            self.announceList = [[self.torrentFile['announce']]]


        self.length = self.torrentFile['info']['length']
        self.pieceLength = self.torrentFile['info']['piece length']
        self.pieces = self.torrentFile['info']['pieces']
        self.info_hash = sha1_hash(str(
            bencode.bencode(self.torrentFile['info'])
        ))
        self.peer_id = self.generatePeerId()

    def generatePeerId(self):
        seed = str(time.time())
        return sha1_hash(seed)

