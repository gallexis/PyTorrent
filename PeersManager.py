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
                        msg = peers[i].recv(1024)
                    except Exception, e:
                        # remove peer disconnected
                        print 'rem'
                        p.pop(i)
                        self.lstPeers.pop(i)
                        break
                    else:
                        if len(msg) == 0:
                            print 'rem2'
                            p.pop(i)
                            self.lstPeers.pop(i)
                            break
                        print 'inc'
                        self.lstPeers[i].buffer += msg

                        self.manageMessageReceived(self.lstPeers[i])
                        #self.lstPeers[i].buffer = b""
                        pass


    def manageMessageReceived(self, peer):
        while len(peer.buffer) > 3:
            print 'w'
            if peer.hasHandshaked == False:
                peer.checkHandshake(peer.buffer)
                print 'hs'
                return

            msgLength = self.convertBytesToDecimal(peer.buffer[0:4],3)

            if len(peer.buffer) == 4:
                if msgLength == '\x00\x00\x00\x00':
                    print 'Keep alive'
                    return True
                print 'Keep alive2'
                return True


            msgCode = int(ord(peer.buffer[4:5]))
            payload = peer.buffer[5:4+msgLength]

            if len(payload) < msgLength-1:
                # Message is not complete. Return
                print 'not complete'
                return True

            peer.buffer = peer.buffer[msgLength+4:]

            if not msgCode:
                # Keep Alive. Keep the connection alive.
                print 'ka'
                continue

            elif msgCode == 0:
                # Choked
                #peer.choke()
                print 'chok'
                continue

            elif msgCode == 1:
                #peer.unchoke()
                #pipeRequests(peer, peerMngr)
                print 'unch'
                continue

            elif msgCode == 4:
                #handleHave(peer, payload)
                print "have"
                continue

            elif msgCode == 5:
                #peer.setBitField(payload)
                print "bitfield"
                continue

            elif msgCode == 7:
                #Piece
                print "piece"
                continue

            elif msgCode == 8:
                #Cancel
                print "Cancel"
                continue

            elif msgCode == 9:
                #Port
                print "port"
                continue

            else:
                print "else"
                return


    def convertBytesToDecimal(self,headerBytes, power):
        size = 0
        for ch in headerBytes:
            size += int(ord(ch))*256**power
            power -= 1
        return size