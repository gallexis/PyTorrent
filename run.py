__author__ = 'alexisgallepe'

import time
import peers_manager
import peers_seeker
import pieces_manager
import torrent
import tracker
import logging
import Queue


class Run(object):
    percentage_completed = -1

    def __init__(self):
        new_peers = Queue.Queue()

        self.torrent = torrent.Torrent().load_from_path("torrent.torrent")
        self.tracker = tracker.Tracker(self.torrent, new_peers)

        self.peer_seeker = peers_seeker.PeersSeeker(new_peers, self.torrent)
        self.pieces_manager = pieces_manager.PiecesManager(self.torrent)
        self.peers_manager = peers_manager.PeersManager(self.torrent, self.pieces_manager)

        self.peers_manager.start()
        logging.info("PeersManager Started")

        self.peer_seeker.start()
        logging.info("PeerSeeker Started")

        self.pieces_manager.start()
        logging.info("PiecesManager Started")

    def start(self):
        while not self.pieces_manager.all_pieces_completed():
            if not self.peers_manager.has_unchoked_peers():
                time.sleep(0.1)
                continue

            for piece in self.pieces_manager.pieces:
                print piece.is_full
                if piece.is_full: continue

                peer = self.peers_manager.get_peer_having_piece(piece.piece_index)
                if not peer: continue

                # peer.send_bitfield()

                data = self.pieces_manager.pieces[piece.piece_index].get_empty_block()
                if data:
                    self.peers_manager.peer_requests_piece(peer, data)

                """
                data = self.pieces_manager.pieces[piece.piece_index].get_empty_block()
                if data:
                    index, offset, length = data
                    block = self.pieces_manager.get_block(index, offset, length)
                    if block:
                        peer.send_piece(index, offset, length, block)
                """

                if piece.all_blocks_full():
                    piece.set_to_full()

                piece.update_block_status()

            self.display_progression()

            time.sleep(0.1)

    def display_progression(self):
        new_progression = 0

        for i in range(self.pieces_manager.number_of_pieces):
            for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                if self.pieces_manager.pieces[i].blocks[j][0] == "Full":
                    new_progression += len(self.pieces_manager.pieces[i].blocks[j][2])

        if new_progression == self.percentage_completed:
            return

        number_of_peers = len(self.peers_manager.unchoked_peers_count())
        percentage_completed = float((float(new_progression) / self.torrent.total_length) * 100)

        print "Number of peers: {} - Completed : {}%".format(number_of_peers, percentage_completed)

        self.percentage_completed = new_progression
