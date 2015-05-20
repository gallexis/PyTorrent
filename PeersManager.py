__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread


class PeersManager(Thread):
    def __init__(self, torrent):
        Thread.__init__(self)
        self.peers = []
        self.torrent = torrent

    def run(self):

        while True:
            self.startConnectionToPeers()
            read = [p.socket for p in self.peers]
            readList, _, _ = select.select(read, [], [], 2)

            for socket in readList:          # !! socket != peer !!
                try:
                    peer = self.getPeerBySocket(socket)
                    msg = socket.recv(1024)
                except Exception, e:
                    print e
                    self.removePeer(peer)
                    continue

                if len(msg) == 0:
                    self.removePeer(peer)
                    continue

                peer.receiveBuffer += msg
                self.manageMessageReceived(peer)

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
        while len(peer.receiveBuffer) > 3:
            if peer.hasHandshaked == False:
                peer.checkHandshake(peer.receiveBuffer)
                return

            msgLength = self.convertBytesToDecimal(peer.receiveBuffer[0:4], 3)

            if len(peer.receiveBuffer) == 4:
                if msgLength == '\x00\x00\x00\x00':
                    print 'Keep alive'
                    return True
                print 'Keep alive2'
                return True

            msgCode = int(ord(peer.receiveBuffer[4:5]))
            payload = peer.receiveBuffer[5:4 + msgLength]

            if len(payload) < msgLength - 1:
                # Message is not complete. Return
                print msgLength - 1
                return True

            peer.receiveBuffer = peer.receiveBuffer[msgLength + 4:]

            if not msgCode:
                # Keep Alive. Keep the connection alive.
                print 'ka'
                continue

            elif msgCode == 0:
                # Choked
                # peer.choke()
                print 'chok'
                continue

            elif msgCode == 1:
                # peer.unchoke()
                #pipeRequests(peer, peerMngr)
                print 'unch'
                continue

            elif msgCode == 4:
                # handleHave(peer, payload)
                print "have"
                continue

            elif msgCode == 5:
                # peer.setBitField(payload)
                print "bitfield"
                continue

            elif msgCode == 7:
                # Piece
                print "piece"
                continue

            elif msgCode == 8:
                # Cancel
                print "Cancel"
                continue

            elif msgCode == 9:
                # Port
                print "port"
                continue

            else:
                print "else"
                return


    def convertBytesToDecimal(self, headerBytes, power):
        size = 0
        for ch in headerBytes:
            size += int(ord(ch)) * 256 ** power
            power -= 1
        return size