__author__ = 'alexisgallepe'

import hashlib

def sha1_hash(string):
    """Return 20-byte sha1 hash of string.
    """
    return hashlib.sha1(string).digest()
