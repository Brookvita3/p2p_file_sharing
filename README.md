# Peer to Peer File Sharing

## Nội dung

Project này triển khai hệ thống chia sẻ tệp Peer-to-Peer (P2P) cho phép chia sẻ các peer dựa theo yêu cầu [BTL](). Project này được hiện thực dựa trên giao tiếp bằng socket và quản lý các peer bằng server. Kiến trúc thiết kế có thể xem tại [đây]()

## Cài đặt

1. Clone kho lưu trữ:
   ```bash
   git clone https://github.com/Brookvita3/p2p_file_sharing.git
   cd p2p_file_sharing
   ```
2. Cấu hình môi trường
   Tạo tệp `.env` trong thư mục gốc và thêm các biến sau:
   ```env
   DATABASE_URL= # link database để quản lý các peerr
   TRACKERPORT= # port giao tiếp với tracker
   PIECE_SIZE= # size của 1 peer
   TRACKERURL= # url của tracker
   ```
3. Cài đặt các phụ thuộc cần thiết và chạy tracker:
   ```bash
   python tracker.py
   ```
4. Khởi chạy peer:

```bash
python peer.py
```
