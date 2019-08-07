import logging

__author__ = 'alexisgallepe'


class RarestPieces(object):
    def __init__(self, pieces_manager):

        self.pieces_manager = pieces_manager
        self.rarest_pieces = []

        for piece_number in range(self.pieces_manager.number_of_pieces):
            self.rarest_pieces.append({"idPiece": piece_number, "numberOfPeers": 0, "peers": []})

        # pub.subscribe(self.peersBitfield, 'RarestPiece.updatePeersBitfield')

    def peers_bitfield(self, bitfield=None, peer=None, piece_index=None):

        if len(self.rarest_pieces) == 0:
            raise Exception("No more piece")

        # Piece complete
        try:
            if not piece_index == None:
                self.rarest_pieces.__delitem__(piece_index)
        except Exception:
                logging.exception("Failed to remove rarest piece")

        # Peer's bitfield updated
        else:
            for i in range(len(self.rarest_pieces)):
                if bitfield[i] == 1 and peer not in self.rarest_pieces[i]["peers"]:
                    self.rarest_pieces[i]["peers"].append(peer)
                    self.rarest_pieces[i]["numberOfPeers"] = len(self.rarest_pieces[i]["peers"])

    def get_sorted_pieces(self):
        return sorted(self.rarest_pieces, key=lambda x: x['numberOfPeers'])
