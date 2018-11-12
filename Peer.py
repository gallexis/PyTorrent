__author__ = 'alexisgallepe'

import socket
import struct
import bitstring
from bitstring import BitArray
from pubsub import pub
from libs import utils
import threading
import logging


class Peer(object):
    def __init__(self, torrent, ip, port=6881):

        self.lock = threading.Lock()
        self.handshake = None
        self.has_handshaked = False
        self.read_buffer = b""
        self.counter = 10
        self.socket = None
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.sockets_peers = []

        self.state = {
            'am_choking': True,
            'am_interested': False,
            'peer_choking': True,
            'peer_interested': False,
        }
        self.map_code_to_method = {
            0: self.choke,
            1: self.unchoke,
            2: self.interested,
            3: self.not_interested,
            4: self.have,
            5: self.bitfield,
            6: self.request,
            7: self.piece,
            8: self.cancel,
            9: self.portRequest
        }

        self.number_of_pieces = torrent.number_of_pieces

        self.bit_field = bitstring.BitArray(self.number_of_pieces)

    def connect_to_peer(self, timeout=10):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout)
            logging.info("connected to peer ip: {} - port: {}".format(self.ip, self.port))
            self.build_handshake()

            return True
        except Exception as e:
            logging.error("Failed to connect to peer : %s", e.message)

        return False

    def has_piece(self, index):
        return self.bit_field[index]

    def build_handshake(self):
        pstr = "BitTorrent protocol"
        reserved = "0" * 8
        hs = struct.pack("B" + str(len(pstr)) + "s8x20s20s",
                         len(pstr),
                         pstr,
                         # reserved,
                         self.torrent.info_hash,
                         self.torrent.peer_id
                         )
        assert len(hs) == 49 + len(pstr)
        self.handshake = hs

    def build_interested(self):
        return struct.pack('!I', 1) + struct.pack('!B', 2)

    def build_request(self, index, offset, length):
        header = struct.pack('>I', 13)
        id = '\x06'
        index = struct.pack('>I', index)
        offset = struct.pack('>I', offset)
        length = struct.pack('>I', length)
        request = header + id + index + offset + length

        return request

    def build_piece(self, index, offset, data):
        header = struct.pack('>I', 13)
        id = '\x07'
        index = struct.pack('>I', index)
        offset = struct.pack('>I', offset)
        data = struct.pack('>I', data)
        piece = header + id + index + offset + data

        return piece

    def build_bitfield(self):
        length = struct.pack('>I', 4)
        id = '\x05'
        bitfield = self.bit_field.tobytes()
        bitfield = length + id + bitfield
        return bitfield

    def send_to_peer(self, msg):
        try:
            self.socket.send(msg)
        except:
            logging.error("Failed to send to peer")

    def check_handshake(self, buf, pstr="BitTorrent protocol"):
        if buf[1:20] == pstr:
            handshake = buf[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)

            if self.torrent.info_hash == info_hash:
                self.has_handshaked = True
                self.send_to_peer(self.build_bitfield())
            else:
                logging.warning("Error with peer's handshake")

            self.read_buffer = self.read_buffer[28 + len(info_hash) + 20:]

    def keep_alive(self, payload):
        try:
            keep_alive = struct.unpack("!I", payload[:4])[0]
            if keep_alive == 0:
                logging.info('KEEP ALIVE')
                return True
        except:
            logging.error("Error Keep Alive")
            return False

    def choke(self, payload=None):
        logging.info('choke')
        self.state['peer_choking'] = True

    def unchoke(self, payload=None):
        logging.info('unchoke')
        pub.sendMessage('PeersManager.peerUnchoked', peer=self)
        self.state['peer_choking'] = False

    def interested(self, payload=None):
        logging.info('interested')
        self.state['peer_interested'] = True

    def not_interested(self, payload=None):
        logging.info('not_interested')
        self.state['peer_interested'] = False

    def have(self, payload):
        index = utils.bytes_to_decimal(payload)
        self.bit_field[index] = True
        pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field, peer=self)

    def bitfield(self, payload):
        self.bit_field = BitArray(bytes=payload)
        logging.info('request')
        pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field, peer=self)

    def request(self, payload):
        piece_index = payload[:4]
        block_offset = payload[4:8]
        block_length = payload[8:]
        logging.info('request')
        pub.sendMessage('PiecesManager.PeerRequestsPiece', piece=(piece_index, block_offset, block_length), peer=self)

    def piece(self, payload):
        piece_index = utils.bytes_to_decimal(payload[:4])
        piece_offset = utils.bytes_to_decimal(payload[4:8])
        piece_data = payload[8:]
        pub.sendMessage('PiecesManager.Piece', piece=(piece_index, piece_offset, piece_data))

    def cancel(self, payload=None):
        logging.info('cancel')

    def portRequest(self, payload=None):
        logging.info('portRequest')
