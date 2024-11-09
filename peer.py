import socket
from threading import Thread, Lock
import json
import ast
import os
from dotenv import load_dotenv
from utils import *
import random
import time
import requests


class Peer:

    def __init__(self, peer_host, peer_port):
        self.running = True

        self.peer_host = peer_host
        self.peer_port = peer_port

        self.magnet_text_list = {}

    # ---------PEER CONNECTION INTERACTION-------------#

    def make_connection_to_peer(self, peer):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.settimeout(5)
        peer_socket.connect((peer[0], int(peer[1])))
        return peer_socket

    def download_status_from_peer(self, peer, data_torrent, status, lock):
        """Download the status"""
        addr = (peer["peerIp"], peer["peerPort"])
        peer_socket = self.make_connection_to_peer(addr)
        print(
            "Make connect to peer to get status {} : {}".format(
                peer["peerIp"], peer["peerPort"]
            )
        )
        message = "STATUS " + data_torrent["magnetText"]
        peer_socket.sendall(message.encode())
        res = peer_socket.recv(8192).decode("utf-8")
        res = res + " " + str(peer)

        with lock:
            status.append(res)
        peer_socket.close()

    def download_pieces_from_peer(
        self, ListPeer, piece_index, data_torrent, downloaded_status
    ):
        """Download the piece"""
        for peer in ListPeer:
            peer_socket = self.make_connection_to_peer(peer)
            print("Make connect to peer to get piece {} : {}".format(peer[0], peer[1]))
            message = "PIECE " + str(piece_index) + " " + data_torrent["magnetText"]
            peer_socket.sendall(message.encode())
            res = peer_socket.recv(8192)

            # debug
            with open("t.txt", "wb") as file:
                a = file.write(res)
                print(a)

            peer_socket.close()

            if create_temp_file(res, piece_index, data_torrent):
                downloaded_status[piece_index] = True
                break

    def DownloadProcess(self, peerList, data_torrent):
        """Handle download process for each peer in the peerList"""

        # get status

        threadsStatus = []
        threadsPiece = []
        list_status = []
        lock = Lock()
        # Tạo thread cho mỗi peer
        for peer in peerList:
            thread = Thread(
                target=self.download_status_from_peer,
                args=(peer, data_torrent, list_status, lock),
            )
            threadsStatus.append(thread)
            thread.start()

        # Chờ tất cả các thread hoàn thành
        for thread in threadsStatus:
            thread.join()
        print(list_status)
        piece_to_peer = contruct_piece_to_peers(list_status)
        print(piece_to_peer)

        # {0: true,
        #  1: fale }

        downloaded_status = [False] * len(piece_to_peer)
        timeout = time.time() + 10
        # get piece
        try:

            while time.time() < timeout:
                # while True:
                for piece_index in piece_to_peer:
                    if downloaded_status[piece_index] == False:
                        random.shuffle(piece_to_peer[piece_index])
                        print(piece_to_peer[piece_index])
                        thread = Thread(
                            target=self.download_pieces_from_peer,
                            args=(
                                piece_to_peer[piece_index],
                                piece_index,
                                data_torrent,
                                downloaded_status,
                            ),
                        )
                        threadsPiece.append(thread)
                        thread.start()

                for thread in threadsPiece:
                    thread.join()

                if False in downloaded_status:
                    continue
                else:
                    break

        except Exception as e:
            print("something when wrong in download process : {}".format(e))

        name = data_torrent["metaInfo"]["name"]
        merge_temp_files(name, data_torrent["metaInfo"]["name"])
        print("Download complete")

    def download(self, magnet_text):
        """Handle download"""
        try:
            # data_torrent, peer_list = self.download_torrent_from_tracker(magnet_text)
            data_torrent, peer_list = self.download_torrent_from_tracker_api(
                magnet_text
            )
            print(data_torrent)
            print(peer_list)
        except Exception as e:
            print("something err download: {}".format(e))
            return

        if data_torrent["magnetText"] not in self.magnet_text_list:
            filename = data_torrent["metaInfo"]["name"]
            filenameTorrent = filename.split(".")[0] + ".json"
            self.magnet_text_list[data_torrent["magnetText"]] = filenameTorrent
            create_torrent_file(filename, data_torrent)
        else:
            print("You already have torrent")

        print("Your download is being process, peerList: {}".format(peer_list))

        if len(peer_list) == 0:
            print("There's no seeder online now pls try nater")
            return

        downloadThread = Thread(
            target=self.DownloadProcess, args=(peer_list, data_torrent)
        )
        downloadThread.start()

    # -------------------------------------------------#

    # -------------PEER LISTENING INTERACTION------------#

    def handle_status(self, recv_socket: socket.socket, src_addr, magnetText):
        """Handle status"""
        filenameTorrent = self.magnet_text_list[magnetText]

        path = os.path.dirname(__file__)
        fullpath = os.path.join(path, "Torrent", filenameTorrent)
        try:
            with open(fullpath, "r") as file:
                torrent_file = file.read()
                status = check_file(json.loads(torrent_file))
                print(status)
                send_socket = recv_socket.sendall(str(status).encode("utf-8"))

        except Exception as e:
            print("something when wrong when handle status listen: {}".format(e))

    def listen(self):
        """
        Listen on the opening socket and create a new thread whenever it accepts a connection (listen peer connect ?!).
        """
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind((self.peer_host, self.peer_port))
        print("Succes listening")
        print(self.listen_socket.getsockname())
        self.listen_socket.listen(50)
        self.listen_socket.settimeout(10)
        while self.running:
            try:
                recv_socket, src_addr = self.listen_socket.accept()

                print("connected from {}".format(src_addr))
                message = recv_socket.recv(8192).decode("utf-8")

                handle_listen = Thread(
                    target=self.handle_listen, args=(recv_socket, src_addr, message)
                )
                handle_listen.start()

            except Exception:
                continue

    def handle_listen(self, recv_socket: socket.socket, src_addr, message):
        if message.startswith("STATUS"):
            self.handle_status(recv_socket, src_addr, message[7:])
        else:
            self.handle_piece(recv_socket, src_addr, message[6:])

    def handle_piece(self, recv_socket: socket.socket, src_addr, message):
        """send piece"""
        print("--------piece dowload------")
        piece_index, magnet_text = message.split(" ")

        filenameTorrent = self.magnet_text_list[magnet_text]

        piece_index = int(piece_index)

        path = os.path.dirname(__file__)

        torrent_file = json.loads(
            open(os.path.join(path, "Torrent", filenameTorrent), "r").read()
        )

        filename = torrent_file["metaInfo"]["name"]
        piece_size = int(torrent_file["metaInfo"]["piece_size"])

        fullpath = os.path.join(path, "MyFolder", filename)
        piece = None
        with open(fullpath, "rb") as file:
            # for index in range(piece_index+1):
            #     piece = file.read(piece_size)
            file.seek(piece_index * piece_size)
            piece = file.read(piece_size)

            if (
                check_sum_piece(piece, torrent_file["metaInfo"]["pieces"], piece_index)
                == False
            ):
                recv_socket.sendall(str("False").encode("utf-8"))
            else:
                recv_socket.sendall(piece)

    # -------------------------------------------#

    # ---------------------------------------------------#

    # -----------TRACKER INTERACTION-------------#

    def start(self):
        """start server listen thread"""
        print(trackerIP, trackerPort)
        self.send_torrent_hashcodes(trackerIP, trackerPort)
        listen_thread = Thread(target=self.listen, args=())
        listen_thread.start()

    def send_torrent_hashcodes(self, trackerIP, trackerPort):

        # Lấy danh sách các tệp trong thư mục Torrent
        self.magnet_text_list = get_magnetTexts_from_torrent()
        keys = list(self.magnet_text_list.keys())
        if len(keys) == 0:
            return

        try:
            tracker_socket = self.make_connection_to_tracker()
            print(
                f"Connected to tracker for sending hashcodes {trackerIP}:{trackerPort}"
            )

            # Gửi danh sách hashcode cho tracker
            message = (
                "START"
                + " "
                + self.peer_host
                + " "
                + str(self.peer_port)
                + " "
                + " ".join(keys)
            )
            print(message)
            tracker_socket.sendall(f"{message}".encode())
            print(tracker_socket.recv(8192).decode())
            tracker_socket.close()
            print("Sent success")
        except Exception as e:
            print("something when wrong when start : {}".format(e))

    def get_all_file(self):
        """Fetch all file from Tracker"""

        try:
            tracker_socket = self.make_connection_to_tracker()
            print(f"Connected to get all file {trackerIP}:{trackerPort}")

            message = "FETCH ALL TORRENT"
            tracker_socket.sendall(message.encode())
            res = tracker_socket.recv(8192).decode("utf-8")
            Files = ast.literal_eval(res)
            tracker_socket.close()
            return Files
        except Exception as e:
            print("something when wrong when get all file: {}".format(e))
            return []

    def upload_Torrent(self, filename):  # .txt
        """upload torrent for tracker"""
        try:
            tracker_socket = self.make_connection_to_tracker()
            print("connected to upload file")
            data = generate_Torrent(filename)
            if data is None:
                return

            message = (
                "UPLOAD " + self.peer_host + " " + str(self.peer_port) + " " + data
            )
            print(message)
            tracker_socket.sendall(message.encode())

            res = tracker_socket.recv(8192).decode("utf-8")
            if res != "File already exists":
                create_torrent_file(filename, json.loads(data))

            magnet_text = json.loads(data)["magnetText"]
            filenameTorrent = filename.split(".")[0] + ".json"
            self.magnet_text_list[magnet_text] = filenameTorrent
            print(self.magnet_text_list)
            tracker_socket.close()
        except Exception as e:
            print("something when wrong when Upload file: {}".format(e))

    def make_connection_to_tracker(self):
        """connect to tracker"""
        tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_socket.settimeout(2)
        tracker_socket.connect((trackerIP, trackerPort))
        return tracker_socket

    def download_torrent_from_tracker(self, magnet_text):
        try:
            tracker_socket = self.make_connection_to_tracker()
            print(
                f"Connected to tracker for download torrent {trackerIP}:{trackerPort}"
            )

            message = (
                "DOWNLOAD "
                + self.peer_host
                + " "
                + str(self.peer_port)
                + " "
                + magnet_text
            )
            print(message)
            tracker_socket.sendall(message.encode())

            #  hanlde respond from tracker

            res = tracker_socket.recv(8192).decode("utf-8")
            # data = bencodepy.decode(res)
            # print(json.loads(data))
            data_torrent = json.loads(res)["torrent_file"]
            print(type(data_torrent))
            data_list = json.loads(res)["peer_list"]
            print(type(data_list))

            tracker_socket.close()
            return data_torrent, data_list
        except Exception as e:
            print("something when wrong when download torrent : {}".format(e))

    def exit(self, host, port):
        try:
            tracker_socket = self.make_connection_to_tracker()
            message = "EXIT" + " " + host + " " + str(port)
            tracker_socket.sendall(message.encode())
            tracker_socket.close()
            self.running = False
            print("Exit success")
        except Exception as e:
            self.running = False
            print("something when wrong when exit")

    # -------------------------------------------#
    # -----------TRACKER INTERACTION WITH API HTTP-------------#

    def start_api(self):
        url = "http://localhost:3000/tracker/start"
        lists = get_magnetTexts_from_torrent()
        self.magnet_text_list = lists
        print(type(lists))
        list = [listM for listM in lists]
        print(list)
        params = {
            "peerIp": self.peer_host,
            "peerPort": self.peer_port,
            "magnetList": list,
        }

        response = requests.post(url, json=params)
        print(response.json())

        listen_thread = Thread(target=self.listen, args=())
        listen_thread.start()

    def get_all_file_api(self):
        url = "http://localhost:3000/tracker/getAllTorrents"
        response = requests.get(url)
        return response.json()

    def exit_api(self):
        self.running = False
        url = "http://localhost:3000/tracker/exit"
        param = {"peerIp": self.peer_host, "peerPort": self.peer_port}
        response = requests.post(url, json=param)
        print(response.json())

    def upload_api(self, filename):
        try:
            data = generate_Torrent(filename)
            if data is None:
                return

            url = "http://localhost:3000/tracker/upload"

            data = json.loads(data)
            param = {
                "peerIp": self.peer_host,
                "peerPort": self.peer_port,
                "Torrent": data,
            }

            response = requests.post(url, json=param)
            if response.status_code != 409:
                create_torrent_file(filename, data)

            magnet_text = data["magnetText"]
            filenameTorrent = filename.split(".")[0] + ".json"
            self.magnet_text_list[magnet_text] = filenameTorrent
        except Exception as e:
            print("something wrong when upload file: {}".format(e))

    def download_torrent_from_tracker_api(self, magnetText):
        url = "http://localhost:3000/tracker/download"
        param = {
            "peerIp": self.peer_host,
            "peerPort": self.peer_port,
            "magnetText": magnetText,
        }
        response = requests.get(url, json=param)

        data_torent = response.json()["torrent"]
        peerlist = response.json()["listPeer"]

        return data_torent, peerlist
