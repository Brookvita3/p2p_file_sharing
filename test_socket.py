import socket
from utils import *
import json
import ast

data = {
    "trackerIp": "192.168.244.43",
    "magnetText": "de9606a4a16a251304dd0095a00f86419cf01",
    "metaInfo": {
        "name": "text.txt",
        "filesize": 24,
        "piece_size": 4,
        "pieces": [
            "776351ef196dbed5844a1140802b855498d7d81e",
            "c4269587151954eb6574fde71423650831ffb111",
            "19c96b9957f3491ac5881c52c163dfe4b481c3ff",
            "2ed618ae9167374fef1859a846a389ccf4a08427",
            "61dce8dc32a68b6793698881bfd9d244cf5dfc41",
            "a78fc6756af3b204c8dfe1635b2cb47ac71ae988",
        ],
    },
}


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = get_host_default()
print(ip)
s.connect((ip, 65432))
message1 = "START 17.0.1 10 sadkasd asmdasmd"
message2 = "EXIT 17.0.1 10"

# Chuyển đổi dữ liệu thành chuỗi JSON
json_data = json.dumps(data)
message3 = "UPLOAD " + json_data
message4 = "FETCH ALL TORRENT"

message5 = "DOWNLOAD fa3b79a6fded16aed27d3051c9b2ec779e9a3e1a"
message6 = """UPLOAD {"trackerIp": "10.10.2.182", "magnetText": "5f7124f698afa29f5780043bc62144767ba5af7c", "metaInfo": {"name": "text3", "filesize": 80, "piece_size": 4, "pieces": ["776351ef196dbed5844a1140802b855498d7d81e", "c4269587151954eb6574fde71423650831ffb111", "19c96b9957f3491ac5881c52c163dfe4b481c3ff", "2ed618ae9167374fef1859a846a389ccf4a08427", "61dce8dc32a68b6793698881bfd9d244cf5dfc41", "a78fc6756af3b204c8dfe1635b2cb47ac71ae988", "910091cc05b9bd57820c2d1d921f6a7a3fa9bca5", "eef18771dac22e9d6bcb29f8620208e8ea1667b0", "596daf0c25a72e2ae114e58b66b3235d9fc96386", "69c298569e8d5bd04d1bbc406cdb5c1699cee7a0", "072c2548bb86a8838bbe10ec453731f4b1455832", "1caa5d9074f0e44d4d732a47b14f122e2b478031", "db9997ca8f6baa3fedda7d5a2ae270832c017b04", "80834a9cf51a8c3faed6af74e3943fc9f9fad018", "5a42fc4be595215857c41c5eee869087f5a30c19", "072c2548bb86a8838bbe10ec453731f4b1455832", "bc32e211aaec9d99e3ebecf377d0944ec5ec3637", "5e37028beac0f0d8c6640021fc13643313ef3e3f", "cf217d30e8b6734c61d5367049dec6207e80018e", "cde5911439b1bf1db82642e6e4ae76bdc44c048a"]}}"""

# s.send(message6.encode("utf-8"))
# split_file("./MyFolder/text3", "./temp", meta)
# print(x)
# x = send_status("./temp", meta)
# print(x)
# meta = generate_Torrent("./MyFolder/text4")
# print(meta)

# data = [
#     "[True, True, True, True, True] [[True, True, True, True, True'10.20.1.83', '2000']",
#     "[True, True, True, False, True] ['10.20.1.83', '1000']",
# ]


# peers = []
# for entry in data:
#     # Split into piece availability and peer info
#     piece_availability, peer_info = entry.split("] [")
#     piece_availability = ast.literal_eval(piece_availability + "]")
#     peer_info = ast.literal_eval("[" + peer_info)[0]
#     peers.append((piece_availability, peer_info))


# # Create a dictionary of pieces to the peers who have them
# piece_to_peers = {
#     i: [
#         peer_info  # Store the actual peer IP and port tuple
#         for availability_list, peer_info in peers
#         if availability_list[i]  # Only include peer if they have the piece
#     ]
#     for i in range(
#         len(peers[0][0])
#     )  # Iterate through the number of pieces (based on the first peer's list)
# }

# print(piece_to_peers)


data = [
    "[True, True, True, True, True] ['10.20.1.83', '2000']",
    "[True, True, True, False, True] ['10.20.1.83', '1000']",
]


def contruct_map_for_download(data):
    peers = []
    for entry in data:
        # Split into piece availability and peer info
        piece_availability, peer_info = entry.split("] [")

        piece_availability = ast.literal_eval(piece_availability + "]")

        peer_info = ast.literal_eval("[" + peer_info)
        peers.append((piece_availability, peer_info))
        print(piece_availability)
        print(peer_info)

    # Create a dictionary of pieces to the peers who have them
    piece_to_peers = {
        i: [peer_info for availability_list, peer_info in peers if availability_list[i]]
        for i in range(len(peers[0][0]))
    }
    return piece_to_peers


magnet_text = open(os.path.join("./Torrent", "text4.json"), "r").read()
print(magnet_text)

{
    0: [["10.20.1.83", "1000"]],
    1: [["10.20.1.83", "1000"]],
    2: [["10.20.1.83", "1000"]],
    3: [["10.20.1.83", "1000"]],
    4: [["10.20.1.83", "1000"]],
}
