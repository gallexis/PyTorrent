__author__ = 'alexisgallepe'

import socket
import struct


class Peer(object):

    def __init__(self, torrent, port=6881):

        LP = '!IB'  # "Length Prefix" (req'd by protocol)
        self.MESSAGE_TYPES = {
            -1: 'keep_alive',
            0: ('choke', LP, 1),
            1: ('unchoke', LP, 1),
            2: ('interested', LP, 1),
            3: ('not interested', LP, 1),
            4: ('have', LP + 'I', 5),
            # bitfield: Append <bitfield> later. Dynamic length.
            5: ('bitfield', LP),
            6: ('request', LP + 'III', 13),
            # piece: Append <index><begin><block> later. Dynamic length.
            7: ('piece', LP + 'II'),
            8: ('cancel', LP + 'III', 13),
            9: ('port', LP + 'BB', 3)
        }

        self.socket = None
        self.torrent = torrent
        self.handshake = None
        self.socketsPeers = []

    #def run(self):
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
        self.handshake=hs

    def sendToPeer(self, msg):
        self.socket.send(msg)

