__author__ = 'alexisgallepe'

import bencode
import requests
import struct,random,socket
from urlparse import urlparse

class Tracker(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.listPeers = []

    def getPeersFromTrackers(self):
        for tracker in self.torrent.announceList:
            if tracker[0][:4] == "http":
                self.getPeersFromTracker(tracker[0])
            else:
                rep = self.scrape_udp(self.torrent.info_hash, tracker[0], self.torrent.peer_id)
                if not rep == "":
                    self.parseTrackerResponse(rep)

        if len(self.listPeers) <= 0: print "Error, no peer available"
        return self.listPeers

    def getPeersFromTracker(self, tracker):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.torrent.peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent.length,
            'event': 'started'
        }
        answerTracker = requests.get(tracker, params=params, timeout=3)
        lstPeers = bencode.bdecode(answerTracker.text)
        self.parseTrackerResponse(lstPeers['peers'])
        print self.listPeers

    def parseTrackerResponse(self, peersByte):
        raw_bytes = [ord(c) for c in peersByte]
        for i in range(len(raw_bytes) / 6):
            start = i * 6
            end = start + 6
            ip = ".".join(str(i) for i in raw_bytes[start:end - 2])
            port = raw_bytes[end - 2:end]
            port = port[1] + port[0] * 256
            self.listPeers.append([ip, port])



    def make_connection_id_request(self):
        conn_id = struct.pack('>Q', 0x41727101980)
        action = struct.pack('>I', 0)
        trans_id = struct.pack('>I', random.randint(0, 100000))

        return (conn_id + action + trans_id, trans_id, action)

    def make_announce_input(self,info_hash, conn_id, peer_id):
        action = struct.pack('>I', 1)
        trans_id = struct.pack('>I', random.randint(0, 100000))

        downloaded = struct.pack('>Q', 0)
        left = struct.pack('>Q', 0)
        uploaded = struct.pack('>Q', 0)

        event = struct.pack('>I', 0)
        ip = struct.pack('>I', 0)
        key = struct.pack('>I', 0)
        num_want = struct.pack('>i', -1)
        port = struct.pack('>h', 8000)

        msg = (conn_id + action + trans_id + info_hash + peer_id + downloaded +
                left + uploaded + event + ip + key + num_want + port)

        return msg, trans_id, action

    def send_msg(self,conn, sock, msg, trans_id, action, size):
        sock.sendto(msg, conn)
        try:
            response = sock.recv(2048)
        except socket.timeout as err:
            print err
            return
            #logging.debug(err)
            #logging.debug("Connecting again...")
            return self.send_msg(conn, sock, msg, trans_id, action, size)
        if len(response) < size:
            #logging.debug("Did not get full message. Connecting again...")
            return self.send_msg(conn, sock, msg, trans_id, action, size)

        if action != response[0:4] or trans_id != response[4:8]:
            #logging.debug("Transaction or Action ID did not match. Trying again...")
            return self.send_msg(conn, sock, msg, trans_id, action, size)

        return response

    def scrape_udp(self,info_hash, announce, peer_id):
        print(announce)
        parsed = urlparse(announce)
        ip = socket.gethostbyname(parsed.hostname)

        if ip == '127.0.0.1':
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(8)
        conn = (ip, parsed.port)
        msg, trans_id, action = self.make_connection_id_request()
        response = self.send_msg(conn, sock, msg, trans_id, action, 16)
        if response == None:
            return ""

        conn_id = response[8:]
        msg, trans_id, action = self.make_announce_input(info_hash, conn_id, peer_id)
        response = self.send_msg(conn, sock, msg, trans_id, action, 20)

        return response[20:]