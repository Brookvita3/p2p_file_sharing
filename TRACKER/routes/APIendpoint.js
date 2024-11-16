const express = require("express");
const router = express.Router();
const ListPeer = require("../models/ListPeerModel");
const Torrent = require("../models/TorrentModel");
const { getLocalIp, splitIntoChunks } = require("../utils/utils");
const net = require("net");

// Function to handle socket data
async function handleSocketData(socket) {
  return new Promise((resolve, reject) => {
    let dataBuffer = "";

    socket.on("data", (chunk) => {
      console.log("Received chunk:", chunk.toString());
      dataBuffer += chunk.toString();
    });

    socket.on("end", () => {
      try {
        const torrentData = JSON.parse(dataBuffer);
        resolve(torrentData);
      } catch (error) {
        reject(new Error("Failed to parse torrent data: " + error.message));
      }
    });

    socket.on("error", (err) => {
      reject(err);
    });
  });
}

// Endpoint get all torrents: Trả về list MagnetText của tất cả torrents
router.get("/getAllTorrents", async (req, res) => {
  try {
    const torrents = await Torrent.find(
      {},
      "magnetText metaInfo.name description"
    );

    // Chuyển đổi kết quả thành mảng các đối tượng với `filename` và `magnetText`
    const result = torrents.map((t) => ({
      filename: t.metaInfo.name, // Lấy tên file từ `metaInfo.name`
      magnetText: t.magnetText,
      description: t.description,
    }));
    console.log(result);
    res.status(200).json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoint receive START message
// Cập nhật ListPeer của torrent tương ứng với MagnetText
router.post("/start", async (req, res) => {
  const { peerIp, peerPort, magnetList } = req.body;
  try {
    // Lặp qua từng magnetText trong danh sách magnetList
    for (const magnetText of magnetList) {
      // Kiểm tra xem magnetText có tồn tại không
      let listPeer = await ListPeer.findOne({ magnetText });

      // Nếu không tồn tại, bỏ qua và tiếp tục vòng lặp
      if (!listPeer) continue;

      // Kiểm tra xem peer đã tồn tại trong list_peer chưa
      const peerExists = listPeer.list_peer.some(
        (peer) => peer.peerIp === peerIp && peer.peerPort === peerPort
      );

      // Nếu peer chưa tồn tại, thêm peer mới vào list_peer
      if (!peerExists) {
        listPeer.list_peer.push({ peerIp, peerPort });
        await listPeer.save(); // Lưu thay đổi vào database
      }
    }
    console.log("Connect to peer: ", peerIp, peerPort);
    res.status(200).json({ message: "Peers updated successfully." });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoint receive UPLOAD message
// Lưu nội dung của Torrent vào database và cập nhật ListPeer của torrent mới
router.post("/upload", async (req, res) => {
  // Start a temporary socket server
  const { peerIp, peerPort } = req.body;
  const server = net.createServer(async (socket) => {
    console.log("Client connected via socket.");

    try {
      const torrentData = await handleSocketData(socket);

      console.log("Received torrent data:");

      const { magnetText } = torrentData;

      // Save torrent to database
      let torrent = await Torrent.findOne({ magnetText });
      if (!torrent) {
        const newTorrent = new Torrent(torrentData);
        await newTorrent.save();
        console.log("Torrent saved to database.");
      }

      // Update peer list
      let listPeerOfTorrent = await ListPeer.findOne({ magnetText });
      if (!listPeerOfTorrent) {
        listPeerOfTorrent = new ListPeer({
          magnetText,
          list_peer: [{ peerIp, peerPort }],
        });
      } else {
        listPeerOfTorrent.list_peer.push({ peerIp, peerPort });
      }
      await listPeerOfTorrent.save();
      console.log("Peer list updated:", { peerIp, peerPort });

      socket.write(
        JSON.stringify({ message: "Torrent uploaded successfully." })
      );
    } catch (error) {
      console.error("Error processing socket data:", error);
      socket.write(JSON.stringify({ error: error.message }));
    } finally {
      socket.end();
      server.close(() => {
        console.log("Socket server closed.");
      });
    }
  });

  // Listen on a dynamic port
  server.listen(0, () => {
    const address = server.address();
    const port = address.port;
    console.log(`Temporary socket server listening on port ${address.port}`);
    res
      .status(200)
      .json({ message: "Socket server ready.", port: address.port });
  });

  server.on("error", (err) => {
    console.error("Socket server error:", err);
    res.status(500).json({ error: "Failed to start socket server." });
  });
});

// Endpoint receive DOWNLOAD message
// Trả về ListPeer của torrent theo MagnetText
router.get("/download", async (req, res) => {
  const { peerIp, peerPort, magnetText } = req.body;
  try {
    const torrent = await Torrent.findOne({ magnetText });
    if (!torrent) {
      return res.status(404).json({ message: "There is no torrent" });
    }

    const listPeer = await ListPeer.findOne({ magnetText });
    let resList = [];

    if (!listPeer) {
      // Nếu không có listPeer, trả về torrent và danh sách peer rỗng
      res.status(200).json({
        torrent: torrent,
        listPeer: resList,
      });
    } else {
      // Tìm vị trí của peer trong list_peer
      const existingPeerIndex = listPeer.list_peer.findIndex(
        (peer) => peer.peerIp === peerIp && peer.peerPort === peerPort
      );

      // Tạo một bản sao của list_peer để trả về mà không bao gồm peer hiện tại
      resList = listPeer.list_peer.filter(
        (peer) => !(peer.peerIp === peerIp && peer.peerPort === peerPort)
      );

      if (existingPeerIndex === -1) {
        // Nếu peer chưa tồn tại, thêm peer mới vào list_peer trong database
        listPeer.list_peer.push({ peerIp, peerPort });
        await listPeer.save(); // Lưu thay đổi vào database
      }

      const socket = new net.Socket();
      socket.connect(5000, peerIp, () => {
        console.log("Connected to peer at ", peerIp, peerPort);

        // Send the torrent and list of peers as JSON
        const dataToSend = torrent;

        const jsonString = JSON.stringify(dataToSend);
        const chunks = splitIntoChunks(jsonString, 1024);

        // Function to send all chunks
        let chunkCount = 0;
        function sendChunk() {
          if (chunkCount < chunks.length) {
            console.log(`Sending chunk ${chunkCount + 1}:`, chunks[chunkCount]);
            socket.write(chunks[chunkCount]);
            chunkCount++;

            // Wait before sending the next chunk (50ms delay)
            setTimeout(sendChunk, 50); // You can adjust the delay as needed
          } else {
            // Close the socket after sending all chunks
            socket.end();
            console.log("All chunks sent, connection closed.");
          }
        }

        // Start sending the chunks
        sendChunk();
      });

      // Handle errors and close the connection if there are issues
      socket.on("error", (err) => {
        console.error("Socket error:", err);
        socket.end();
      });

      //   const ip = await getLocalIp();
      console.log("Download from peer: ", peerIp, peerPort);

      // Trả về torrent và listPeer không bao gồm peer hiện tại
      res.status(200).json({
        torrent: torrent,
        listPeer: resList,
      });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Endpoint receive EXIT message
// Xóa peerIp, peerPort khỏi ListPeer
router.post("/exit", async (req, res) => {
  const { peerIp, peerPort } = req.body;
  try {
    await ListPeer.updateMany(
      {},
      { $pull: { list_peer: { peerIp, peerPort } } }
    );
    res.status(200).json({ message: "Peer removed successfully." });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get("/ip", async (req, res) => {
  const ip = await getLocalIp();
  res.status(200).json({ ip: ip });
});

module.exports = router;
