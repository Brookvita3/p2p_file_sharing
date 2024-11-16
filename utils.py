import socket
import hashlib
import os
from dotenv import load_dotenv
import json
import ast

load_dotenv()
trackerIP = os.getenv("TRACKERIP")
trackerPort = int(os.getenv("TRACKERPORT"))
pieceSize = int(os.getenv("PIECE_SIZE"))


def get_host_default():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        print("err when get host default")
        return None
    finally:
        s.close()
    return ip


def make_attribute_torrent(filename, piece_size=pieceSize):  # .txt
    path = os.path.dirname(__file__)
    fullpath = os.path.join(path, "MyFolder", filename)

    piece_hashes = []
    hashinfo = hashlib.sha256()
    if not os.path.isfile(fullpath):
        print("File is not exist")
        raise Exception
    size = os.stat(fullpath).st_size

    with open(fullpath, "rb") as f:
        while True:
            piece = f.read(piece_size)
            if not piece:
                break
            # piece = piece.encode()
            piece_hash = hashlib.sha256(piece).hexdigest()
            piece_hashes.append(piece_hash)
            hashinfo.update(piece_hash.encode())

    return hashinfo.hexdigest(), piece_hashes, size, piece_size


def generate_Torrent(filename, description: str):
    try:
        magnet_text, pieces, size, piece_size = make_attribute_torrent(filename)  # .txt
    except Exception:
        return
    data = {
        "trackerIp": trackerIP,
        "magnetText": magnet_text,
        "description": description,
        "metaInfo": {
            "name": filename,
            "filesize": size,
            "piece_size": piece_size,
            "pieces": pieces,
        },
    }
    return json.dumps(data)


def get_magnetTexts_from_torrent():
    path = os.path.dirname(__file__)
    fullpath = os.path.join(path, "Torrent")

    # Lấy danh sách các tệp trong thư mục Torrent
    hashcodes = {}
    files = os.listdir(fullpath)
    json_files = [file for file in files if file.endswith(".json")]

    for file_name in json_files:
        hashcode = get_hashcode(fullpath, file_name)
        if hashcode is not None:
            hashcodes[hashcode] = file_name

    return hashcodes


def get_hashcode(fullpath, file_name):
    try:
        with open(os.path.join(fullpath, file_name), "r") as file:
            data = json.load(file)
            hashcode = data.get("magnetText", None)
            if hashcode is not None:
                return hashcode
            else:
                raise Exception("khong co hashcode")
    except json.JSONDecodeError:
        print(f"Lỗi định dạng JSON trong tệp {file_name}. Bỏ qua tệp này.")
    except Exception as e:
        print(f"Lỗi khi đọc tệp {file_name}: {e}")


def create_torrent_file(file_name, data_torrent):
    """Tạo một tệp .json mới từ dữ liệu JSON."""
    path = os.path.dirname(__file__)
    file_name = file_name.split(".")[0] + ".json"
    fullpath = os.path.join(path, "Torrent", file_name)
    with open(fullpath, "w") as json_file:
        json.dump(data_torrent, json_file, indent=4)
    print(f"Tệp {file_name} đã được tạo thành công.")


def create_temp_file(data: bytes, piece_index, torrent):
    """tao temp file cho piece"""
    # check sum + create file tmp
    if check_sum_piece(data, torrent["metaInfo"]["pieces"], piece_index):

        path = os.path.dirname(__file__)
        file_name = torrent["metaInfo"]["name"] + "_" + str(piece_index) + ".tmp"
        fullpath = os.path.join(path, "Temp", file_name)

        with open(fullpath, "wb") as f:
            f.write(data)
        print(f"Tệp {file_name}.tmp đã được tạo thành công.")

        return True

    else:
        print("data loi khi check sum.")
        return False


def check_sum_piece(data: bytes, listPiece, piece_index):
    """check"""
    # hashPiece = hashlib.sha1(data.encode()).hexdigest()
    hashPiece = hashlib.sha256(data).hexdigest()
    print(hashPiece, piece_index)
    if hashPiece == listPiece[piece_index]:
        return True
    else:
        return False


def check_file(torrent_file):
    status = []
    path = os.path.dirname(__file__)
    filename = torrent_file["metaInfo"]["name"]
    fullpath = os.path.join(path, "MyFolder", filename)
    index = 0
    with open(fullpath, "rb") as file:
        while True:
            piece = file.read(torrent_file["metaInfo"]["piece_size"])
            # print(piece)
            if not piece:
                break
            status.append(
                check_sum_piece(piece, torrent_file["metaInfo"]["pieces"], index)
            )
            index = index + 1

    return status


def merge_temp_files(output_file, filename):
    """Gộp tất cả các tệp .tmp trong thư mục temp thành một tệp duy nhất."""
    path = os.path.dirname(__file__)
    fullpath = os.path.join(path, "Download", output_file)

    with open(fullpath, "wb") as outfile:
        # Lấy danh sách tất cả các tệp .tmp trong thư mục temp và sắp xếp chúng
        temp_files = sorted(
            [
                f
                for f in os.listdir(os.path.join(path, "Temp"))
                if f.endswith(".tmp") and f.startswith(filename)
            ],
            key=lambda x: int(x.split("_")[1].split(".")[0]),
        )  # Giả sử tên tệp có dạng 'piece_1.tmp'

        # Duyệt qua từng tệp .tmp và ghi nội dung vào tệp đích
        for temp_file in temp_files:
            temp_file_path = os.path.join(os.path.join(path, "Temp"), temp_file)
            with open(temp_file_path, "rb") as infile:
                outfile.write(infile.read())  # Đọc và ghi toàn bộ nội dung vào tệp đích

    print(f"Đã gộp tất cả các tệp .tmp thành tệp duy nhất: {output_file}")


def contruct_piece_to_peers(data: list):
    peers = []
    for entry in data:
        # Split into piece availability and peer info
        piece_availability, peer_info = entry.split("] {")
        piece_availability = piece_availability + "]"
        peer_info = "{" + peer_info

        piece_availability = ast.literal_eval(piece_availability)
        peer_info = ast.literal_eval(peer_info)
        peers.append((piece_availability, peer_info))

    print(peers)
    # [([True, True], {'peerIp': '192.168.244.43', 'peerPort': 1000})]

    # Create a dictionary of pieces to the peers who have them
    piece_count = len(peers[0][0])
    piece_to_peers = {}
    for i in range(piece_count):
        piece_to_peers[i] = []
        for availability_list, peer_info in peers:
            if availability_list[i]:
                data = [peer_info["peerIp"], str(peer_info["peerPort"])]
                piece_to_peers[i].append(data)

    return piece_to_peers


def clear_temp_files():
    path = os.path.dirname(__file__)
    folder_path = os.path.join(path, "Temp")
    try:
        # Get list of all files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):  # Ensure it's a file, not a subfolder
                os.remove(file_path)
        print("All files deleted.")
    except Exception as e:
        print(f"An error occurred when delete file in Temp folder: {e}")
