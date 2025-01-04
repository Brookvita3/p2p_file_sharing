# Peer to Peer File Sharing

## Nội dung
Project này triển khai hệ thống chia sẻ tệp Peer-to-Peer (P2P) cho phép chia sẻ các peer dựa theo yêu cầu [BTL](). Project này được hiện thực dựa trên giao tiếp bằng socket và quản lý các peer bằng server. Kiến trúc thiết kế có thể xem tại [đây]()

## Cài đặt
1. Clone kho lưu trữ:
   ```bash
   git clone https://github.com/Brookvita3/p2p_file_sharing.git
   cd p2p_file_sharing
   ```
2. Cài đặt các phụ thuộc cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy tracker:
   ```bash
   python tracker.py
   ```
4. Khởi chạy peer:
   ```bash
   python peer.py
   ```

## Sử dụng
- **Thêm một Peer:** Mỗi peer có thể tham gia mạng bằng cách kết nối với tracker.
- **Yêu cầu một Tệp:** Các peer có thể yêu cầu các tệp cụ thể, và hệ thống sẽ truy xuất chúng từ các peer khác.
- **Chia sẻ Tệp:** Các peer chia sẻ các tệp sẵn có của mình với mạng để người khác truy cập.
