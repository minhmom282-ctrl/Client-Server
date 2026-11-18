"""
Xử lý thông điệp giao thức HTTP (HTTPRequest và HTTPResponse)
Tự phân tích cú pháp HTTP Request và sinh HTTP Response chuẩn trên TCP Socket thô.
Tuân thủ đặc tả Use Case UC08, UC12 và Sơ đồ lớp (Class Diagram).
"""
import json
import socket
from typing import Dict, Any, Optional, Tuple
from common.config import HTTP_STATUS, CONTENT_TYPE_FORM, CONTENT_TYPE_JSON, MAX_PAYLOAD_SIZE, NETWORK_TIMEOUT
from common.utils import parse_form_urlencoded, parse_json_body


class HTTPRequest:
    """
    Đại diện cho một thông điệp yêu cầu HTTP từ Client.
    Phân tích raw stream từ TCP socket thành đối tượng có cấu trúc.
    """
    def __init__(self):
        self.method: str = ""
        self.path: str = ""
        self.http_version: str = "HTTP/1.1"
        self.headers: Dict[str, str] = {}
        self.raw_body: bytes = b""
        self.body: str = ""
        self.params: Dict[str, str] = {}
        self.content_type: str = ""
        self.content_length: int = 0
        self.error_code: Optional[int] = None
        self.error_message: str = ""

    def get_header(self, name: str, default: str = "") -> str:
        """Lấy giá trị header không phân biệt hoa thường"""
        target = name.lower()
        for k, v in self.headers.items():
            if k.lower() == target:
                return v
        return default

    @classmethod
    def parse_from_socket(cls, client_sock: socket.socket) -> 'HTTPRequest':
        """
        Đọc và phân tích thông điệp HTTP từ Socket TCP.
        Hỗ trợ đọc header ngăn cách bằng '\\r\\n\\r\\n', sau đó đọc đúng Content-Length bytes body.
        Xử lý timeout 10 giây theo đặc tả Use Case UC08 - E1.
        """
        req = cls()
        buffer = bytearray()
        client_sock.settimeout(NETWORK_TIMEOUT)

        # 1. Đọc phần Header (kết thúc bằng \r\n\r\n hoặc \n\n)
        header_end = -1
        delimiter_len = 4
        while True:
            try:
                chunk = client_sock.recv(4096)
                if not chunk:
                    # Client đóng kết nối sớm
                    break
                buffer.extend(chunk)

                # Kiểm tra delimiter kết thúc header
                idx = buffer.find(b"\r\n\r\n")
                if idx != -1:
                    header_end = idx
                    delimiter_len = 4
                    break
                idx = buffer.find(b"\n\n")
                if idx != -1:
                    header_end = idx
                    delimiter_len = 2
                    break

                if len(buffer) > 65536: # Header quá lớn > 64KB
                    req.error_code = 400
                    req.error_message = "HTTP Header quá lớn vượt quá giới hạn an toàn"
                    return req
            except socket.timeout:
                req.error_code = 400
                req.error_message = "Quá thời gian chờ gửi dữ liệu từ Client (Timeout 10s)"
                return req
            except Exception as e:
                req.error_code = 400
                req.error_message = f"Lỗi đọc socket kết nối: {e}"
                return req

        if header_end == -1:
            req.error_code = 400
            req.error_message = "Yêu cầu HTTP không hợp lệ (không tìm thấy Header hoàn chỉnh)"
            return req

        # 2. Phân tích Request Line và Headers
        header_bytes = buffer[:header_end]
        body_initial = buffer[header_end + delimiter_len:]

        try:
            header_text = header_bytes.decode("iso-8859-1")
            lines = header_text.splitlines()
            if not lines:
                req.error_code = 400
                req.error_message = "Yêu cầu HTTP rỗng"
                return req

            # Dòng yêu cầu (Request Line): METHOD PATH VERSION
            req_line = lines[0].strip()
            parts = req_line.split()
            if len(parts) >= 3:
                req.method = parts[0].upper()
                req.path = parts[1]
                req.http_version = parts[2]
            elif len(parts) == 2:
                req.method = parts[0].upper()
                req.path = parts[1]
            else:
                req.error_code = 400
                req.error_message = f"Cú pháp Request Line không hợp lệ: {req_line}"
                return req

            # Các trường Header
            for line in lines[1:]:
                if ":" in line:
                    key, val = line.split(":", 1)
                    req.headers[key.strip()] = val.strip()

        except Exception as e:
            req.error_code = 400
            req.error_message = f"Lỗi phân tích cú pháp Header: {e}"
            return req

        # 3. Phân tích Content-Length và đọc Body đầy đủ
        content_length_str = req.get_header("Content-Length", "0")
        try:
            req.content_length = int(content_length_str)
        except ValueError:
            req.error_code = 400
            req.error_message = "Giá trị Content-Length không hợp lệ"
            return req

        # Kiểm tra giới hạn kích thước payload (UC08 / 413)
        if req.content_length > MAX_PAYLOAD_SIZE:
            req.error_code = 413
            req.error_message = f"Kích thước payload vượt quá giới hạn cho phép ({MAX_PAYLOAD_SIZE} bytes)"
            return req

        body_buffer = bytearray(body_initial)
        bytes_to_read = req.content_length - len(body_buffer)

        while bytes_to_read > 0:
            try:
                chunk = client_sock.recv(min(bytes_to_read, 4096))
                if not chunk:
                    break
                body_buffer.extend(chunk)
                bytes_to_read -= len(chunk)
            except socket.timeout:
                req.error_code = 400
                req.error_message = "Quá thời gian chờ nhận toàn bộ body từ Client"
                return req
            except Exception as e:
                req.error_code = 400
                req.error_message = f"Lỗi khi đọc body từ socket: {e}"
                return req

        req.raw_body = bytes(body_buffer)
        try:
            req.body = req.raw_body.decode("utf-8")
        except UnicodeDecodeError:
            req.body = req.raw_body.decode("iso-8859-1")

        # 4. Phân tích Body theo Content-Type
        req.content_type = req.get_header("Content-Type", "")
        if req.method == "POST" and req.content_length > 0:
            ct_lower = req.content_type.lower()
            if "application/json" in ct_lower:
                success, parsed_json, err = parse_json_body(req.body)
                if not success:
                    req.error_code = 400
                    req.error_message = f"Không thể phân tích JSON body: {err}"
                    return req
                req.params = parsed_json or {}
            elif "application/x-www-form-urlencoded" in ct_lower:
                req.params = parse_form_urlencoded(req.body)
            else:
                # Thử tự động nhận diện nếu Content-Type không rõ ràng
                if req.body.strip().startswith("{"):
                    success, parsed_json, _ = parse_json_body(req.body)
                    if success:
                        req.params = parsed_json or {}
                    else:
                        req.params = parse_form_urlencoded(req.body)
                else:
                    req.params = parse_form_urlencoded(req.body)

        return req


class HTTPResponse:
    """
    Đại diện cho thông điệp phản hồi HTTP từ Server về Client.
    Đóng gói Header và JSON Body chuẩn.
    """
    def __init__(self, status_code: int = 200, status_text: str = "", message: str = "", data: Any = None):
        self.status_code = status_code
        self.status_text = status_text or HTTP_STATUS.get(status_code, "Unknown")
        self.headers: Dict[str, str] = {
            "Server": "Python-HTTPv3-CustomServer/1.0",
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "close"
        }
        self.data = data
        self.message = message

        # Xây dựng JSON body thống nhất
        body_dict = {
            "status": self.status_code,
            "message": self.message
        }
        if data is not None:
            body_dict["data"] = data

        self.body = json.dumps(body_dict, ensure_ascii=False)

    @classmethod
    def created(cls, message: str, username: str = "") -> 'HTTPResponse':
        """201 Created: Đăng ký thành công"""
        data = {"username": username} if username else None
        return cls(status_code=201, status_text="Created", message=message, data=data)

    @classmethod
    def conflict(cls, message: str) -> 'HTTPResponse':
        """409 Conflict: Tên đăng nhập đã tồn tại"""
        return cls(status_code=409, status_text="Conflict", message=message)

    @classmethod
    def bad_request(cls, message: str) -> 'HTTPResponse':
        """400 Bad Request: Yêu cầu không hợp lệ"""
        return cls(status_code=400, status_text="Bad Request", message=message)

    @classmethod
    def not_found(cls, message: str = "Đường dẫn không tồn tại") -> 'HTTPResponse':
        """404 Not Found: Sai đường dẫn"""
        return cls(status_code=404, status_text="Not Found", message=message)

    @classmethod
    def method_not_allowed(cls, message: str = "Phương thức không được hỗ trợ, yêu cầu POST") -> 'HTTPResponse':
        """405 Method Not Allowed: Sai phương thức"""
        return cls(status_code=405, status_text="Method Not Allowed", message=message)

    @classmethod
    def payload_too_large(cls, message: str = "Kích thước yêu cầu vượt quá giới hạn cho phép") -> 'HTTPResponse':
        """413 Payload Too Large: Dữ liệu quá lớn"""
        return cls(status_code=413, status_text="Payload Too Large", message=message)

    @classmethod
    def server_error(cls, message: str = "Lỗi xử lý nội bộ phía máy chủ") -> 'HTTPResponse':
        """500 Internal Server Error: Lỗi server nội bộ"""
        return cls(status_code=500, status_text="Internal Server Error", message=message)

    def to_bytes(self) -> bytes:
        """
        Chuyển đổi đối tượng HTTPResponse thành chuỗi bytes chuẩn HTTP/1.1
        gồm Status Line, Headers, Content-Length và Body.
        """
        body_bytes = self.body.encode("utf-8")
        self.headers["Content-Length"] = str(len(body_bytes))

        # Xây dựng Response Header
        status_line = f"HTTP/1.1 {self.status_code} {self.status_text}\r\n"
        headers_lines = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        header_block = f"{status_line}{headers_lines}\r\n"

        return header_block.encode("iso-8859-1") + body_bytes
