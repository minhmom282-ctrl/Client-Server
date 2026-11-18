"""
Các tiện ích dùng chung (Utilities)
Mã hóa SHA-256, kiểm tra tính hợp lệ dữ liệu, phân giải dữ liệu Form/JSON
"""
import hashlib
import re
import urllib.parse
import json
from datetime import datetime
from typing import Tuple, Optional, Dict, Any


def hash_password(password: str) -> str:
    """
    Tính mã băm SHA-256 của mật khẩu (theo yêu cầu bảo mật của đồ án).
    Trả về chuỗi hex 64 ký tự.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_username(username: str) -> Tuple[bool, str]:
    """
    Kiểm tra tên đăng nhập:
    - Không được rỗng
    - Không chứa khoảng trắng (theo UC02 quy tắc nghiệp vụ)
    - Độ dài từ 3 đến 30 ký tự
    - Chỉ gồm chữ cái, chữ số và dấu gạch dưới
    """
    if not username:
        return False, "Tên đăng nhập không được để trống"
    if any(c.isspace() for c in username):
        return False, "Tên đăng nhập không được chứa khoảng trắng"
    if len(username) < 3 or len(username) > 30:
        return False, "Tên đăng nhập phải có độ dài từ 3 đến 30 ký tự"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới"
    return True, ""


def is_valid_password(password: str) -> Tuple[bool, str]:
    """
    Kiểm tra mật khẩu:
    - Không được rỗng
    - Không chứa khoảng trắng (theo UC02 quy tắc nghiệp vụ)
    - Độ dài tối thiểu 6 ký tự
    """
    if not password:
        return False, "Mật khẩu không được để trống"
    if any(c.isspace() for c in password):
        return False, "Mật khẩu không được chứa khoảng trắng"
    if len(password) < 6:
        return False, "Mật khẩu phải có độ dài tối thiểu 6 ký tự"
    return True, ""


def is_valid_email(email: str) -> Tuple[bool, str]:
    """
    Kiểm tra định dạng email tiêu chuẩn
    """
    if not email:
        return False, "Email không được để trống"
    if any(c.isspace() for c in email):
        return False, "Email không được chứa khoảng trắng"
    # Regex kiểm tra email chuẩn
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Địa chỉ email không đúng định dạng (ví dụ: user@example.com)"
    return True, ""


def validate_registration_data(username: str, password: str, email: str) -> Tuple[bool, str]:
    """
    Kiểm tra toàn bộ thông tin đăng ký
    """
    ok, msg = is_valid_username(username)
    if not ok:
        return False, msg

    ok, msg = is_valid_password(password)
    if not ok:
        return False, msg

    ok, msg = is_valid_email(email)
    if not ok:
        return False, msg

    return True, "Dữ liệu hợp lệ"


def parse_form_urlencoded(body_str: str) -> Dict[str, str]:
    """
    Phân tích chuỗi form URL-encoded (application/x-www-form-urlencoded)
    thành dictionary các tham số (bỏ khoảng trắng đầu cuối).
    """
    parsed = urllib.parse.parse_qs(body_str, keep_blank_values=True)
    res = {}
    for k, v in parsed.items():
        if v:
            res[k.strip()] = v[0].strip()
        else:
            res[k.strip()] = ""
    return res


def encode_form_urlencoded(data: Dict[str, str]) -> str:
    """
    Đóng gói dictionary thành chuỗi form URL-encoded
    """
    return urllib.parse.urlencode(data)


def parse_json_body(body_str: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Phân tích chuỗi JSON body
    """
    try:
        data = json.loads(body_str)
        if not isinstance(data, dict):
            return False, None, "JSON body phải là một đối tượng (object)"
        # Strip khoảng trắng cho các trường chuỗi
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                cleaned[k.strip()] = v.strip()
            else:
                cleaned[k.strip()] = str(v)
        return True, cleaned, ""
    except json.JSONDecodeError as e:
        return False, None, f"Lỗi cú pháp JSON: {e}"


def get_current_timestamp() -> str:
    """Trả về thời gian hiện tại định dạng YYYY-MM-DD HH:MM:SS"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
