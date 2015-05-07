__author__ = 'alexisgallepe'

import bencode
import requests

class Tracker(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.listPeers=[]

    def getPeersFromTrackers(self):
        for tracker in self.torrent.announceList:
            if tracker[0][:4] == "http":
                try:
                    self.getPeersFromTracker(tracker[0])
                except:
                    pass

        if len(self.listPeers)<=0: print "Error, no peer available"
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


    def parseTrackerResponse(self, peersByte):
        raw_bytes = [ord(c) for c in peersByte]
        for i in range(len(raw_bytes) / 6):
            start = i * 6
            end = start + 6
            ip = ".".join(str(i) for i in raw_bytes[start:end - 2])
            port = raw_bytes[end - 2:end]
            port = port[1] + port[0] * 256
            self.listPeers.append([ip, port])