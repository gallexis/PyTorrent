__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread
from libs import utils
from pubsub import pub
import RarestPieces
import logging


class PeersManager(Thread):
    def __init__(self, torrent, pieces_manager):
        Thread.__init__(self)
        self.peers = []
        self.unchoked_peers = []
        self.torrent = torrent
        self.pieces_manager = pieces_manager
        self.rarest_pieces = RarestPieces.RarestPieces(pieces_manager)
        self.pieces_by_peer = [[0, []] for _ in range(self.pieces_manager.number_of_pieces)]

        # Events
        pub.subscribe(self.add_peer, 'PeersManager.newPeer')
        pub.subscribe(self.add_unchoked_peer, 'PeersManager.peerUnchoked')
        pub.subscribe(self.handle_peer_requests, 'PeersManager.PeerRequestsPiece')
        pub.subscribe(self.peers_bitfield, 'PeersManager.updatePeersBitfield')

    def peers_bitfield(self, bitfield=None, peer=None, piece_index=None):
        if not piece_index == None:
            self.pieces_by_peer[piece_index] = ["", []]
            return

        for i in range(len(self.pieces_by_peer)):
            if bitfield[i] == 1 and peer not in self.pieces_by_peer[i][1] and not self.pieces_by_peer[i][0] == "":
                self.pieces_by_peer[i][1].append(peer)
                self.pieces_by_peer[i][0] = len(self.pieces_by_peer[i][1])

    def get_unchoked_peer(self, index):
        for peer in self.unchoked_peers:
            if peer.has_piece(index):
                return peer

        return False

    def run(self):
        while True:
            self.init_peers_connection()
            read = [p.socket for p in self.peers]
            readList, _, _ = select.select(read, [], [], 1)

            # Receive from peers
            for socket in readList:
                peer = self.get_peer_by_socket(socket)
                try:
                    msg = socket.recv(1024)
                except:
                    self.remove_peer(peer)
                    continue

                if len(msg) == 0:
                    self.remove_peer(peer)
                    continue

                peer.read_buffer += msg
                self.manage_message_received(peer)

    def init_peers_connection(self):
        for peer in self.peers:
            if not peer.has_handshaked:
                try:
                    peer.send_to_peer(peer.handshake)
                    interested = peer.build_interested()
                    peer.send_to_peer(interested)
                except:
                    self.remove_peer(peer)

    def add_peer(self, peer):
        self.peers.append(peer)

    def add_unchoked_peer(self, peer):
        self.unchoked_peers.append(peer)

    def remove_peer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except Exception as e:
                logging.error(e.message)

            self.peers.remove(peer)

        if peer in self.unchoked_peers:
            self.unchoked_peers.remove(peer)

        for rarest_piece in self.rarest_pieces.rarest_pieces:
            if peer in rarest_piece["peers"]:
                rarest_piece["peers"].remove(peer)

    def get_peer_by_socket(self, socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

        raise Exception("peer not present in PeerList")

    def handle_peer_requests(self, piece, peer):
        piece_index, block_offset, block_length = piece
        block = self.pieces_manager.get_block(piece_index, block_offset, block_length)
        piece = peer.build_request(self, piece_index, block_offset, block)
        peer.send_to_peer(piece)

    def manage_message_received(self, peer):
        while len(peer.read_buffer) > 0:
            if peer.has_handshaked == False:
                peer.check_handshake(peer.read_buffer)
                break

            message_length = utils.bytes_to_decimal(peer.read_buffer[0:4])

            # handle keep alive
            if peer.keep_alive(peer.read_buffer):
                break

            # len 0
            try:
                message_code = int(ord(peer.read_buffer[4:5]))
                payload = peer.read_buffer[5:4 + message_length]
            except Exception as e:
                logging.info("Error when reading buffer : %s" % e)
                break

            # Message is not yet complete. Wait for next message
            if len(payload) < message_length - 1:
                break

            peer.read_buffer = peer.read_buffer[message_length + 4:]

            try:
                peer.map_code_to_method[message_code](payload)
            except Exception, e:
                logging.debug("error id:", message_code, " ->", e)
                break

    def request_new_piece(self, peer, piece_index, offset, length):
        request = peer.build_request(piece_index, offset, length)
        peer.send_to_peer(request)
