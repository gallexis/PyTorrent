__author__ = 'alexisgallepe'

import PiecesManager


class FilesManager(object):
    def __init__(self, torrent):
        self.torrent = torrent
        self.allFilesCompleted = False
        self.files = []

        # if one file
        if 'files' in torrent['info']:
            # nameFiles = torrent['files']['path']
            raise ('To be completed')

        else:
            fileName = torrent['info']['name']
            file = PiecesManager.PiecesManager(torrent, fileName)
            self.files.append(file)

    def filesManager(self):
        while not self.allFilesCompleted:
            for file in self.files:
                file.doAction()

            self.checkIfAllFilesCompleted()

    def checkIfAllFilesCompleted(self):
        allFilesCompleted = True
        for file in self.files:
            if file.arePiecesCompleted:
                self.files.remove(file)
            else:
                allFilesCompleted = False

        return allFilesCompleted
