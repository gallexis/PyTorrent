__author__ = 'alexisgallepe'

import select
import struct
import random
from threading import Thread
from libs import utils
from pubsub import pub

class PeersManager(Thread):
    def __init__(self, torrent,piecesManager):
        Thread.__init__(self)
        self.peers = []
        self.unchokedPeers = []
        self.torrent = torrent
        self.piecesManager = piecesManager

        # Events
        pub.subscribe(self.addPeer, 'event.newPeer')
        pub.subscribe(self.unchokedPeers.append, 'event.peerUnchoked')

    def run(self):
        while True:
            self.startConnectionToPeers()
            read = [p.socket for p in self.peers]
            readList, _, _ = select.select(read, [], [], 1)

            # Receive from peers
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

    def startConnectionToPeers(self):
        for peer in self.peers:
            if not peer.hasHandshaked:
                try:
                    peer.sendToPeer(peer.handshake)
                    interested = struct.pack('!I', 1) + struct.pack('!B', 2)
                    peer.sendToPeer(interested)
                except:
                    self.removePeer(peer)

    def addPeer(self, peer):
        self.peers.append(peer)

    def removePeer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except:
                pass

            self.peers.remove(peer)

            if peer in self.unchokedPeers:
                self.unchokedPeers.remove(peer)


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

            # handle keep alive
            if peer.keep_alive(peer.readBuffer):
                return

            msgCode = int(ord(peer.readBuffer[4:5]))
            payload = peer.readBuffer[5:4 + msgLength]

            # Message is not complete. Return
            if len(payload) < msgLength - 1:
                print msgLength - 1
                return

            peer.readBuffer = peer.readBuffer[msgLength + 4:]

            try:
                peer.idFunction[msgCode](payload)
            except:
                print "error id:"
                print msgCode
                # erase readBuffer?
                break

    def calculRarestPiece(self):
        sizeBitfield = self.peers[0].numberOfPieces
        bitfields = [0] * sizeBitfield

        for peer in self.peers:
            for i in range(sizeBitfield):
                if self.piecesManager.bitfield[i] == 1:
                    bitfields[i] = ""
                else:
                    bitfields[i] += peer.bitField[i]

        rarestPiece = min(bitfields)  # FILTER + LIST PEERS UNCHOKED ME
        indexOfRarestPiece = bitfields.index(rarestPiece)

        return indexOfRarestPiece

    def requestNewPiece(self,index,offset, length):
        for peer in self.peers:
            if peer.hasPiece(index) and not peer.state['peer_choking']:
                print 'request new piece'
                request = peer.build_request(index, offset, length)
                peer.sendToPeer(request)
                return
