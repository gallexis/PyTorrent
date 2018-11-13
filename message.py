from struct import pack, unpack, error as unpack_exception

# https://github.com/nbedos/PyTo/blob/master/pyto/messages.py


# HandShake - String identifier of the protocol for BitTorrent V1
import bitstring

HANDSHAKE_PSTR_V1 = b"BitTorrent protocol"
HANDSHAKE_PSTR_LEN = len(HANDSHAKE_PSTR_V1)
LENGTH_PREFIX = 4


class Message(object):
    pass


class Handshake(Message):
    """
        Handshake = <pstrlen><pstr><reserved><info_hash><peer_id>
            - pstrlen = length of pstr (1 byte)
            - pstr = string identifier of the protocol: "BitTorrent protocol" (19 bytes)
            - reserved = 8 reserved bytes indicating extensions to the protocol (8 bytes)
            - info_hash = hash of the value of the 'info' key of the torrent file (20 bytes)
            - peer_id = unique identifier of the Peer (20 bytes)

        Total length = payload length = 49 + len(pstr) = 68 bytes (for BitTorrent v1)
    """

    payload_length = 68
    total_length = payload_length

    def __init__(self, info_hash, peer_id=b'-ZZ0007-000000000000'):
        super(Handshake, self).__init__()

        assert len(info_hash) == 20
        assert len(peer_id) < 255
        self.peer_id = peer_id
        self.info_hash = info_hash

    def to_bytes(self):
        reserved = b'\x00' * 8
        handshake = pack(">B{}s8s20s20s".format(HANDSHAKE_PSTR_LEN),
                         HANDSHAKE_PSTR_LEN,
                         HANDSHAKE_PSTR_V1,
                         reserved,
                         self.info_hash,
                         self.peer_id)

        return handshake

    @classmethod
    def from_bytes(cls, payload):
        try:
            pstrlen, = unpack(">B", payload[:1])
            pstr, reserved, info_hash, peer_id = unpack(">{}s8s20s20s".format(pstrlen), payload[1:])
        except unpack_exception:
            raise ValueError("Invalid binary format for HandShake message")

        if pstr != HANDSHAKE_PSTR_V1:
            raise ValueError("Invalid string identifier of the protocol")

        return Handshake(info_hash, peer_id)


class KeepAlive(Message):
    """
        KEEP_ALIVE = <length>
            - payload length = 0 (4 bytes)
    """
    payload_length = 0
    total_length = 4

    def __init__(self,):
        super(KeepAlive, self).__init__()

    def to_bytes(self):
        return pack(">I", self.payload_length)

    @classmethod
    def from_bytes(cls, payload):
        try:
            payload_length = unpack("!I", payload[:cls.total_length])
            if payload_length != 0:
                raise ValueError("Not a Keep Alive message")

        except unpack_exception:
            raise ValueError("Invalid binary format for Keep Alive message")

        return KeepAlive()


class Choke(Message):
    """
        CHOKE = <length><message_id>
            - payload length = 1 (4 bytes)
            - message id = 0 (1 byte)
    """
    message_id = 0
    chokes_me = True

    payload_length = 1
    total_length = 5

    def __init__(self,):
        super(Choke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        try:
            payload_length, message_id = unpack(">IB", payload[:cls.total_length])
            if message_id != cls.message_id:
                raise ValueError("Not a Choke message")

        except unpack_exception:
            raise ValueError("Invalid binary format for Choke message")

        return Choke()


class UnChoke(Message):
    """
        UnChoke = <length><message_id>
            - payload length = 1 (4 bytes)
            - message id = 1 (1 byte)
    """
    message_id = 1
    chokes_me = False

    payload_length = 1
    total_length = 5

    def __init__(self,):
        super(UnChoke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        try:
            payload_length, message_id = unpack(">IB", payload[:cls.total_length])
            if message_id != cls.message_id:
                raise ValueError("Not an UnChoke message")

        except unpack_exception:
            raise ValueError("Invalid binary format for Unchoke message")

        return UnChoke()


class Interested(Message):
    """
        INTERESTED = <length><message_id>
            - payload length = 1 (4 bytes)
            - message id = 2 (1 byte)
    """
    message_id = 2
    interested = True

    payload_length = 1
    total_size = 4 + payload_length

    def __init__(self,):
        super(Interested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        try:
            payload_length, message_id = unpack(">IB", payload[:cls.total_size])
            if message_id != cls.message_id:
                raise ValueError("Not an Interested message")

        except unpack_exception:
            raise ValueError("Invalid binary format for Interested message")

        return Interested()


class NotInterested(Message):
    """
        NOT INTERESTED = <length><message_id>
            - payload length = 1 (4 bytes)
            - message id = 3 (1 byte)
    """
    message_id = 3
    interested = False

    payload_length = 1
    total_length = 5

    def __init__(self,):
        super(NotInterested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        try:
            payload_length, message_id = unpack(">IB", payload[:cls.total_length])
            if message_id != cls.message_id:
                raise ValueError("Not an Interested message")

        except unpack_exception:
            raise ValueError("Invalid binary format for Interested message")

        return Interested()


class Have(Message):
    """
        HAVE = <length><message_id><piece_index>
            - payload length = 5 (4 bytes)
            - message_id = 4 (1 byte)
            - piece_index = zero based index of the piece (4 bytes)
    """
    message_id = 4

    payload_length = 5
    total_length = 4 + payload_length

    def __init__(self, piece_index):
        super(Have, self).__init__()
        self.piece_index = piece_index

    def to_bytes(self):
        try:
            return pack(">IBI", self.payload_length, self.message_id, self.piece_index)
        except unpack_exception:
            raise ValueError("Invalid values for encoding the Have instance")

    @classmethod
    def from_payload(cls, payload):
        try:
            payload_length, message_id, piece_index, = unpack(">IBI", payload[:cls.total_length])
            if message_id != cls.message_id:
                raise ValueError("Not a Have message")

            return Have(piece_index)

        except unpack_exception:
            raise ValueError("Invalid binary format for Have message")


class BitField(Message):
    """
        BITFIELD = <length><message id><bitfield>
            - payload length = 1 + bitfield_size (4 bytes)
            - message id = 5 (1 byte)
            - bitfield = bitfield representing downloaded pieces (bitfield_size bytes)
    """
    message_id = 5

    # Unknown until given a bitfield
    payload_length = -1
    total_length = -1

    def __init__(self, bitfield):  # bitfield is a bitstring.BitArray
        super(BitField, self).__init__()

        self.bitfield_as_bytes = bitfield.tobytes()
        self.bitfield_length = len(self.bitfield_as_bytes)

        self.payload_length = 1 + self.bitfield_length
        self.total_length = 4 + self.payload_length

    def to_bytes(self):
        return pack(">IB{}s".format(self.bitfield_length),
                    self.payload_length,
                    self.message_id,
                    self.bitfield_as_bytes)

    @classmethod
    def from_payload(cls, payload):
        payload_length, message_id, = unpack(">IB", payload[:5])
        bitfield_length = payload_length - 1

        if message_id != cls.message_id:
            raise ValueError("Not a BitField message")

        raw_bitfield = unpack(">{}s".format(bitfield_length), payload[5:bitfield_length])
        bitfield = bitstring.BitArray(bytes=str(raw_bitfield))

        return BitField(bitfield)


class Request(Message):
    """
        REQUEST = <length><message id><piece index><block offset><block length>
            - payload length = 13 (4 bytes)
            - message id = 6 (1 byte)
            - piece index = zero based piece index (4 bytes)
            - block offset = zero based of the requested block (4 bytes)
            - block length = length of the requested block (4 bytes)
    """
    message_id = 6

    payload_length = 13
    total_length = 4 + payload_length

    def __init__(self, piece_index, block_offset, block_length):
        super(Request, self).__init__()

        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def to_bytes(self):
        try:
            return pack(">IBIII",
                        self.payload_length,
                        self.message_id,
                        self.piece_index,
                        self.block_offset,
                        self.block_length)
        except unpack_exception:
            raise ValueError("Invalid values for encoding the Request instance")

    @classmethod
    def from_payload(cls, payload):
        try:
            payload_length, message_id, piece_index, block_offset, block_length = unpack(">IBIII", payload)
            if message_id != cls.message_id:
                raise ValueError("Not a Request message")

            return Request(piece_index, block_offset, block_length)

        except unpack_exception:
            raise ValueError("Invalid binary format for Request message")


class Piece(Message):
    """
        PIECE = <length><message id><piece index><block offset><block>
        - length = 9 + block length (4 bytes)
        - message id = 7 (1 byte)
        - piece index =  zero based piece index (4 bytes)
        - block offset = zero based of the requested block (4 bytes)
        - block = block as a bytestring or bytearray (block_length bytes)"""
    message_id = 7

    payload_length = -1
    total_length = -1

    def __init__(self, block_length, piece_index, block_offset, block):
        super(Piece, self).__init__()

        self.block_length = block_length
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block = block

        self.payload_length = 9 + block_length
        self.total_length = 4 + self.payload_length

    def to_bytes(self):
        try:
            return pack(">IBII{}s".format(self.block_length),
                        self.payload_length,
                        self.message_id,
                        self.piece_index,
                        self.block_offset,
                        self.block)
        except unpack_exception:
            raise ValueError("Invalid values for encoding the Piece instance")

    @classmethod
    def from_payload(cls, payload):
        block_length = len(payload) - 13
        try:
            payload_length, message_id, piece_index, block_offset, block = unpack(">IBII{}s".format(block_length),
                                                                                  payload)

            if message_id != cls.message_id:
                raise ValueError("Not a Piece message")

            return Piece(block_length, piece_index, block_offset, block)

        except unpack_exception:
            raise ValueError("Invalid binary format for Piece message")


class Cancel(Message):
    """CANCEL = <length><message id><piece index><block offset><block length>
        - length = 13 (4 bytes)
        - message id = 8 (1 byte)
        - piece index = zero based piece index (4 bytes)
        - block offset = zero based of the requested block (4 bytes)
        - block length = length of the requested block (4 bytes)"""
    message_id = 8

    payload_length = 13
    total_length = 4 + payload_length

    def __init__(self, piece_index, block_offset, block_length):
        super(Cancel, self).__init__()

        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def to_bytes(self):
        try:
            return pack(">IBIII",
                        self.payload_length,
                        self.message_id,
                        self.piece_index,
                        self.block_offset,
                        self.block_length)
        except unpack_exception:
            raise ValueError("Invalid values for encoding the Cancel instance")

    @classmethod
    def from_payload(cls, payload):
        try:
            payload_length, message_id, piece_index, block_offset, block_length = unpack(">IBIII", payload)
            if message_id != cls.message_id:
                raise ValueError("Not a Cancel message")

            return Cancel(piece_index, block_offset, block_length)

        except unpack_exception:
            raise ValueError("Invalid binary format for Cancel message")


class Port(Message):
    """
        PORT = <length><message id><port number>
            - length = 5 (4 bytes)
            - message id = 9 (1 byte)
            - port number = listen_port (4 bytes)
    """
    message_id = 9

    payload_length = 5
    total_length = 4 + payload_length

    def __init__(self, listen_port):
        super(Port, self).__init__()

        self.listen_port = listen_port

    def to_bytes(self):
        try:
            return pack(">IBI",
                        self.payload_length,
                        self.message_id,
                        self.listen_port)

        except unpack_exception:
            raise ValueError("Invalid values for encoding the Port instance")

    @classmethod
    def from_payload(cls, payload):
        try:
            payload_length, message_id, listen_port, = unpack(">IBI", payload)
            if message_id != cls.message_id:
                raise ValueError("Not a Port message")

            return Port(listen_port)

        except unpack_exception:
            raise ValueError("Invalid binary format for Port message")
