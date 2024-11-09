from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from utils import *
import certifi
import socket
from threading import Thread
import json
import bencodepy


# Create a new client and connect to the server
DATABASE_URL = "mongodb+srv://tranchinhbach:tranchinhbach@co3001.qkb5z.mongodb.net/?retryWrites=true&w=majority&appName=CO3001/"


class Tracker:
    def __init__(self, port):
        self.host = get_host_default()
        self.port = port

        self.tracker_socket: socket.socket = None

        self.database: MongoClient = None
        self.torrent_file: Collection = None
        self.files: Collection = None

        self.__thread: dict[str, Thread] = {}
        self.start()

    def start(self):

        # Connnect to database
        try:
            self.database = MongoClient(DATABASE_URL, tlsCAFile=certifi.where())[
                "tracker"
            ]
            self.torrent_file = self.database["torrentfiles"]
            self.files = self.database["listpeers"]

            print("Connected to MongoDB successfully.")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            self.shutdown()

        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_socket.bind((self.host, self.port))
        self.tracker_socket.listen(10)

        # self.get_all_files("a", "v", "get all files")

        while True:
            peer_socket, peer_addr = self.tracker_socket.accept()
            peer = Thread(target=self.handle_request, args=(peer_socket, peer_addr))
            print(f"connect from {peer_addr}")
            peer.start()

    def recieve_magnet(self, peer_socket: socket.socket, peer_addr, message):
        magnet_list = message.split(" ")
        address = (magnet_list[0], magnet_list[1])

        for magnet in magnet_list[2:]:
            existing_doc = self.files.find_one({"magnetText": magnet})
            if existing_doc:
                self.files.update_one(
                    {"magnetText": magnet},
                    {"$addToSet": {"list_peer": address}},
                )
            # else:
            #     document = {"magnetText": magnet, "list_peer": [address]}
            #     print(address)
            #     self.files.insert_one(document)
        print(f"recieve magnet {magnet_list} for {peer_addr}")

        peer_socket.send(f"Updated successfully".encode("utf-8"))

    def get_all_files(self, peer_socket: socket.socket, peer_addr, message):

        result = self.torrent_file.find({})
        names = [(doc["metaInfo"]["name"], doc["magnetText"]) for doc in result]
        print(names)

        print(f"get all files for {peer_addr}")

        peer_socket.send(str(names).encode("utf-8"))

    def peer_exit(self, peer_socket: socket.socket, peer_addr, message):

        data = message.split(" ")
        self.files.update_many({"list_peer": data}, {"$pull": {"list_peer": data}})
        print(f"peer exit {peer_addr}")

    def upload_file(self, peer_socket: socket.socket, peer_addr, message):

        data_list = message.split(" ", 2)

        addr = (data_list[0], data_list[1])

        data = json.loads(data_list[2])
        existing_document = self.torrent_file.find_one(
            {"magnetText": data["magnetText"]}
        )
        if existing_document:
            self.files.update_one(
                {"magnetText": data["magnetText"]},
                {"$addToSet": {"list_peer": addr}},
            )
            peer_socket.send(f"File already exists".encode("utf-8"))
            print("File already exists")
            return

        self.torrent_file.insert_one(data)
        self.files.insert_one(
            {
                "magnetText": data["magnetText"],
                "list_peer": [addr],
            },
        )

        print(f"upload file for {peer_addr}")
        peer_socket.send(f"Uploaded successfully".encode("utf-8"))

    def peer_download(self, peer_socket: socket.socket, peer_addr, message):

        data_list = message.split(" ", 2)
        addr = [data_list[0], data_list[1]]

        magnetText = data_list[2]

        torrent_file = self.torrent_file.find_one({"magnetText": magnetText})
        print(torrent_file)
        torrent_file.pop("_id")

        peer_list = self.files.find_one({"magnetText": magnetText})["list_peer"]

        peer_list = [peer for peer in peer_list if peer != addr]

        print(peer_list)

        data = {
            "torrent_file": torrent_file,
            "peer_list": peer_list,
        }
        message = json.dumps(data)
        # message = bencodepy.encode(data)
        # print(message)
        # peer_socket.sendall(message)

        peer_socket.sendall(message.encode("utf-8"))

        # upload peer to peer list
        self.files.update_one(
            {"magnetText": magnetText},
            {"$addToSet": {"list_peer": addr}},
        )

        print(f"Download file {magnetText} for {peer_addr}".encode("utf-8"))

    def handle_request(self, peer_socket: socket.socket, peer_addr):
        print(f"accept connect from {peer_addr}")
        message = peer_socket.recv(102400).decode("utf-8")

        if message == "FETCH ALL TORRENT":
            self.get_all_files(peer_socket, peer_addr, message)
        elif message.startswith("START"):
            self.recieve_magnet(peer_socket, peer_addr, message[6:])
        elif message.startswith("EXIT"):
            self.peer_exit(peer_socket, peer_addr, message[5:])
        elif message.startswith("UPLOAD"):
            self.upload_file(peer_socket, peer_addr, message[7:])
        elif message.startswith("DOWNLOAD"):
            self.peer_download(peer_socket, peer_addr, message[9:])

    def shutdown(self):
        for thread in self.__thread.values():
            thread.join()

        self.database.close()

    # b"asjdhkajshdalks333333dhlaskd asjdhkajshdalksdhl222222askd asjdhkajshdalksdhl111111askd "


if __name__ == "__main__":
    ip = get_host_default()
    print(ip)
    tracker = Tracker(65432)
