__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread


class PeerManager(Thread):
    def __init__(self, lstPeers, torrent):
        Thread.__init__(self)
        self.lstPeers = lstPeers
        self.torrent = torrent

    def run(self):
        buf = ""
        peers = []
        p = [s.socket for s in self.lstPeers]

        while True:
            buf = ""
            try:
                peers, wlist, xlist = select.select(p, [], [], 2)
            except Exception, a:
                print a
                break
                pass
            else:
                for i in range(len(peers)):
                    try:
                        msg = peers[i].recv(4096)
                    except Exception, e:
                        # remove peer disconnected
                        p.pop(i)
                        print 'rem'
                        break
                    else:
                        if len(msg) == 0: break
                        buf += msg

                    if len(msg) > 0:
                        print self.decodeMessagePeer(buf)
                        # return buf
                        pass

    def decodeMessagePeer(self, buf, pstr="BitTorrent protocol"):
        if buf[1:20] == pstr:  # Received handshake
            handshake = buf[:68]
            expected_length, info_dict, info_hash, peer_id = struct.unpack(
                "B" + str(len(pstr)) + "s8x20s20s",
                handshake)
            buf = buf[68:]

            if self.torrent.info_hash == info_hash:
                return ('handshake', (info_hash, peer_id)), buf
            else:
                return 'error info_hash'

        if len(buf) < 4:
            raise Exception("Too few bytes to form a protocol message.")

        # Try to match keep-alive
        try:
            keep_alive = struct.unpack("!I", buf[:4])[0]
            assert keep_alive == 0
            buf = buf[4:]
            return (self.MESSAGE_TYPES[-1], None), buf
        except AssertionError:
            pass

        # First 5 bytes are always <4:total_message_length><1:msg_id>
        total_message_length, msg_id = struct.unpack("!IB", buf[:5])
        # Advance buffer to payload
        buf = buf[5:]
        print "id: "
        print msg_id
        print "msg len: "
        print total_message_length

        return buf