__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread
from libs import utils
from pubsub import pub
import RarestPieces
import logging

class PeersManager(Thread):
    def __init__(self, torrent,piecesManager):
        Thread.__init__(self)
        self.peers = []
        self.unchokedPeers = []
        self.torrent = torrent
        self.piecesManager = piecesManager
        self.rarestPieces = RarestPieces.RarestPieces(piecesManager)

        self.piecesByPeer = []
        for i in range(self.piecesManager.numberOfPieces):
            self.piecesByPeer.append([0,[]])

        # Events
        pub.subscribe(self.addPeer, 'event.newPeer')
        pub.subscribe(self.addUnchokedPeer, 'event.peerUnchoked')
        pub.subscribe(self.peersBitfield, 'event.updatePeersBitfield')

    def peersBitfield(self,bitfield=None,peer=None,pieceIndex=None):
        if not pieceIndex == None:
            self.piecesByPeer[pieceIndex] = ["",[]]
            return

        for i in range(len(self.piecesByPeer)):
            if bitfield[i] == 1 and peer not in self.piecesByPeer[i][1] and not self.piecesByPeer[i][0] == "":
                self.piecesByPeer[i][1].append(peer)
                self.piecesByPeer[i][0] = len(self.piecesByPeer[i][1])

    def getUnchokedPeer(self,index):
        for peer in self.unchokedPeers:
            if peer.getCounter() > 0 and peer.hasPiece(index):
                return peer

        return False

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

        for rarestPiece in self.rarestPieces.rarestPieces:
            if peer in rarestPiece["peers"]:
                rarestPiece["peers"].remove(peer)


    def getPeerBySocket(self,socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

        raise("peer not present in PeerList")

    def manageMessageReceived(self, peer):
        while len(peer.readBuffer) > 0:
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
            except Exception as e:
                logging.info(e)
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

    def incAllPeersCounter(self):
        for peer in self.unchokedPeers:
            peer.incCounter()


    def requestNewPiece(self,peer, pieceIndex,offset, length):

        if peer.getCounter() > 0:
            request = peer.build_request(pieceIndex, offset, length)
            peer.sendToPeer(request)
            return True
        else:
            return False