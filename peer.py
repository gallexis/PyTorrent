__author__ = 'alexisgallepe'

import socket
import struct
import bitstring
from pubsub import pub
import logging

import message


class Peer(object):
    def __init__(self, torrent, ip, port=6881):
        self.has_handshaked = False
        self.to_remove = False
        self.read_buffer = b''
        self.socket = None
        self.ip = ip
        self.port = port
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

    def connect(self):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout=5)
            self.socket.setblocking(False)
            logging.info("Connected to peer ip: {} - port: {}".format(self.ip, self.port))
            return True

        except Exception as e:
            logging.error("Failed to connect to peer : %s" % e.message)

        return False

    def send_to_peer(self, msg):
        try:
            if not self.to_remove:
                self.socket.send(msg)
        except Exception as e:
            self.to_remove = True
            logging.error("Failed to send to peer : %s" % e.message)

    def has_piece(self, index):
        return self.bit_field[index]

    def am_choking(self):
        return self.state['am_choking']

    def am_unchoking(self):
        return not self.am_choking()

    def is_choking(self):
        return self.state['peer_choking']

    def is_unchoked(self):
        return not self.is_choking()

    def is_interested(self):
        return self.state['peer_interested']

    def am_interested(self):
        return self.state['am_interested']

    def handle_choke(self):
        logging.debug('handle_choke - %s' % self.ip)
        self.state['peer_choking'] = True

    def handle_unchoke(self):
        logging.debug('handle_unchoke - %s' % self.ip)
        self.state['peer_choking'] = False

    def handle_interested(self):
        logging.debug('handle_interested - %s' % self.ip)
        self.state['peer_interested'] = True

        if self.am_choking():
            unchoke = message.UnChoke().to_bytes()
            self.send_to_peer(unchoke)

    def handle_not_interested(self):
        logging.debug('handle_not_interested - %s' % self.ip)
        self.state['peer_interested'] = False

    def handle_have(self, have):
        """
        :type have: message.Have
        """
        logging.debug('handle_have - %s' % self.ip)
        self.bit_field[have.piece_index] = True

        if self.is_choking():
            interested = message.Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

        # pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field)

    def handle_bitfield(self, bitfield):
        """
        :type bitfield: message.BitField
        """
        logging.debug('handle_bitfield - %s' % self.ip)
        self.bit_field = bitfield.bitfield

        if self.is_choking():
            interested = message.Interested().to_bytes()
            self.send_to_peer(interested)
            self.state['am_interested'] = True

        # pub.sendMessage('RarestPiece.updatePeersBitfield', bitfield=self.bit_field)

    def handle_request(self, request):
        """
        :type request: message.Request
        """
        logging.debug('handle_request - %s' % self.ip)
        if self.is_interested() and self.is_unchoked():
            pub.sendMessage('PiecesManager.PeerRequestsPiece', request=request, peer=self)

    def handle_piece(self, message):
        """
        :type message: message.Piece
        """
        logging.debug('handle_piece - %s' % self.ip)
        pub.sendMessage('PiecesManager.Piece', piece=(message.piece_index, message.block_offset, message.block))

    def handle_cancel(self):
        logging.debug('handle_cancel - %s' % self.ip)

    def handle_port_request(self):
        logging.debug('handle_port_request - %s' % self.ip)

    def _handle_handshake(self):
        try:
            handshake_message = message.Handshake.from_bytes(self.read_buffer)
            self.has_handshaked = True
            self.read_buffer = self.read_buffer[handshake_message.total_length:]
            logging.debug('handle_handshake - %s' % self.ip)
            return True

        except Exception as e:
            logging.error("First message should always be an handshake message : %s" % e.message)
            self.to_remove = True

        return False

    def _handle_keep_alive(self):
        try:
            keep_alive = message.KeepAlive.from_bytes(self.read_buffer)
            logging.debug('handle_keep_alive - %s' % self.ip)
        except message.WrongMessageException:
            return False
        except Exception as e:
            logging.error("Error KeepALive, (need at least 4 bytes : {}) - {}".format(len(self.read_buffer), e.message))
            return False

        self.read_buffer = self.read_buffer[keep_alive.total_length:]
        return True

    def get_messages(self):
        while len(self.read_buffer) > 4 and not self.to_remove:
            if (not self.has_handshaked and self._handle_handshake()) or self._handle_keep_alive():
                continue

            payload_length, = struct.unpack(">I", self.read_buffer[:4])
            total_length = payload_length + 4

            if len(self.read_buffer) < total_length:
                break
            else:
                payload = self.read_buffer[:total_length]
                self.read_buffer = self.read_buffer[total_length:]

            try:
                yield message.MessageDispatcher(payload).dispatch()
            except message.WrongMessageException as e:
                logging.error(e.message)
