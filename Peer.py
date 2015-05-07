__author__ = 'alexisgallepe'

import socket
import struct
import select


class Peer(object):
    def __init__(self, torrent, sock, port=6881):

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

        self.socket = sock
        self.torrent = torrent
        self.socketsPeers = []

        self.socketRec = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        # self.socketRec.bind(('localhost', port))
        #self.socketRec.listen(5)

    def connectToPeer(self, peer, timeout=3):
        ip = peer[0]
        port = peer[1]

        try:
            peerConnection = socket.create_connection((ip, port), timeout)
            print "connected to peer ip: {} - port: {}".format(ip, port)
            return peerConnection
        except:
            pass

    def build_handshake(self):
        """Return formatted message ready for sending to peer:
            handshake: <pstrlen><pstr><reserved><info_hash><peer_id>
        """
        pstr = "BitTorrent protocol"
        reserved = "0" * 8
        handshake = struct.pack("B" + str(len(pstr)) + "s8x20s20s",
                                len(pstr),
                                pstr,
                                # reserved,
                                self.torrent.info_hash,
                                self.torrent.peer_id
                                )
        assert len(handshake) == 49 + len(pstr)
        return handshake

    def sendToPeer(self, socket, msg):
        socket.send(msg)

    def recv_msg(self):
        pass
"""
    def recv_msg(self):
        buf = ""
        peers = []

        while True:
            try:
                peers, wlist, xlist = select.select(self.socketsPeers, [], [], 0.05)
            except Exception, e:
                print e
                break
                pass
            else:
                for peer in peers:
                    # thread managePeer
                    try:
                        msg = peer.recv(4096)
                    except Exception, e:
                        # print "error rec message peer" #if timeout, not an error
                        # self.socket.close()
                        print e
                        break
                    else:
                        if len(msg) == 0: break
                        buf += msg

                    if len(msg) > 0:
                        print self.decodeMessagePeer(buf)
                        # return buf
"""
    def decodeMessagePeer(self, buf, pstr="BitTorrent protocol"):
        if buf[1:20] == pstr:  # Received handshake
            handshake = buf[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)
            buf = buf[68:]

            if self.torrent.info_hash == info_hash:
                interested = struct.pack('!I', 1) + struct.pack('!B', 2)
                self.sendToPeer(interested)
                return ('handshake', (info_hash, peer_id)), buf
            else:
                return 'error info_hash'

        if len(buf) < 4:
            raise Exception("Too few bytes to form a protocol message.")

        length = struct.unpack('!I', buf[:4])[0]
        if length == 0:
            type = 'keep alive'
            buf = buf[4:]
        else:  # data type anything but 'keep alive'
            print "Trying to parse data"
            type = self.MESSAGE_TYPES[ord(buf[4])]
            print(type)

        return buf

