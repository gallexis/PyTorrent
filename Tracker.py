__author__ = 'alexisgallepe'

import bencode
import requests
import logging
import struct,random,socket
from urlparse import urlparse
import threading,time

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)

class Tracker(object):
    def __init__(self, torrent, newpeersQueue):
        self.torrent = torrent
        self.lstThreads =  []
        self.newpeersQueue = newpeersQueue
        self.getPeersFromTrackers()

    def getPeersFromTrackers(self):
        for tracker in self.torrent.announceList:
            if tracker[0][:4] == "http":
                t1 = FuncThread(self.scrapeHTTP, self.torrent,tracker[0])
                self.lstThreads.append(t1)
                t1.start()
            else:
                t2 = FuncThread(self.scrape_udp, self.torrent, tracker[0])
                self.lstThreads.append(t2)
                t2.start()

        for t in self.lstThreads:
            t.join()


    def scrapeHTTP(self, torrent, tracker):

        params = {
            'info_hash': torrent.info_hash,
            'peer_id': torrent.peer_id,
            'uploaded': 0,
            'downloaded': 0,
            'left': torrent.totalLength,
            'event': 'started'
        }
        try:
            answerTracker = requests.get(tracker, params=params, timeout=3)
            lstPeers = bencode.bdecode(answerTracker.text)
            self.parseTrackerResponse(lstPeers['peers'])
        except:
            pass

    def parseTrackerResponse(self, peersByte):
        raw_bytes = [ord(c) for c in peersByte]
        for i in range(len(raw_bytes) / 6):
            start = i * 6
            end = start + 6
            ip = ".".join(str(i) for i in raw_bytes[start:end - 2])
            port = raw_bytes[end - 2:end]
            port = port[1] + port[0] * 256
            self.newpeersQueue.put([ip, port])


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
            logging.debug(err)
            return
            #logging.debug("Connecting again...")
            #return self.send_msg(conn, sock, msg, trans_id, action, size)
        if len(response) < size:
            logging.debug("Did not get full message. Connecting again...")
            return self.send_msg(conn, sock, msg, trans_id, action, size)

        if action != response[0:4] or trans_id != response[4:8]:
            logging.debug("Transaction or Action ID did not match. Trying again...")
            return self.send_msg(conn, sock, msg, trans_id, action, size)

        return response

    def scrape_udp(self,torrent, announce):
        try:
            parsed = urlparse(announce)
            ip = socket.gethostbyname(parsed.hostname)

            if ip == '127.0.0.1':
                return False
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            conn = (ip, parsed.port)
            msg, trans_id, action = self.make_connection_id_request()
            response = self.send_msg(conn, sock, msg, trans_id, action, 16)
            if response == None:
                return ""

            conn_id = response[8:]
            msg, trans_id, action = self.make_announce_input(torrent.info_hash, conn_id, torrent.peer_id)
            response = self.send_msg(conn, sock, msg, trans_id, action, 20)
            if response == None or response == "":
                return ""

            self.parseTrackerResponse(response[20:])
        except:
            pass