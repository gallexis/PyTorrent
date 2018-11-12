__author__ = 'alexisgallepe'

import time
import PeersManager
import PeerSeeker
import PiecesManager
import Torrent
import Tracker
import logging
import Queue


class Run(object):
    def __init__(self):
        new_peers = Queue.Queue()

        self.torrent = Torrent.Torrent().load_from_path("oldest_torrent_file.torrent")
        self.tracker = Tracker.Tracker(self.torrent, new_peers)

        self.peer_seeker = PeerSeeker.PeerSeeker(new_peers, self.torrent)
        self.pieces_manager = PiecesManager.PiecesManager(self.torrent)
        self.peers_manager = PeersManager.PeersManager(self.torrent, self.pieces_manager)

        self.peers_manager.start()
        logging.info("Peers-manager Started")

        self.peer_seeker.start()
        logging.info("Peer-seeker Started")

        self.pieces_manager.start()
        logging.info("Pieces-manager Started")

    def start(self):
        old = 0

        while not self.pieces_manager.pieces_full():
            if len(self.peers_manager.unchoked_peers) > 0:

                for piece in self.pieces_manager.pieces:
                    if not piece.is_full:
                        peer = self.peers_manager.get_unchoked_peer(piece.piece_index)
                        if not peer:
                            continue

                        data = self.pieces_manager.pieces[piece.piece_index].get_empty_block()

                        if data:
                            index, offset, length = data
                            self.peers_manager.request_new_piece(peer, index, offset, length)

                        if piece.all_blocks_full():
                            piece.set_to_full()

                        ##########################
                        for block in piece.blocks:
                            if (int(time.time()) - block[3]) > 8 and block[0] == "Pending":
                                block[0] = "Free"
                                block[3] = 0

                b = 0
                for i in range(self.pieces_manager.number_of_pieces):
                    for j in range(self.pieces_manager.pieces[i].number_of_blocks):
                        if self.pieces_manager.pieces[i].blocks[j][0] == "Full":
                            b += len(self.pieces_manager.pieces[i].blocks[j][2])

                if b == old:
                    continue

                old = b
                print "Number of peers: ", len(self.peers_manager.unchoked_peers), " Completed: ", float(
                    (float(b) / self.torrent.total_length) * 100), "%"

            ##########################

            time.sleep(0.1)
