__author__ = 'alexisgallepe'

import hashlib

def bytes_to_decimal(headerBytes):
    size = 0
    power = len(headerBytes) - 1

    for ch in headerBytes:
        size += int(ord(ch)) * 256 ** power
        power -= 1
    return size

def sha1_hash(string):
    """Return 20-byte sha1 hash of string.
    """
    return hashlib.sha1(string).digest()
