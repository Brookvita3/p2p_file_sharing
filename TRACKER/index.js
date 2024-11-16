const express = require("express");
const bodyParser = require("body-parser");
const connectDB = require("./config/config");
const trackerRoutes = require("./routes/APIendpoint");

// Kết nối MongoDB
connectDB();

// Tạo ứng dụng Express
const app = express();
app.use(bodyParser.json());

// Routes
app.use("/tracker", trackerRoutes);

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Tracker server running on http://localhost:${PORT}`);
});
