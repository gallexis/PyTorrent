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

        self.piecesByPeer = []
        for i in range(self.piecesManager.numberOfPieces):
            self.piecesByPeer.append([0,[]])

        # Events
        pub.subscribe(self.addPeer, 'event.newPeer')
        pub.subscribe(self.addUnchokedPeer, 'event.peerUnchoked')
        pub.subscribe(self.peersBitfield, 'event.updatePeersBitfield')

    def peersBitfield(self,bitfield=None,peer=None,pieceIndex=None):
        if not pieceIndex == None:
            #print 'pieceIndex: ',pieceIndex
            self.piecesByPeer[pieceIndex] = ["",[]]
            return

        for i in range(len(self.piecesByPeer)):
            if bitfield[i] == 1 and peer not in self.piecesByPeer[i][1] and not self.piecesByPeer[i][0] == "":
                self.piecesByPeer[i][1].append(peer)
                self.piecesByPeer[i][0] = len(self.piecesByPeer[i][1])

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

    def addUnchokedPeer(self, peer):
        self.unchokedPeers.append(peer)

    def removePeer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except:
                pass

            self.peers.remove(peer)

            if peer in self.unchokedPeers:
                self.unchokedPeers.remove(peer)

            for i in range(len(self.piecesByPeer)):
                if peer in self.piecesByPeer[i][1]:
                    self.piecesByPeer[i][1].remove(peer)


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

            msgLength = utils.convertBytesToDecimal(peer.readBuffer[0:4])

            # handle keep alive
            if peer.keep_alive(peer.readBuffer):
                return

            #len 0
            try:
                msgCode = int(ord(peer.readBuffer[4:5]))
                payload = peer.readBuffer[5:4 + msgLength]
            except Exception, e:
                print e
                return

            # Message is not complete. Return
            if len(payload) < msgLength - 1:
                return

            peer.readBuffer = peer.readBuffer[msgLength + 4:]

            peer.idFunction[msgCode](payload)

            """
            try:
                peer.idFunction[msgCode](payload)
            except Exception, e:
                print "error id:", msgCode," ->", e
                return
            """


    def requestNewPiece(self,index,offset, length):
        """
        numberOfPeers = len(self.piecesByPeer[index][1])
        peer = self.piecesByPeer[index][1][random.randrange(0,numberOfPeers)]

        request = peer.build_request(index, offset, length)
        peer.sendToPeer(request)
        return
        """
        for peer in self.unchokedPeers:
            if peer.hasPiece(index):
                request = peer.build_request(index, offset, length)
                peer.sendToPeer(request)
                return
        """
        while True:
            numPeer = random.randrange(0,len(self.unchokedPeers))
            peer = self.unchokedPeers[numPeer]
            if peer.hasPiece(index):
                request = peer.build_request(index, offset, length)
                peer.sendToPeer(request)
                return
        """
