__author__ = 'alexisgallepe'

import socket
import struct


class Peer(object):
    def __init__(self, torrent, port=6881):

        self.handshake = None
        self.hasHanshaked = False
        self.buffer = b""
        self.state = {
            'am_choking': True,
            'am_interested': False,
            'peer_choking': True,
            'peer_interested': False,
        }

        self.message_ID_to_func_name = {
            0: self.choke,
            1: self.unchoke,
            2: self.interested,
            3: self.not_interested,
            4: self.have,
            5: self.bitfield,
            6: self.request,
            7: self.piece,
            8: self.cancel,
            9: self.port
        }

        self.socket = None
        self.torrent = torrent
        self.socketsPeers = []

        # def run(self):
        #self.peerManager()

    def connectToPeer(self, peer, timeout=10):
        ip = peer[0]
        port = peer[1]

        try:
            self.socket = socket.create_connection((ip, port), timeout)
            print "connected to peer ip: {} - port: {}".format(ip, port)
            self.build_handshake()

            return True
        except:
            pass

        return False

    def build_handshake(self):
        """Return formatted message ready for sending to peer:
            handshake: <pstrlen><pstr><reserved><info_hash><peer_id>
        """
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

    def sendToPeer(self, msg):
        self.socket.send(msg)

    def checkHandshake(self, buf, pstr="BitTorrent protocol"):
        if buf[1:20] == pstr:
            handshake = buf[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)

            if self.torrent.info_hash == info_hash:
                self.hasHandshake = True
                print ('handshake', (info_hash, peer_id)), buf
            else:
                print 'error info_hash'
            self.buffer = b""


    def keep_alive(self, message_bytes):
        keep_alive = struct.unpack("!I", message_bytes[:4])[0]
        if keep_alive == 0:
            print('KEEP ALIVE')
            self.buffer = b""
            return True

        return False


    def choke(self, message_bytes):
        self.buffer = b""
        self.state['peer_choking'] = True


    def unchoke(self, message_bytes):
        self.buffer = b""
        self.state['peer_choking'] = False


    def interested(self, message_bytes):
        self.buffer = b""
        self.state['peer_interested'] = True


    def not_interested(self, message_bytes):
        self.buffer = b""
        self.state['peer_interested'] = False


    def have(self, message_bytes):
        '''	Have message is the index of a piece the peer has. Updates
            peer.has_pieces.
        '''
        piece_index = int.from_bytes(message_bytes, byteorder='big')
        self.has_pieces[piece_index] = True
        self.buffer = b""


    def bitfield(self, message_bytes):
        ''' formats each byte into binary and updates peer.has_pieces list
            appropriately.
        '''
        bitstring = ''.join('{0:08b}'.format(byte) for byte in message_bytes)
        self.has_pieces = [bool(int(c)) for c in bitstring]
        # print('PEER HAS PIECES:', self.has_pieces)
        self.torrent.pieces_changed_callback(self)
        self.buffer = b""


    def request(self, message_bytes):
        index = message_bytes[:4]
        piece_offset = message_bytes[4:8]
        length = message_bytes[8:]
        # request: <len=0013><id=6><index><begin><length>
        self.buffer = b""


    def piece(self, message_bytes):
        ''' Piece message is constructed:
            <index><offset><piece bytes>
        '''
        piece_index = message_bytes[:4]
        piece_begins = message_bytes[4:8]
        piece = message_bytes[8:]
        self.torrent.check_piece_callback(piece, piece_index, self)
        self.buffer = b""

        # piece: <len=0009+X><id=7><index><begin><block>,


    def cancel(self, message_bytes):
        self.buffer = b""
        pass
        # cancel: <len=0013><id=8><index><begin><length>,


    def port(self, message_bytes):
        print('HELP! I HAVE A PORT REQUEST!!!!!')
        self.buffer = b""
        pass
        # port: <len=0003><id=9><listen-port>


    def construct_payload(self, message_id):
        self.buffer = b""
        pass


    def construct_message(self, message_id, payload_bytes=b''):
        '''messages in the protocol take the form of
        <length prefix><message ID><payload>. The length prefix is a four byte
        big-endian value. The message ID is a single decimal byte.
        The payload is message dependent.
        '''
        # print('CONSTRUCTING MESSAGE')
        length_bytes = (1 + len(payload_bytes)).to_bytes(4, byteorder='big')
        message_id_bytes = message_id.to_bytes(1, byteorder='big')
        elements = [length_bytes, message_id_bytes, payload_bytes]
        message_bytes = b''.join(elements)
        self.buffer = b""
        return message_bytes