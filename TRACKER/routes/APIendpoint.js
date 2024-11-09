const express = require("express");
const router = express.Router();
const ListPeer = require("../models/ListPeerModel");
const Torrent = require("../models/TorrentModel")

// Endpoint get all torrents: Trả về list MagnetText của tất cả torrents
router.get("/getAllTorrents", async (req, res) => {
    try {
        const torrents = await Torrent.find({}, 'magnetText metaInfo.name');
        
        // Chuyển đổi kết quả thành mảng các đối tượng với `filename` và `magnetText`
        const result = torrents.map(t => ({
            filename: t.metaInfo.name, // Lấy tên file từ `metaInfo.name`
            magnetText: t.magnetText
        }));

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
        res.status(200).json({ message: "Peers updated successfully." });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Endpoint receive UPLOAD message
// Lưu nội dung của Torrent vào database và cập nhật ListPeer của torrent mới
router.post("/upload", async (req, res) => {
    const {peerIp, peerPort, Torrent: torrentData }= req.body;
    try {
        const { magnetText } = torrentData;
        let torrent = await Torrent.findOne({ magnetText });
        if(!torrent){
            const newTorrent = new Torrent(torrentData);
            await newTorrent.save();
        }
        else{
            return res.status(409).json({ error: "already have on server" });
        }

        let listPeerOfTorrent = await ListPeer.findOne({ magnetText });
        
        if (!listPeerOfTorrent) {
            listPeerOfTorrent = new ListPeer({ magnetText, list_peer: [{ peerIp: peerIp, peerPort: peerPort }] });
        }
        else{
            listPeerOfTorrent.list_peer.push({ peerIp, peerPort })
        }
        await listPeerOfTorrent.save();

        res.status(200).json({ message: "Torrent uploaded successfully." });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
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
                listPeer: resList
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

            // Trả về torrent và listPeer không bao gồm peer hiện tại
            res.status(200).json({
                torrent: torrent,
                listPeer: resList
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

module.exports = router;
