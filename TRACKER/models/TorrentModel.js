const mongoose = require('mongoose');

const TorrentSchema = new mongoose.Schema({
    trackerIp: { type: String, required: true },
    magnetText: { type: String, required: true },
    metaInfo: {
        name: { type: String, required: true },
        filesize: { type: Number, required: true },
        piece_size: { type: Number, required: true },
        pieces: [{ type: String, required: true }, { _id: false }]
    }
});

module.exports = mongoose.model('torrentfile', TorrentSchema);
