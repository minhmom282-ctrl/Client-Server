"""
HTTP Server Core - Lập trình Socket TCP đa luồng
Tự triển khai giao thức HTTP/1.1 trên nền TCP Socket thô (không dùng Flask, Django hay thư viện web có sẵn).
Tuân thủ đặc tả Use Case UC06, UC07, UC08, UC09, UC10, UC11, UC12.
"""
import os
import socket
import threading
import traceback
from typing import Callable, Optional, Dict, Any, Tuple
from common.config import DEFAULT_HOST, DEFAULT_PORT, REGISTER_PATH, LOG_FILE
from common.utils import validate_registration_data, get_current_timestamp
from server.user_manager import UserRepository
from server.request_handler import HTTPRequest, HTTPResponse


class HTTPServer:
    """
    Lớp điều khiển HTTP Server đa luồng.
    Lắng nghe kết nối TCP trên cổng 8888, phân phối mỗi Client vào một Thread riêng biệt.
    """
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, user_repo: Optional[UserRepository] = None):
        self.host = host
        self.port = port
        self.user_repo = user_repo or UserRepository()
        self.server_socket: Optional[socket.socket] = None
        self.is_running: bool = False
        self.accept_thread: Optional[threading.Thread] = None

        # Khóa đồng bộ số liệu thống kê
        self.stats_lock = threading.Lock()
        self.total_requests = 0
        self.success_count = 0
        self.conflict_count = 0
        self.error_count = 0
        self.active_clients = 0

        # Callbacks giao tiếp với GUI
        self.log_callback: Optional[Callable[[str, str], None]] = None
        self.stats_callback: Optional[Callable[[Dict[str, int]], None]] = None
        self.user_callback: Optional[Callable[[str, str], None]] = None
        self.state_callback: Optional[Callable[[bool], None]] = None

        # Đảm bảo thư mục log tồn tại
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """Ghi log sự kiện ra file và chuyển tiếp lên giao diện GUI"""
        timestamp = get_current_timestamp()
        log_entry = f"[{timestamp}] [{level:<7}] {message}"
        print(log_entry)

        # Ghi log vào file
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass

        # Gửi log lên GUI nếu có callback
        if self.log_callback:
            try:
                self.log_callback(log_entry, level)
            except Exception:
                pass

    def _notify_stats(self) -> None:
        """Cập nhật các chỉ số thống kê lên giao diện GUI"""
        if self.stats_callback:
            with self.stats_lock:
                stats = {
                    "total_requests": self.total_requests,
                    "success_count": self.success_count,
                    "conflict_count": self.conflict_count,
                    "error_count": self.error_count,
                    "active_clients": self.active_clients
                }
            try:
                self.stats_callback(stats)
            except Exception:
                pass

    def start(self) -> Tuple[bool, str]:
        """
        Khởi động HTTP Server (Use Case UC06).
        Tạo Socket TCP, gán vào cổng 8888 và bắt đầu lắng nghe kết nối.
        """
        if self.is_running:
            return False, "Server đang chạy rồi"

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Cho phép tái sử dụng cổng ngay sau khi đóng (SO_REUSEADDR)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(128)
            self.is_running = True

            # Chạy luồng lắng nghe accept kết nối
            self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.accept_thread.start()

            msg = f"Server đã khởi động thành công và đang lắng nghe trên cổng {self.port} (0.0.0.0)"
            self.log(msg, "SUCCESS")

            if self.state_callback:
                self.state_callback(True)
            self._notify_stats()
            return True, msg

        except Exception as e:
            self.is_running = False
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
                self.server_socket = None

            err_msg = f"Không thể mở cổng {self.port}: {e}"
            self.log(err_msg, "ERROR")
            if self.state_callback:
                self.state_callback(False)
            return False, err_msg

    def stop(self) -> Tuple[bool, str]:
        """
        Dừng HTTP Server (Use Case UC07).
        Ngừng chấp nhận kết nối mới, đóng socket và giải phóng cổng mạng.
        """
        if not self.is_running:
            return False, "Server chưa chạy"

        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        with self.stats_lock:
            self.active_clients = 0

        msg = "Server đã dừng hoạt động. Cổng mạng đã được giải phóng."
        self.log(msg, "WARNING")

        if self.state_callback:
            self.state_callback(False)
        self._notify_stats()
        return True, msg

    def _accept_loop(self) -> None:
        """Vòng lặp chấp nhận kết nối từ các máy khách (Client)"""
        while self.is_running:
            try:
                if not self.server_socket:
                    break
                client_sock, client_addr = self.server_socket.accept()
                with self.stats_lock:
                    self.active_clients += 1
                self._notify_stats()

                # Giao mỗi kết nối cho một Thread xử lý riêng (đa luồng)
                t = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                t.start()

            except (socket.error, OSError):
                # Socket đóng do stop()
                break
            except Exception as e:
                if self.is_running:
                    self.log(f"Lỗi trong vòng lặp tiếp nhận kết nối: {e}", "ERROR")

    def _handle_client(self, client_sock: socket.socket, client_addr: Tuple[str, int]) -> None:
        """
        Xử lý yêu cầu HTTP từ một Client trong luồng riêng (Use Case UC08).
        """
        addr_str = f"{client_addr[0]}:{client_addr[1]}"
        self.log(f"Client kết nối từ {addr_str}", "CLIENT")

        response: Optional[HTTPResponse] = None

        try:
            with self.stats_lock:
                self.total_requests += 1

            # 1. Phân tích gói tin HTTP Request
            req = HTTPRequest.parse_from_socket(client_sock)

            # 2. Xử lý các lỗi phân tích cú pháp (nếu có)
            if req.error_code:
                if req.error_code == 413:
                    response = HTTPResponse.payload_too_large(req.error_message)
                else:
                    response = HTTPResponse.bad_request(req.error_message)
                self._record_error()
                self.log(f"[{addr_str}] Yêu cầu không hợp lệ ({response.status_code}): {req.error_message}", "WARNING")

            # 3. Kiểm tra đường dẫn yêu cầu
            elif req.path != REGISTER_PATH:
                response = HTTPResponse.not_found(f"Đường dẫn '{req.path}' không tồn tại. Chỉ hỗ trợ {REGISTER_PATH}")
                self._record_error()
                self.log(f"[{addr_str}] 404 Not Found - Path sai: {req.path}", "WARNING")

            # 4. Kiểm tra phương thức yêu cầu (Chỉ chấp nhận POST)
            elif req.method != "POST":
                response = HTTPResponse.method_not_allowed(f"Phương thức '{req.method}' không được hỗ trợ. Vui lòng dùng POST")
                self._record_error()
                self.log(f"[{addr_str}] 405 Method Not Allowed - Phương thức: {req.method}", "WARNING")

            # 5. Xử lý nghiệp vụ đăng ký tài khoản
            else:
                params = req.params
                username = params.get("username", "")
                password = params.get("password", "")
                email = params.get("email", "")

                self.log(f"[{addr_str}] Nhận yêu cầu POST /register | User: '{username}' | Email: '{email}'", "INFO")

                # Kiểm tra tính hợp lệ dữ liệu (UC12)
                is_valid, validation_msg = validate_registration_data(username, password, email)
                if not is_valid:
                    response = HTTPResponse.bad_request(validation_msg)
                    self._record_error()
                    self.log(f"[{addr_str}] 400 Bad Request - {validation_msg}", "WARNING")
                else:
                    # Kiểm tra trùng và thêm user vào users.txt (UC09, UC10, UC11)
                    # Sử dụng atomic save trong UserRepository
                    status, save_msg = self.user_repo.save(username, password, email)
                    if status == "CREATED":
                        response = HTTPResponse.created(save_msg, username=username)
                        with self.stats_lock:
                            self.success_count += 1
                        self.log(f"[{addr_str}] 201 Created - Đăng ký thành công tài khoản '{username}'", "SUCCESS")

                        # Thông báo cập nhật danh sách người dùng cho GUI
                        if self.user_callback:
                            try:
                                self.user_callback(username, email)
                            except Exception:
                                pass
                    elif status == "CONFLICT":
                        # UC11: Thông báo user đã tồn tại
                        response = HTTPResponse.conflict(save_msg)
                        with self.stats_lock:
                            self.conflict_count += 1
                        self.log(f"[{addr_str}] 409 Conflict - Tên đăng nhập '{username}' đã được sử dụng", "WARNING")
                    else:
                        response = HTTPResponse.server_error(f"Lỗi ghi dữ liệu: {save_msg}")
                        self._record_error()
                        self.log(f"[{addr_str}] 500 Internal Error - {save_msg}", "ERROR")

            # 6. Gửi phản hồi HTTP về Client
            if response:
                resp_bytes = response.to_bytes()
                client_sock.sendall(resp_bytes)
                self.log(f"[{addr_str}] Đã gửi phản hồi HTTP {response.status_code} {response.status_text}", "INFO")

        except Exception as e:
            self._record_error()
            self.log(f"[{addr_str}] Ngoại lệ xử lý Client: {e}\n{traceback.format_exc()}", "ERROR")
            try:
                err_resp = HTTPResponse.server_error("Đã xảy ra lỗi không mong muốn trên Server")
                client_sock.sendall(err_resp.to_bytes())
            except Exception:
                pass

        finally:
            # 7. Đóng kết nối TCP theo mô hình Connection: close
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                client_sock.close()
            except Exception:
                pass

            with self.stats_lock:
                if self.active_clients > 0:
                    self.active_clients -= 1
            self._notify_stats()
            self.log(f"[{addr_str}] Đã đóng kết nối với Client", "CLIENT")

    def _record_error(self) -> None:
        """Ghi nhận yêu cầu lỗi"""
        with self.stats_lock:
            self.error_count += 1
