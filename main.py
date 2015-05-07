__author__ = 'alexisgallepe'

#!/usr/local/bin/python

import bencode
import hashlib
import time
import requests
import socket
import struct
import select
import sys

def sha1_hash(string):
    """Return 20-byte sha1 hash of string.
    """
    return hashlib.sha1(string).digest()


class Torrent(object):
    def __init__(self, path):
        with open(path, 'r') as f:
            contents = f.read()
        self.torrentFile = bencode.bdecode(contents)

        self.announceList = self.torrentFile['announce-list']
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


class Tracker(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.peers=[]

    def getPeersFromTrackers(self):
        for tracker in self.torrent.announceList:
            try:
                if tracker[0][:4] == "http":
                    self.getPeersFromTracker(tracker[0])
            except:
                pass

        if len(self.peers)<=0: print "Error, no peer available"
        return self.peers

    def getPeersFromTracker(self, tracker):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.torrent.peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent.length,
            'event': 'started'
        }
        answerTracker = requests.get(tracker, params=params, timeout=3)
        lstPeers = bencode.bdecode(answerTracker.text)
        self.parseTrackerResponse(lstPeers['peers'])


    def parseTrackerResponse(self, peersByte):
        raw_bytes = [ord(c) for c in peersByte]
        for i in range(len(raw_bytes) / 6):
            start = i * 6
            end = start + 6
            ip = ".".join(str(i) for i in raw_bytes[start:end - 2])
            port = raw_bytes[end - 2:end]
            port = port[1] + port[0] * 256
            self.peers.append([ip, port])


class Peers(object):
    def __init__(self, torrent,port=6881):

        LP = '!IB' # "Length Prefix" (req'd by protocol)
        MESSAGE_TYPES = {
            -1: 'keep_alive',
            0: ('choke', LP, 1),
            1: ('unchoke', LP, 1),
            2: ('interested', LP, 1),
            3: ('not interested', LP, 1),
            4: ('have', LP+'I', 5),
            # bitfield: Append <bitfield> later. Dynamic length.
            5: ('bitfield', LP),
            6: ('request', LP+'III', 13),
            # piece: Append <index><begin><block> later. Dynamic length.
            7: ('piece', LP+'II'),
            8: ('cancel', LP+'III', 13),
            9: ('port', LP+'BB', 3)
        }

        self.torrent=torrent
        self.socketsPeers=[]

        self.socketRec = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        #self.socketRec.bind(('localhost', port))
        #self.socketRec.listen(5)

    def connectToPeer(self, peer, timeout=3):
        ip = peer[0]
        port = peer[1]

        try:
            peerConnection = socket.create_connection((ip, port), timeout)
            self.socketsPeers.append(peerConnection)
            print "connected to peer ip: {} - port: {}".format(ip, port)
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
        buf = ""
        peers = []

        while True:
            try:
                peers, wlist, xlist = select.select(self.socketsPeers,[], [], 0.05)
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
                    #return buf

    def decodeMessagePeer(self, buf, pstr="BitTorrent protocol"):
        if buf[1:20] == pstr:  # Received handshake
            handshake = buf[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)
            buf = buf[68:]
            if self.torrent.info_hash == info_hash:
                return ('handshake', (info_hash, peer_id)), buf
            else:
                return 'error info_hash'

        if len(buf) < 4:
            raise Exception("Too few bytes to form a protocol message.")

        print ":"+buf
        a = struct.unpack("!I", buf[4])
        return a



def main():

    t = Torrent("w.torrent")
    tk = Tracker(t)

    peers = tk.getPeersFromTrackers()
    print "get peers from tracker"

    p = Peers(t)
    peers = peers[:8]
    for peer in peers:
        p.connectToPeer(peer)

    print "creating handshake"
    handshake = p.build_handshake()

    for sockPeer in p.socketsPeers:
        p.sendToPeer(sockPeer,handshake)
        print "handshake sent"

    p.recv_msg()
    p.socket.close()


if __name__ == '__main__':
    main()
