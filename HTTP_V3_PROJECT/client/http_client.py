"""
HTTP Client Core - Lập trình Socket TCP thuần
Tự tạo yêu cầu HTTP/1.1 POST và phân tích HTTP Response từ Socket TCP.
Tuân thủ đặc tả Use Case UC03, UC04, UC05 và Sơ đồ lớp (Class Diagram).
"""
import socket
import json
from typing import Tuple, Dict, Any, Optional
from common.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT, REGISTER_PATH, NETWORK_TIMEOUT, CONTENT_TYPE_FORM, CONTENT_TYPE_JSON
from common.utils import encode_form_urlencoded


class HTTPClient:
    """
    HTTP Client tương tác với Server qua TCP Socket.
    Hỗ trợ hai chế độ đóng gói: Form URL-encoded (mặc định) và JSON.
    """
    def __init__(self, host: str = DEFAULT_CLIENT_HOST, port: int = DEFAULT_PORT, is_json_mode: bool = False):
        self.host = host
        self.port = port
        self.is_json_mode = is_json_mode
        self.timeout = NETWORK_TIMEOUT

    def package_data(self, username: str, password: str, email: str, use_json: Optional[bool] = None) -> Tuple[Dict[str, str], str]:
        """
        Đóng gói dữ liệu đăng ký thành Body và Headers tương ứng (UC03).
        - use_json: True -> JSON (application/json)
        - use_json: False -> Form URL-encoded (application/x-www-form-urlencoded)
        """
        if use_json is None:
            use_json = self.is_json_mode

        data_dict = {
            "username": username,
            "password": password,
            "email": email
        }

        if use_json:
            body = json.dumps(data_dict, ensure_ascii=False)
            content_type = CONTENT_TYPE_JSON
        else:
            body = encode_form_urlencoded(data_dict)
            content_type = CONTENT_TYPE_FORM

        headers = {
            "Host": f"{self.host}:{self.port}",
            "Content-Type": content_type,
            "Connection": "close"
        }
        return headers, body

    def send_register_request(self, username: str, password: str, email: str, use_json: Optional[bool] = None) -> Tuple[int, str, Dict[str, Any], str]:
        """
        Kết nối TCP tới Server, gửi HTTP POST /register và nhận kết quả (UC04).
        Trả về:
            (status_code, status_text, response_json_dict, raw_response_body)
        """
        headers, body = self.package_data(username, password, email, use_json)
        return self.send_custom_request(method="POST", path=REGISTER_PATH, headers=headers, body=body)

    def send_custom_request(self, method: str = "POST", path: str = REGISTER_PATH, headers: Optional[Dict[str, str]] = None, body: str = "") -> Tuple[int, str, Dict[str, Any], str]:
        """
        Gửi yêu cầu HTTP tùy chỉnh qua TCP Socket và phân tích Response.
        Hỗ trợ kiểm thử các phương thức GET, POST, sai path, v.v.
        """
        headers = headers or {}
        if "Host" not in headers:
            headers["Host"] = f"{self.host}:{self.port}"
        if "Connection" not in headers:
            headers["Connection"] = "close"

        body_bytes = body.encode("utf-8")
        headers["Content-Length"] = str(len(body_bytes))

        # Xây dựng chuỗi HTTP Request
        request_line = f"{method.upper()} {path} HTTP/1.1\r\n"
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        raw_request = (request_line + header_lines + "\r\n").encode("iso-8859-1") + body_bytes

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            # 1. Kết nối TCP tới Server
            sock.connect((self.host, self.port))

            # 2. Gửi thông điệp HTTP
            sock.sendall(raw_request)

            # 3. Đọc toàn bộ phản hồi từ Server cho đến khi Server đóng kết nối
            response_data = bytearray()
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data.extend(chunk)
                except socket.timeout:
                    break

            if not response_data:
                return 0, "No Response", {}, "Server đã đóng kết nối mà không trả về dữ liệu"

            # 4. Phân tích phản hồi HTTP
            return self._parse_http_response(bytes(response_data))

        except ConnectionRefusedError:
            err_msg = f"Không thể kết nối tới Server tại {self.host}:{self.port}. Vui lòng kiểm tra Server đã được khởi động chưa."
            return 0, "Connection Refused", {"status": 0, "message": err_msg}, err_msg
        except socket.timeout:
            err_msg = f"Quá thời gian kết nối hoặc nhận phản hồi từ Server (Timeout {self.timeout}s)."
            return 0, "Timeout", {"status": 0, "message": err_msg}, err_msg
        except Exception as e:
            err_msg = f"Lỗi kết nối mạng: {e}"
            return 0, "Network Error", {"status": 0, "message": err_msg}, err_msg
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _parse_http_response(self, raw_bytes: bytes) -> Tuple[int, str, Dict[str, Any], str]:
        """
        Phân tích chuỗi bytes nhận được từ Server thành mã trạng thái và nội dung JSON (UC05).
        """
        delimiter = b"\r\n\r\n"
        idx = raw_bytes.find(delimiter)
        delimiter_len = 4
        if idx == -1:
            delimiter = b"\n\n"
            idx = raw_bytes.find(delimiter)
            delimiter_len = 2

        if idx == -1:
            # Không tìm thấy header delimiter
            return 0, "Malformed Response", {}, raw_bytes.decode("utf-8", errors="replace")

        header_part = raw_bytes[:idx].decode("iso-8859-1", errors="replace")
        body_part = raw_bytes[idx + delimiter_len:].decode("utf-8", errors="replace")

        lines = header_part.splitlines()
        status_code = 0
        status_text = "Unknown"

        if lines:
            status_line = lines[0].strip()
            parts = status_line.split(maxsplit=2)
            if len(parts) >= 2 and parts[1].isdigit():
                status_code = int(parts[1])
                status_text = parts[2] if len(parts) > 2 else ""

        # Phân tích nội dung JSON nếu có
        json_dict = {}
        try:
            parsed = json.loads(body_part)
            if isinstance(parsed, dict):
                json_dict = parsed
        except Exception:
            pass

        return status_code, status_text, json_dict, body_part
