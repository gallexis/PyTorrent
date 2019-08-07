import logging
import random
import socket
from struct import pack, unpack

# HandShake - String identifier of the protocol for BitTorrent V1
import bitstring

HANDSHAKE_PSTR_V1 = b"BitTorrent protocol"
HANDSHAKE_PSTR_LEN = len(HANDSHAKE_PSTR_V1)
LENGTH_PREFIX = 4


class WrongMessageException(Exception):
    pass

class MessageDispatcher:

    def __init__(self, payload):
        self.payload = payload

    def dispatch(self):
        try:
            payload_length, message_id, = unpack(">IB", self.payload[:5])
        except:
            logging.exception("Error when unpacking message")
            return None

        map_id_to_message = {
            0: Choke,
            1: UnChoke,
            2: Interested,
            3: NotInterested,
            4: Have,
            5: BitField,
            6: Request,
            7: Piece,
            8: Cancel,
            9: Port
        }

        if message_id not in list(map_id_to_message.keys()):
            raise WrongMessageException("Wrong message id")

        return map_id_to_message[message_id].from_bytes(self.payload)


class Message:
    def to_bytes(self):
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, payload):
        raise NotImplementedError()


"""
UDP Tracker
"""


class UdpTrackerConnection(Message):
    """
        connect = <connection_id><action><transaction_id>
            - connection_id = 64-bit integer
            - action = 32-bit integer
            - transaction_id = 32-bit integer

        Total length = 64 + 32 + 32 = 128 bytes
    """

    def __init__(self):
        super(UdpTrackerConnection, self).__init__()
        self.conn_id = pack('>Q', 0x41727101980)
        self.action = pack('>I', 0)
        self.trans_id = pack('>I', random.randint(0, 100000))

    def to_bytes(self):
        return self.conn_id + self.action + self.trans_id

    def from_bytes(self, payload):
        self.action, = unpack('>I', payload[:4])
        self.trans_id, = unpack('>I', payload[4:8])
        self.conn_id, = unpack('>Q', payload[8:])


class UdpTrackerAnnounce(Message):
    """
        connect = <connection_id><action><transaction_id>

        0	64-bit integer	connection_id
8	32-bit integer	action	1
12	32-bit integer	transaction_id
16	20-byte string	info_hash
36	20-byte string	peer_id
56	64-bit integer	downloaded
64	64-bit integer	left
72	64-bit integer	uploaded
80	32-bit integer	event
84	32-bit integer	IP address	0
88	32-bit integer	key
92	32-bit integer	num_want	-1
96	16-bit integer	port

            - connection_id = 64-bit integer
            - action = 32-bit integer
            - transaction_id = 32-bit integer

        Total length = 64 + 32 + 32 = 128 bytes
    """

    def __init__(self, info_hash, conn_id, peer_id):
        super(UdpTrackerAnnounce, self).__init__()
        self.peer_id = peer_id
        self.conn_id = conn_id
        self.info_hash = info_hash
        self.trans_id = pack('>I', random.randint(0, 100000))
        self.action = pack('>I', 1)

    def to_bytes(self):
        conn_id = pack('>Q', self.conn_id)
        action = self.action
        trans_id = self.trans_id
        downloaded = pack('>Q', 0)
        left = pack('>Q', 0)
        uploaded = pack('>Q', 0)

        event = pack('>I', 0)
        ip = pack('>I', 0)
        key = pack('>I', 0)
        num_want = pack('>i', -1)
        port = pack('>h', 8000)

        msg = (conn_id + action + trans_id + self.info_hash + self.peer_id + downloaded +
               left + uploaded + event + ip + key + num_want + port)

        return msg


class UdpTrackerAnnounceOutput:
    """
        connect = <connection_id><action><transaction_id>

0	32-bit integer	action	1
4	32-bit integer	transaction_id
8	32-bit integer	interval
12	32-bit integer	leechers
16	32-bit integer	seeders
20 + 6 * n	32-bit integer	IP address
24 + 6 * n	16-bit integer	TCP port
20 + 6 * N

    """

    def __init__(self):
        self.action = None
        self.transaction_id = None
        self.interval = None
        self.leechers = None
        self.seeders = None
        self.list_sock_addr = []

    def from_bytes(self, payload):
        self.action, = unpack('>I', payload[:4])
        self.transaction_id, = unpack('>I', payload[4:8])
        self.interval, = unpack('>I', payload[8:12])
        self.leechers, = unpack('>I', payload[12:16])
        self.seeders, = unpack('>I', payload[16:20])
        self.list_sock_addr = self._parse_sock_addr(payload[20:])

    def _parse_sock_addr(self, raw_bytes):
        socks_addr = []

        # socket address : <IP(4 bytes)><Port(2 bytes)>
        # len(socket addr) == 6 bytes
        for i in range(int(len(raw_bytes) / 6)):
            start = i * 6
            end = start + 6
            ip = socket.inet_ntoa(raw_bytes[start:(end - 2)])
            raw_port = raw_bytes[(end - 2):end]
            port = raw_port[1] + raw_port[0] * 256

            socks_addr.append((ip, port))

        return socks_addr


"""
    Bittorrent messages
"""

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
        pstrlen, = unpack(">B", payload[:1])
        pstr, reserved, info_hash, peer_id = unpack(">{}s8s20s20s".format(pstrlen), payload[1:cls.total_length])

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

    def __init__(self):
        super(KeepAlive, self).__init__()

    def to_bytes(self):
        return pack(">I", self.payload_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_length = unpack(">I", payload[:cls.total_length])

        if payload_length != 0:
            raise WrongMessageException("Not a Keep Alive message")

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

    def __init__(self):
        super(Choke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id = unpack(">IB", payload[:cls.total_length])
        if message_id != cls.message_id:
            raise WrongMessageException("Not a Choke message")

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

    def __init__(self):
        super(UnChoke, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id = unpack(">IB", payload[:cls.total_length])

        if message_id != cls.message_id:
            raise WrongMessageException("Not an UnChoke message")

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
    total_length = 4 + payload_length

    def __init__(self):
        super(Interested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id = unpack(">IB", payload[:cls.total_length])

        if message_id != cls.message_id:
            raise WrongMessageException("Not an Interested message")

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

    def __init__(self):
        super(NotInterested, self).__init__()

    def to_bytes(self):
        return pack(">IB", self.payload_length, self.message_id)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id = unpack(">IB", payload[:cls.total_length])
        if message_id != cls.message_id:
            raise WrongMessageException("Not a Non Interested message")

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
        pack(">IBI", self.payload_length, self.message_id, self.piece_index)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id, piece_index = unpack(">IBI", payload[:cls.total_length])
        if message_id != cls.message_id:
            raise WrongMessageException("Not a Have message")

        return Have(piece_index)


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
        self.bitfield = bitfield
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
    def from_bytes(cls, payload):
        payload_length, message_id = unpack(">IB", payload[:5])
        bitfield_length = payload_length - 1

        if message_id != cls.message_id:
            raise WrongMessageException("Not a BitField message")

        raw_bitfield, = unpack(">{}s".format(bitfield_length), payload[5:5 + bitfield_length])
        bitfield = bitstring.BitArray(bytes=bytes(raw_bitfield))

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
        return pack(">IBIII",
                    self.payload_length,
                    self.message_id,
                    self.piece_index,
                    self.block_offset,
                    self.block_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id, piece_index, block_offset, block_length = unpack(">IBIII",
                                                                                     payload[:cls.total_length])
        if message_id != cls.message_id:
            raise WrongMessageException("Not a Request message")

        return Request(piece_index, block_offset, block_length)


class Piece(Message):
    """
        PIECE = <length><message id><piece index><block offset><block>
        - length = 9 + block length (4 bytes)
        - message id = 7 (1 byte)
        - piece index =  zero based piece index (4 bytes)
        - block offset = zero based of the requested block (4 bytes)
        - block = block as a bytestring or bytearray (block_length bytes)
    """
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
        return pack(">IBII{}s".format(self.block_length),
                    self.payload_length,
                    self.message_id,
                    self.piece_index,
                    self.block_offset,
                    self.block)

    @classmethod
    def from_bytes(cls, payload):
        block_length = len(payload) - 13
        payload_length, message_id, piece_index, block_offset, block = unpack(">IBII{}s".format(block_length),
                                                                              payload[:13 + block_length])

        if message_id != cls.message_id:
            raise WrongMessageException("Not a Piece message")

        return Piece(block_length, piece_index, block_offset, block)


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
        return pack(">IBIII",
                    self.payload_length,
                    self.message_id,
                    self.piece_index,
                    self.block_offset,
                    self.block_length)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id, piece_index, block_offset, block_length = unpack(">IBIII",
                                                                                     payload[:cls.total_length])
        if message_id != cls.message_id:
            raise WrongMessageException("Not a Cancel message")

        return Cancel(piece_index, block_offset, block_length)


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
        return pack(">IBI",
                    self.payload_length,
                    self.message_id,
                    self.listen_port)

    @classmethod
    def from_bytes(cls, payload):
        payload_length, message_id, listen_port = unpack(">IBI", payload[:cls.total_length])

        if message_id != cls.message_id:
            raise WrongMessageException("Not a Port message")

        return Port(listen_port)
