import struct

__author__ = 'alexisgallepe'

import select
from threading import Thread
from pubsub import pub
import rarest_piece
import logging


class PeersManager(Thread):
    def __init__(self, torrent, pieces_manager):
        Thread.__init__(self)
        self.peers = []
        self.torrent = torrent
        self.pieces_manager = pieces_manager
        self.rarest_pieces = rarest_piece.RarestPieces(pieces_manager)
        self.pieces_by_peer = [[0, []] for _ in range(pieces_manager.number_of_pieces)]

        # Events
        pub.subscribe(self.add_new_peer, 'PeersManager.newPeer')
        pub.subscribe(self.peer_requests_piece, 'PeersManager.PeerRequestsPiece')
        pub.subscribe(self.peers_bitfield, 'PeersManager.updatePeersBitfield')

    def peers_bitfield(self, bitfield=None, peer=None, piece_index=None):
        if piece_index:
            self.pieces_by_peer[piece_index] = [None, []]
            return

        for i in range(len(self.pieces_by_peer)):
            if bitfield[i] == 1 and peer not in self.pieces_by_peer[i][1] and self.pieces_by_peer[i][0]:
                self.pieces_by_peer[i][1].append(peer)
                self.pieces_by_peer[i][0] = len(self.pieces_by_peer[i][1])

    def get_peer_having_piece(self, index):
        for peer in self.peers:
            if peer.is_choking() and peer.has_piece(index):
                print '>>>', peer.is_choking(), peer.has_piece(index), index
                return peer

        return None

    def has_unchoked_peers(self):
        for peer in self.peers:
            if not peer.is_choking():
                return True
        return False

    def unchoked_peers_count(self):
        cpt = 0
        for peer in self.peers:
            if peer.is_choking():
                cpt += 1
        return cpt

    def run(self):
        while True:
            self.startConnectionToPeers()
            read = [p.socket for p in self.peers]
            read_list, _, _ = select.select(read, [], [], 1)

            # Receive from peers
            for socket in read_list:
                peer = self.get_peer_by_socket(socket)
                try:
                    data = socket.recv(1024)
                except Exception as e:
                    logging.error("Error when receiving from peer : %s" % e.message)
                    self.remove_peer(peer)
                    continue

                if len(data) == 0:
                    self.remove_peer(peer)
                    continue

                print '(((', data
                peer.read_buffer += data

                self.handle_new_message(peer)

    def startConnectionToPeers(self):
        for peer in self.peers:
            if not peer.has_handshaked:
                try:
                    peer.sendToPeer(peer.handshake)
                    interested = struct.pack('!I', 1) + struct.pack('!B', 2)
                    peer.sendToPeer(interested)
                except:
                    self.remove_peer(peer)

    def add_new_peer(self, peer):
        try:
            self.peers.append(peer)

        except Exception as e:
            logging.error("Error when sending Handshake or Interested message : %s" % e.message)
            return

    def remove_peer(self, peer):
        if peer in self.peers:
            try:
                peer.socket.close()
            except Exception as e:
                logging.error(e.message)

            self.peers.remove(peer)

        for rarest_piece in self.rarest_pieces.rarest_pieces:
            if peer in rarest_piece["peers"]:
                rarest_piece["peers"].remove(peer)

    def get_peer_by_socket(self, socket):
        for peer in self.peers:
            if socket == peer.socket:
                return peer

        raise Exception("Peer not present in peer_list")

    def peer_requests_piece(self, peer, piece):
        piece_index, block_offset, block_length = piece
        request = peer.build_request(piece_index, block_offset, block_length)
        peer.send_to_peer(request)
        logging.info("Sent : peer_requests_piece (%s)" % str(piece))

    def request_piece(self, peer, piece_index, offset, block):
        request = peer.build_request(piece_index, offset, block)
        peer.send_to_peer(request)
        logging.info("Sent : send_new_piece (%s)" % str((piece_index, offset)))

    def handle_new_message(self, peer):
        while len(peer.read_buffer) > 0:
            if not peer.has_handshaked:
                peer.check_handshake(peer.read_buffer)
                logging.error("No handshake made")
                break

            message_length = struct.unpack('!I', peer.read_buffer[:4])[0]

            if peer.is_keep_alive(peer.read_buffer):
                break

            try:
                message_code = int(ord(peer.read_buffer[4:5]))
                payload = peer.read_buffer[5:4 + message_length]
            except Exception as e:
                logging.info("Error when reading buffer : %s" % e.message)
                break

            # Message is not yet complete. Wait for next message
            print '>>', payload, message_code, len(payload), message_length

            if len(payload) < message_length - 1:
                break

            peer.read_buffer = peer.read_buffer[message_length + 4:]

            try:
                peer.map_code_to_handlers[message_code](payload)
            except Exception as e:
                logging.debug("Message_code error (%s) : %s " % (message_code, e.message))
                break

            peer.read_buffer = b''
