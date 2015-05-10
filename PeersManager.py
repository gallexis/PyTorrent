__author__ = 'alexisgallepe'

import select
import struct
from threading import Thread


class PeerManager(Thread):
    def __init__(self, lstPeers, torrent):
        Thread.__init__(self)
        self.lstPeers = lstPeers
        # self.torrent = torrent


    def run(self):
        p = [s.socket for s in self.lstPeers]

        while True:
            try:
                peers, wlist, xlist = select.select(p, [], [], 1)
            except Exception, e:
                print e
            else:
                for i in range(len(peers)):
                    try:
                        msg = peers[i].recv(4096)
                    except Exception, e:
                        # remove peer disconnected
                        print 'rem'
                        p.pop(i)
                        self.lstPeers.pop(i)
                        break
                    else:
                        if len(msg) == 0: break
                        self.lstPeers[i].buffer += msg
                        print "bufff"
                    if len(self.lstPeers[i].buffer) > 0:
                        self.manageMessageReceived(self.lstPeers[i])
                        #self.lstPeers[i].buffer = b""
                        pass


    def manageMessageReceived(self, peer):
        if peer.hasHanshaked == False:
            peer.checkHandshake(peer.buffer)
            return

        elif peer.keep_alive(peer.buffer):
            # send back keepalive ?
            return

        elif len(peer.buffer) >= 4:
            total_message_length, msg_id = struct.unpack("!IB", peer.buffer[:5])
            if len(peer.buffer[4:]) >= total_message_length:
                peer.message_ID_to_func_name[msg_id](peer.buffer[5:])
                # self.buffer = self.buffer[message_length + 4:]
            else:
                # return self.buffer
                print "else"
                pass
        else:
            print 'too small'
            # return self.buffer