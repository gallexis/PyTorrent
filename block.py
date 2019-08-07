__author__ = 'alexisgallepe'

from enum import Enum

BLOCK_SIZE = 2 ** 14


class State(Enum):
    FREE = 0
    PENDING = 1
    FULL = 2


class Block():
    def __init__(self, state: State = State.FREE, block_size: int = BLOCK_SIZE, data: bytes = b'', last_seen: float = 0):
        self.state: State = state
        self.block_size: int = block_size
        self.data: bytes = data
        self.last_seen: float = last_seen

    def __str__(self):
        return "%s - %d - %d - %d" % (self.state, self.block_size, len(self.data), self.last_seen)