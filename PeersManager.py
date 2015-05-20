__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread
from libs import utils

class PeersManager(Thread):
    def __init__(self, torrent):
        Thread.__init__(self)
        self.peers = []
        self.torrent = torrent

    def run(self):
        while True:
            self.startConnectionToPeers()
            read = [p.socket for p in self.peers]
            write = [p.socket for p in self.peers if p.writeBuffer != ""]
            readList, writeList, _ = select.select(read, write, [], 2)

            for socket in readList:
                peer = self.getPeerBySocket(socket)
                try:
                    msg = socket.recv(1024)
                except:
                    self.removePeer(peer)
                    continue

                if len(msg) == 0:
                    self.removePeer(peer)
                    continue

                peer.readBuffer += msg
                self.manageMessageReceived(peer)

            for socket in writeList:
                peer = self.getPeerBySocket(socket)
                try:
                    peer.sendToPeer(peer.writeBuffer)
                except:
                    self.removePeer(peer)
                    continue

    def startConnectionToPeers(self):
        for peer in self.peers:
            if not peer.hasHandshaked:
                try:
                    peer.sendToPeer(peer.handshake)
                    interested = struct.pack('!I', 1) + struct.pack('!B', 2)
                    peer.sendToPeer(interested)
                except:
                    print 'err startConnectionToPeers'
                    self.removePeer(peer)

    def addPeer(self, peer):
        print "addPeer"
        self.peers.append(peer)

    def removePeer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except:
                pass

            self.peers.remove(peer)
            print "peer removed"

    def getPeerBySocket(self,socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

        raise("peer not present in PeerList")


    def manageMessageReceived(self, peer):
        while len(peer.readBuffer) > 3:
            if peer.hasHandshaked == False:
                peer.checkHandshake(peer.readBuffer)
                return

            msgLength = utils.convertBytesToDecimal(peer.readBuffer[0:4], 3)

            if len(peer.readBuffer) == 4:
                if msgLength == '\x00\x00\x00\x00':
                    print 'Keep alive'
                    return True
                print 'Keep alive2'
                return True

            msgCode = int(ord(peer.readBuffer[4:5]))
            payload = peer.readBuffer[5:4 + msgLength]

            if len(payload) < msgLength - 1:
                # Message is not complete. Return
                print msgLength - 1
                return True

            peer.readBuffer = peer.readBuffer[msgLength + 4:]

            if not msgCode:
                # Keep Alive. Keep the connection alive.
                print 'ka'

            elif msgCode == 0:
                peer.choke()

            elif msgCode == 1:
                peer.unchoke()

            elif msgCode == 4:
                peer.have(payload)

            elif msgCode == 5:
                peer.bitfield(payload)

            elif msgCode == 7:
                peer.piece(payload)

            elif msgCode == 8:
                peer.cancel(payload)

            elif msgCode == 9:
                peer.port(payload)

            else:
                print "else"
                return