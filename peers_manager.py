import time

__author__ = 'alexisgallepe'

import select
from threading import Thread
from pubsub import pub
import rarest_piece
import logging
import message
import peer
import errno
import socket
import random


class PeersManager(Thread):
    def __init__(self, torrent, pieces_manager):
        Thread.__init__(self)
        self.peers = []
        self.torrent = torrent
        self.pieces_manager = pieces_manager
        self.rarest_pieces = rarest_piece.RarestPieces(pieces_manager)
        self.pieces_by_peer = [[0, []] for _ in range(pieces_manager.number_of_pieces)]
        self.is_active = True

        # Events
        pub.subscribe(self.peer_requests_piece, 'PeersManager.PeerRequestsPiece')
        pub.subscribe(self.peers_bitfield, 'PeersManager.updatePeersBitfield')

    def peer_requests_piece(self, request=None, peer=None):
        if not request or not peer:
            logging.error("empty request/peer message")

        piece_index, block_offset, block_length = request.piece_index, request.block_offset, request.block_length

        block = self.pieces_manager.get_block(piece_index, block_offset, block_length)
        if block:
            piece = message.Piece(piece_index, block_offset, block_length, block).to_bytes()
            peer.send_to_peer(piece)
            logging.info("Sent piece index {} to peer : {}".format(request.piece_index, peer.ip))

    def peers_bitfield(self, bitfield=None):
        for i in range(len(self.pieces_by_peer)):
            if bitfield[i] == 1 and peer not in self.pieces_by_peer[i][1] and self.pieces_by_peer[i][0]:
                self.pieces_by_peer[i][1].append(peer)
                self.pieces_by_peer[i][0] = len(self.pieces_by_peer[i][1])

    def get_random_peer_having_piece(self, index):
        ready_peers = []

        for peer in self.peers:
            if peer.is_eligible() and peer.is_unchoked() and peer.am_interested() and peer.has_piece(index):
                ready_peers.append(peer)

        return random.choice(ready_peers) if ready_peers else None

    def has_unchoked_peers(self):
        for peer in self.peers:
            if peer.is_unchoked():
                return True
        return False

    def unchoked_peers_count(self):
        cpt = 0
        for peer in self.peers:
            if peer.is_unchoked():
                cpt += 1
        return cpt


    @staticmethod
    def _read_from_socket(sock):
        data = b''

        while True:
            try:
                buff = sock.recv(4096)
                if len(buff) <= 0:
                    break

                data += buff
            except socket.error as e:
                err = e.args[0]
                if err != errno.EAGAIN or err != errno.EWOULDBLOCK:
                    logging.debug("Wrong errno {}".format(err))
                break
            except Exception:
                logging.exception("Recv failed")
                break

        return data

    def run(self):
        while self.is_active:
            read = [peer.socket for peer in self.peers]
            read_list, _, _ = select.select(read, [], [], 1)

            for socket in read_list:
                peer = self.get_peer_by_socket(socket)
                if not peer.healthy:
                    self.remove_peer(peer)
                    continue

                try:
                    payload = self._read_from_socket(socket)
                except Exception as e:
                    logging.error("Recv failed %s" % e.__str__())
                    self.remove_peer(peer)
                    continue

                peer.read_buffer += payload

                for message in peer.get_messages():
                    self._process_new_message(message, peer)

    def _do_handshake(self, peer):
        try:
            handshake = message.Handshake(self.torrent.info_hash)
            peer.send_to_peer(handshake.to_bytes())
            logging.info("new peer added : %s" % peer.ip)
            return True

        except Exception:
            logging.exception("Error when sending Handshake message")

        return False

    def add_peers(self, peers):
        for peer in peers:
            if self._do_handshake(peer):
                self.peers.append(peer)
            else:
                print("Error _do_handshake")

    def remove_peer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except Exception:
                logging.exception("")

            self.peers.remove(peer)

        #for rarest_piece in self.rarest_pieces.rarest_pieces:
        #    if peer in rarest_piece["peers"]:
        #        rarest_piece["peers"].remove(peer)

    def get_peer_by_socket(self, socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

        raise Exception("Peer not present in peer_list")

    def _process_new_message(self, new_message: message.Message, peer: peer.Peer):
        if isinstance(new_message, message.Handshake) or isinstance(new_message, message.KeepAlive):
            logging.error("Handshake or KeepALive should have already been handled")

        elif isinstance(new_message, message.Choke):
            peer.handle_choke()

        elif isinstance(new_message, message.UnChoke):
            peer.handle_unchoke()

        elif isinstance(new_message, message.Interested):
            peer.handle_interested()

        elif isinstance(new_message, message.NotInterested):
            peer.handle_not_interested()

        elif isinstance(new_message, message.Have):
            peer.handle_have(new_message)

        elif isinstance(new_message, message.BitField):
            peer.handle_bitfield(new_message)

        elif isinstance(new_message, message.Request):
            peer.handle_request(new_message)

        elif isinstance(new_message, message.Piece):
            peer.handle_piece(new_message)

        elif isinstance(new_message, message.Cancel):
            peer.handle_cancel()

        elif isinstance(new_message, message.Port):
            peer.handle_port_request()

        else:
            logging.error("Unknown message")
