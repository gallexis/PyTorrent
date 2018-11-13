__author__ = 'alexisgallepe'

import socket
import struct
import bitstring
from bitstring import BitArray
from pubsub import pub
import logging


class Peer(object):
    def __init__(self, torrent, ip, port=6881):
        self.handshake = None
        self.has_handshaked = False
        self.read_buffer = b''
        self.counter = 10
        self.socket = None
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.sockets_peers = []
        self.number_of_pieces = torrent.number_of_pieces
        self.bit_field = bitstring.BitArray(torrent.number_of_pieces)
        self.state = {
            'am_choking': True,
            'am_interested': False,
            'peer_choking': True,
            'peer_interested': False,
        }
        self.map_code_to_handlers = {
            0: self.handle_choke,
            1: self.handle_unchoke,
            2: self.handle_interested,
            3: self.handle_not_interested,
            4: self.handle_have,
            5: self.handle_bitfield,
            6: self.handle_request,
            7: self.handle_piece,
            8: self.handle_cancel,
            9: self.handle_port_request
        }

    def is_choking(self):
        return self.state['peer_choking']

    def connect_to_peer(self, timeout=10):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout)
            logging.info("Connected to peer ip: {} - port: {}".format(self.ip, self.port))
            return True

        except Exception as e:
            pass
            #ogging.error("Failed to connect to peer : %s" % e.message)

        return False

    def send_to_peer(self, msg):
        try:
            self.socket.send(msg)
        except Exception as e:
            logging.error("Failed to send to peer : %s" % e.message)

    def has_piece(self, index):
        return self.bit_field[index]

    def build_handshake(self):
        """<pstrlen><pstr><reserved><info_hash><peer_id>"""
        pstr = b'BitTorrent protocol'
        pstr_len = len(pstr)
        fmt = '!B%ds8x20s20s' % pstr_len
        handshake = struct.pack(fmt, pstr_len, pstr, self.torrent.info_hash, self.torrent.peer_id)

        return handshake

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

    def check_handshake(self, buffer):
        pstr = "BitTorrent protocol"

        if buffer[1:20] == pstr:
            handshake = buffer[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)

            if self.torrent.info_hash == info_hash:
                self.has_handshaked = True
                logging.info('has_handshaked')
            else:
                logging.warning("Error with peer's handshake")

            self.read_buffer = self.read_buffer[28 + len(info_hash) + 20:]

    def is_keep_alive(self, payload):
        try:
            keep_alive = struct.unpack("!I", payload[:4])[0]
            if keep_alive == 0:
                logging.info('Handle KeepAlive')
                return True

        except Exception as e:
            logging.error("Error KeepAlive : %s" % e.message)
            return False

    def handle_choke(self, payload=None):
        logging.info('peer_choking')
        self.state['peer_choking'] = True

    def handle_unchoke(self, payload=None):
        logging.info('unchoke')
        self.state['peer_choking'] = False

    def handle_interested(self, payload=None):
        logging.info('interested')
        self.state['peer_interested'] = True

    def handle_not_interested(self, payload=None):
        logging.info('not_interested')
        self.state['peer_interested'] = False

    def handle_have(self, payload):
        index = struct.unpack('!I', payload)[0]
        self.bit_field[index] = True
        pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field, peer=self)

    def handle_bitfield(self, payload):
        self.bit_field = BitArray(bytes=payload)
        logging.info('request')
        pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field, peer=self)

    def handle_request(self, payload):
        piece_index = payload[:4]
        block_offset = payload[4:8]
        block_length = payload[8:]
        logging.info('request from client')

        #TODO : pub.sendMessage('PiecesManager.PeerRequestsPiece', piece=(piece_index, block_offset, block_length), peer=self)

    def handle_piece(self, payload):
        piece_index = struct.unpack('!I', payload[:4])[0]
        piece_offset = struct.unpack('!I', payload[4:8])[0]
        piece_data = payload[8:]
        pub.sendMessage('PiecesManager.Piece', piece=(piece_index, piece_offset, piece_data))
        logging.info('Receive new Piece : %s', str((piece_index, piece_offset, piece_data)))

    def handle_cancel(self, payload=None):
        logging.info('cancel')

    def handle_port_request(self, payload=None):
        logging.info('portRequest')

    def send_piece(self, piece_index, block_offset, data):
        piece = self.build_piece(piece_index, block_offset, data)
        self.send_to_peer(piece)
        logging.info("Sent : send_new_piece (%s)" % str((piece_index, block_offset, len(data))))
