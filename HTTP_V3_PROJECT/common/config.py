"""
Cấu hình hệ thống Client - Server HTTP v3
Đồ án Lập trình Hệ thống Mạng - Nhóm 6
"""
import os

# Cấu hình mạng
DEFAULT_HOST = "0.0.0.0"       # Server lắng nghe trên mọi card mạng
DEFAULT_CLIENT_HOST = "127.0.0.1"  # Client kết nối mặc định localhost
DEFAULT_PORT = 8888            # Cổng TCP 8888 theo đặc tả đồ án

# Đường dẫn API
REGISTER_PATH = "/register"

# Timeout mạng (giây) - theo đặc tả Use Case UC04, UC08 (10 giây)
NETWORK_TIMEOUT = 10.0

# Giới hạn kích thước payload (1MB) - chống tấn công làm cạn kiệt bộ nhớ (413 Payload Too Large)
MAX_PAYLOAD_SIZE = 1024 * 1024 

# Định danh thư mục gốc của dự án
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Đường dẫn file dữ liệu users.txt
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.txt")

# Đường dẫn file nhật ký log
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "server.log")

# Định dạng Content-Type hỗ trợ
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
CONTENT_TYPE_JSON = "application/json"

# Mã trạng thái HTTP chuẩn
HTTP_STATUS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    500: "Internal Server Error"
}
