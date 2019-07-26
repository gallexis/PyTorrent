__author__ = 'alexisgallepe'

from enum import Enum

BLOCK_SIZE = 2 ** 14


class State(Enum):
    FREE = 1
    PENDING = 2
    FULL = 3


class Block():
    def __init__(self, state: State = State.FREE, block_size: int = BLOCK_SIZE, data: bytes = b'', last_seen: float = 0):
        self.state: State = state
        self.block_size: int = block_size
        self.data: bytes = data
        self.last_seen: float = last_seen
