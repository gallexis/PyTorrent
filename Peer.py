__author__ = 'alexisgallepe'

import socket
import struct


class Peer(object):
    def __init__(self, torrent,ip, port=6881):

        self.handshake = None
        self.hasHandshaked = False
        self.readBuffer = b""
        self.writeBuffer = b""
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
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.socketsPeers = []

        # def run(self):
        #self.peerManager()

    def connectToPeer(self, timeout=10):
        try:
            self.socket = socket.create_connection((self.ip, self.port), timeout)
            print "connected to peer ip: {} - port: {}".format(self.ip, self.port)
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
                self.hasHandshaked = True
                print ('handshake', (info_hash, peer_id)), buf
            else:
                print 'error info_hash'

            self.readBuffer = self.readBuffer[28 +len(info_hash)+20:]
                                                     # HEADER_SIZE

    def keep_alive(self, message_bytes):
        keep_alive = struct.unpack("!I", message_bytes[:4])[0]
        if keep_alive == 0:
            print('KEEP ALIVE')


    def choke(self):
        print "choke"
        self.state['peer_choking'] = True


    def unchoke(self):
        print "unchoke"
        self.state['peer_choking'] = False

    def interested(self):
        print "interested"
        self.state['peer_interested'] = True

    def not_interested(self):
        print "not interested"
        self.state['peer_interested'] = False

    def have(self, message_bytes):
        '''	Have message is the index of a piece the peer has. Updates
            peer.has_pieces.
        '''
        #self.has_pieces[piece_index] = True
        print "have"
        pass


    def bitfield(self, message_bytes):
        ''' formats each byte into binary and updates peer.has_pieces list
            appropriately.
        '''
        print "bitfield"
        pass


    def request(self, message_bytes):
        index = message_bytes[:4]
        piece_offset = message_bytes[4:8]
        length = message_bytes[8:]
        print "request"
        # request: <len=0013><id=6><index><begin><length>
        pass


    def piece(self, message_bytes):
        ''' Piece message is constructed:
            <index><offset><piece bytes>
        '''
        piece_index = message_bytes[:4]
        piece_begins = message_bytes[4:8]
        piece = message_bytes[8:]
        print "piece"
        pass

        # piece: <len=0009+X><id=7><index><begin><block>,


    def cancel(self, message_bytes):
        print "cancel"
        pass
        # cancel: <len=0013><id=8><index><begin><length>,


    def port(self, message_bytes):
        print('HELP! I HAVE A PORT REQUEST!!!!!')
        pass
        # port: <len=0003><id=9><listen-port>
