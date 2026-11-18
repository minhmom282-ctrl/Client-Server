"""
Quản lý người dùng và lưu trữ dữ liệu tệp users.txt
Tuân thủ đặc tả Use Case UC09, UC10, UC11 và Sơ đồ lớp (Class Diagram)
"""
import os
import threading
from typing import Optional, List, Tuple
from common.utils import hash_password
from common.config import USERS_FILE


class User:
    """Mô hình dữ liệu Người dùng"""
    def __init__(self, username: str, password_hash: str, email: str, created_at: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = created_at

    def to_file_format(self) -> str:
        """
        Chuyển đổi thành định dạng ghi file:
        username<TAB>SHA-256(password)<TAB>email
        """
        return f"{self.username}\t{self.password_hash}\t{self.email}\n"

    @staticmethod
    def from_file_line(line: str) -> Optional['User']:
        """
        Đọc và phân tích một dòng từ users.txt
        """
        line = line.strip("\r\n")
        if not line:
            return None
        parts = line.split("\t")
        if len(parts) >= 3:
            return User(
                username=parts[0].strip(),
                password_hash=parts[1].strip(),
                email=parts[2].strip()
            )
        return None


class UserRepository:
    """
    Kho lưu trữ tài khoản người dùng tương tác trực tiếp với users.txt
    Sử dụng cơ chế khóa threading.Lock để đảm bảo an toàn đa luồng (Thread-safe)
    ngăn ngừa tình trạng race condition khi nhiều Client cùng đăng ký một lúc.
    """
    def __init__(self, filepath: str = USERS_FILE):
        self.filepath = filepath
        self.lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Tạo file và thư mục nếu chưa tồn tại (theo UC09 - Luồng thay thế 1a)"""
        with self.lock:
            dirname = os.path.dirname(self.filepath)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            if not os.path.exists(self.filepath):
                with open(self.filepath, "w", encoding="utf-8") as f:
                    pass

    def find_by_username(self, username: str) -> Optional[User]:
        """
        Tra cứu username trong danh sách users.txt (UC09)
        So sánh chính xác, phân biệt chữ hoa và chữ thường.
        """
        self._ensure_file_exists()
        with self.lock:
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        user = User.from_file_line(line)
                        if user and user.username == username:
                            return user
            except Exception as e:
                print(f"[UserRepository] Lỗi khi đọc file {self.filepath}: {e}")
        return None

    def save(self, username: str, password_raw: str, email: str) -> Tuple[str, str]:
        """
        Thêm người dùng mới vào danh sách (UC10)
        - Kiểm tra trùng lặp trong lock (UC09)
        - Tính SHA-256 của password
        - Ghi thêm vào cuối users.txt
        Trả về (status, message):
            status: "CREATED" | "CONFLICT" | "ERROR"
        """
        self._ensure_file_exists()
        with self.lock:
            # Kiểm tra trong lock để đảm bảo nguyên tử (Atomic Check-and-Set)
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        user = User.from_file_line(line)
                        if user and user.username == username:
                            return "CONFLICT", f"User đã tồn tại: {username}"
            except Exception as e:
                return "ERROR", f"Lỗi đọc file: {e}"

            # Tính SHA-256
            pw_hash = hash_password(password_raw)
            new_user = User(username=username, password_hash=pw_hash, email=email)

            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(new_user.to_file_format())
                return "CREATED", f"Đăng ký thành công user {username}"
            except Exception as e:
                return "ERROR", f"Lỗi ghi file: {e}"

    def get_all_users_for_display(self) -> List[Tuple[str, str]]:
        """
        Lấy danh sách các tài khoản để hiển thị trên giao diện quản trị Server.
        CHỈ trả về (username, email) - TUYỆT ĐỐI KHÔNG hiển thị mật khẩu hay hash mật khẩu
        theo đúng yêu cầu bảo mật của đồ án.
        """
        self._ensure_file_exists()
        users_list = []
        with self.lock:
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        u = User.from_file_line(line)
                        if u:
                            users_list.append((u.username, u.email))
            except Exception as e:
                print(f"[UserRepository] Lỗi khi tải danh sách người dùng: {e}")
        return users_list

    def count_users(self) -> int:
        """Đếm tổng số tài khoản hiện có"""
        return len(self.get_all_users_for_display())
