from peer import Peer
import socket
from threading import Thread


class ClientSite:
    """Interface to interact with client with api (like response entity or DTO)"""

    def __init__(self, peer: Peer):
        self.peer = peer

    def start(self):
        """Start first connect to tracker"""
        # self.peer.start()
        self.peer.start_api()
        # print('hello')

    def get_all_file(self):
        """get all file from tracker"""

        # Files = self.peer.get_all_file()
        Files = self.peer.get_all_file_api()
        print(f"{'Name':<20} {'HashInfo'}")
        print("-" * 40)
        for file in Files:
            print(f"{file['filename']:<20} {file['magnetText']}")
        return Files

    def download(self, hashcode):
        """download with hashcode"""
        self.peer.download(hashcode)
        # self.peer.de

    def upload(self, filename):
        """upload torrent"""
        # self.peer.upload_Torrent(filename)
        self.peer.upload_api(filename)

    def exit(self, host, port):
        """exit app"""
        # self.peer.exit(host, port)
        self.peer.exit_api()

        # announce tracker to update peerlist
