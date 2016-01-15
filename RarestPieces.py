__author__ = 'alexisgallepe'

from pubsub import pub

class RarestPieces(object):
    def __init__(self, piecesManager):

        self.piecesManager = piecesManager
        self.rarestPieces = []

        for pieceNumber in range(self.piecesManager.numberOfPieces):
            peersByPieceIndex = {"idPiece":pieceNumber, "numberOfPeers":0, "peers":[]}
            self.rarestPieces.append(peersByPieceIndex)

        #pub.subscribe(self.peersBitfield, 'RarestPiece.updatePeersBitfield')


    def peersBitfield(self,bitfield=None,peer=None,pieceIndex=None):

        if len(self.rarestPieces) == 0:
            raise("no more piece")

        # Piece complete
        try:
            if not pieceIndex == None:
                self.rarestPieces.__delitem__(pieceIndex)
        except:
            pass

        # Peer's bitfield updated
        else:
            for i in range(len(self.rarestPieces)):
                if bitfield[i] == 1 and peer not in self.rarestPieces[i]["peers"]:
                    self.rarestPieces[i]["peers"].append(peer)
                    self.rarestPieces[i]["numberOfPeers"] = len(self.rarestPieces[i]["peers"])

    def getSortedPieces(self):
        return sorted(self.rarestPieces, key=lambda x:x['numberOfPeers'])