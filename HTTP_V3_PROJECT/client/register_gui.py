"""
Giao diện đồ họa Client Đăng ký tài khoản (Client GUI)
Thiết kế hiện đại, sang trọng bằng CustomTkinter.
Hỗ trợ chuyển đổi định dạng Form/JSON, hiện/ẩn mật khẩu, validation thời gian thực,
chạy bất đồng bộ qua luồng riêng (Threading) không bao giờ làm treo giao diện.
"""
import sys
import os
import threading
from typing import Optional

# Thêm đường dẫn gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from common.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT
from common.utils import is_valid_username, is_valid_password, is_valid_email
from client.http_client import HTTPClient

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RegisterClientGUI(ctk.CTk):
    """
    Cửa sổ ứng dụng Đăng ký tài khoản Client
    """
    def __init__(self, host: str = DEFAULT_CLIENT_HOST, port: int = DEFAULT_PORT):
        super().__init__()
        self.host = host
        self.port = port
        self.is_password_visible = False
        self.is_confirm_visible = False
        self.is_processing = False

        self.title("Client - Đăng Ký Tài Khoản (HTTP v3)")
        self.geometry("560 x 780")
        self.minsize(520, 720)
        self.resizable(True, True)

        self._init_ui()

    def _init_ui(self) -> None:
        """Khởi tạo toàn bộ thành phần giao diện"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Khung chính cuộn được hoặc căn giữa
        main_frame = ctk.CTkFrame(self, corner_radius=16, fg_color=("#F8FAFC", "#1E293B"))
        main_frame.grid(row=0, column=0, padx=25, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        # ==================== 1. HEADER (LOGO & TIÊU ĐỀ) ====================
        header_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_box.pack(fill="x", padx=25, pady=(20, 10))

        icon_lbl = ctk.CTkLabel(
            header_box,
            text="✨ 👤 ✨",
            font=ctk.CTkFont(size=30)
        )
        icon_lbl.pack(pady=(0, 5))

        title_lbl = ctk.CTkLabel(
            header_box,
            text="CREATE YOUR ACCOUNT",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        title_lbl.pack()

        subtitle_lbl = ctk.CTkLabel(
            header_box,
            text="Đăng ký tài khoản an toàn qua giao thức HTTP/1.1 trên TCP",
            font=ctk.CTkFont(size=12),
            text_color=("#64748B", "#94A3B8")
        )
        subtitle_lbl.pack(pady=(2, 0))

        # ==================== 2. CẤU HÌNH KẾT NỐI & ĐỊNH DẠNG ====================
        config_box = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("#E2E8F0", "#0F172A"))
        config_box.pack(fill="x", padx=25, pady=(5, 12))
        config_box.grid_columnconfigure(1, weight=1)

        # Server IP & Port
        server_info_frame = ctk.CTkFrame(config_box, fg_color="transparent")
        server_info_frame.pack(fill="x", padx=12, pady=(8, 4))
        
        lbl_server = ctk.CTkLabel(
            server_info_frame, 
            text="Máy chủ Server:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#475569", "#CBD5E1")
        )
        lbl_server.pack(side="left")

        self.entry_host = ctk.CTkEntry(server_info_frame, width=120, height=28, font=ctk.CTkFont(size=12))
        self.entry_host.insert(0, self.host)
        self.entry_host.pack(side="left", padx=6)

        lbl_colon = ctk.CTkLabel(server_info_frame, text=":", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_colon.pack(side="left")

        self.entry_port = ctk.CTkEntry(server_info_frame, width=65, height=28, font=ctk.CTkFont(size=12))
        self.entry_port.insert(0, str(self.port))
        self.entry_port.pack(side="left", padx=6)

        # Chuyển đổi định dạng gửi (Form URL-encoded vs JSON)
        fmt_frame = ctk.CTkFrame(config_box, fg_color="transparent")
        fmt_frame.pack(fill="x", padx=12, pady=(4, 8))

        lbl_fmt = ctk.CTkLabel(
            fmt_frame, 
            text="Định dạng truyền:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#475569", "#CBD5E1")
        )
        lbl_fmt.pack(side="left")

        self.seg_format = ctk.CTkSegmentedButton(
            fmt_frame,
            values=["Form URL-encoded (Mặc định)", "JSON (application/json)"],
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28
        )
        self.seg_format.set("Form URL-encoded (Mặc định)")
        self.seg_format.pack(side="left", padx=10, fill="x", expand=True)

        # ==================== 3. CÁC TRƯỜNG NHẬP LIỆU ====================
        form_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_box.pack(fill="x", padx=25, pady=0)

        # Trường Username
        lbl_u = ctk.CTkLabel(form_box, text="Tên đăng nhập (Username)", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_u.pack(anchor="w", pady=(6, 2))
        self.entry_username = ctk.CTkEntry(
            form_box,
            placeholder_text="Nhập username (không chứa dấu cách, 3-30 ký tự)",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.entry_username.pack(fill="x")

        # Trường Password
        lbl_p = ctk.CTkLabel(form_box, text="Mật khẩu (Password)", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_p.pack(anchor="w", pady=(8, 2))
        
        pass_row = ctk.CTkFrame(form_box, fg_color="transparent")
        pass_row.pack(fill="x")
        self.entry_password = ctk.CTkEntry(
            pass_row,
            placeholder_text="Nhập mật khẩu (tối thiểu 6 ký tự)",
            show="●",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.entry_password.pack(side="left", fill="x", expand=True)

        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="👁",
            width=42,
            height=38,
            font=ctk.CTkFont(size=14),
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            command=self.toggle_password_visibility
        )
        self.btn_toggle_pass.pack(side="left", padx=(6, 0))

        # Trường Confirm Password
        lbl_cp = ctk.CTkLabel(form_box, text="Xác nhận mật khẩu (Confirm Password)", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_cp.pack(anchor="w", pady=(8, 2))

        cpass_row = ctk.CTkFrame(form_box, fg_color="transparent")
        cpass_row.pack(fill="x")
        self.entry_confirm = ctk.CTkEntry(
            cpass_row,
            placeholder_text="Nhập lại mật khẩu để xác nhận",
            show="●",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.entry_confirm.pack(side="left", fill="x", expand=True)

        self.btn_toggle_confirm = ctk.CTkButton(
            cpass_row,
            text="👁",
            width=42,
            height=38,
            font=ctk.CTkFont(size=14),
            fg_color=("#CBD5E1", "#334155"),
            hover_color=("#94A3B8", "#475569"),
            command=self.toggle_confirm_visibility
        )
        self.btn_toggle_confirm.pack(side="left", padx=(6, 0))

        # Trường Email
        lbl_e = ctk.CTkLabel(form_box, text="Địa chỉ Email", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_e.pack(anchor="w", pady=(8, 2))
        self.entry_email = ctk.CTkEntry(
            form_box,
            placeholder_text="ví dụ: user@nuce.edu.vn",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.entry_email.pack(fill="x")

        # ==================== 4. BANNER THÔNG BÁO KẾT QUẢ ====================
        self.banner_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="transparent")
        self.banner_frame.pack(fill="x", padx=25, pady=(12, 5))

        self.lbl_feedback = ctk.CTkLabel(
            self.banner_frame,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=480,
            justify="center"
        )
        self.lbl_feedback.pack(padx=10, pady=8)

        # ==================== 5. CÁC NÚT THAO TÁC ====================
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(10, 15))

        # Nút Register
        self.btn_register = ctk.CTkButton(
            btn_box,
            text="🚀  ĐĂNG KÝ (REGISTER)",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2563EB",  # Xanh dương hiện đại
            hover_color="#1D4ED8",
            height=44,
            command=self.on_register_click
        )
        self.btn_register.pack(fill="x", pady=(0, 8))

        # Hàng nút phụ: Clear và Exit
        sub_btn_row = ctk.CTkFrame(btn_box, fg_color="transparent")
        sub_btn_row.pack(fill="x")
        sub_btn_row.grid_columnconfigure((0, 1), weight=1)

        self.btn_clear = ctk.CTkButton(
            sub_btn_row,
            text="🧹  Xóa dữ liệu (Clear)",
            font=ctk.CTkFont(size=13),
            fg_color=("#64748B", "#475569"),
            hover_color=("#475569", "#334155"),
            height=36,
            command=self.clear_form
        )
        self.btn_clear.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_exit = ctk.CTkButton(
            sub_btn_row,
            text="🚪  Thoát (Exit)",
            font=ctk.CTkFont(size=13),
            fg_color=("#94A3B8", "#334155"),
            hover_color=("#64748B", "#1E293B"),
            height=36,
            command=self.destroy
        )
        self.btn_exit.grid(row=0, column=1, padx=(4, 0), sticky="ew")

    # ==================== XỬ LÝ ẨN/HIỆN MẬT KHẨU ====================

    def toggle_password_visibility(self) -> None:
        """Chuyển đổi ẩn/hiện mật khẩu"""
        self.is_password_visible = not self.is_password_visible
        if self.is_password_visible:
            self.entry_password.configure(show="")
            self.btn_toggle_pass.configure(text="🔒")
        else:
            self.entry_password.configure(show="●")
            self.btn_toggle_pass.configure(text="👁")

    def toggle_confirm_visibility(self) -> None:
        """Chuyển đổi ẩn/hiện mật khẩu xác nhận"""
        self.is_confirm_visible = not self.is_confirm_visible
        if self.is_confirm_visible:
            self.entry_confirm.configure(show="")
            self.btn_toggle_confirm.configure(text="🔒")
        else:
            self.entry_confirm.configure(show="●")
            self.btn_toggle_confirm.configure(text="👁")

    # ==================== XÓA DỮ LIỆU FORM ====================

    def clear_form(self) -> None:
        """Xóa toàn bộ nội dung trong các ô nhập"""
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.entry_confirm.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.hide_feedback()

    # ==================== HIỂN THỊ THÔNG BÁO ====================

    def show_feedback(self, message: str, status_code: int = 0) -> None:
        """Hiển thị banner phản hồi tương ứng theo mã HTTP"""
        # Màu sắc banner
        if status_code == 201:
            bg_color = "#10B981"  # Xanh lục (Thành công)
            text_color = "#FFFFFF"
            prefix = "✅ [HTTP 201 Created] "
        elif status_code == 409:
            bg_color = "#F59E0B"  # Vàng cam (Trùng dữ liệu)
            text_color = "#FFFFFF"
            prefix = "⚠️ [HTTP 409 Conflict] "
        elif status_code in (400, 404, 405, 413):
            bg_color = "#EF4444"  # Đỏ tươi (Lỗi client/request)
            text_color = "#FFFFFF"
            prefix = f"❌ [HTTP {status_code}] "
        elif status_code == 500:
            bg_color = "#DC2626"  # Đỏ sẫm (Lỗi server)
            text_color = "#FFFFFF"
            prefix = "🔥 [HTTP 500 Server Error] "
        else:
            # Lỗi kết nối / mất mạng
            bg_color = "#B91C1C"
            text_color = "#FFFFFF"
            prefix = "🔌 [Lỗi Kết Nối] "

        self.banner_frame.configure(fg_color=bg_color)
        self.lbl_feedback.configure(text=prefix + message, text_color=text_color)

    def hide_feedback(self) -> None:
        """Ẩn thông báo"""
        self.banner_frame.configure(fg_color="transparent")
        self.lbl_feedback.configure(text="")

    # ==================== XỬ LÝ ĐĂNG KÝ QUA MẠNG ====================

    def on_register_click(self) -> None:
        """Xử lý khi bấm nút Đăng ký"""
        if self.is_processing:
            return

        username = self.entry_username.get().strip()
        password = self.entry_password.get()
        confirm_password = self.entry_confirm.get()
        email = self.entry_email.get().strip()

        # 1. Kiểm tra tính hợp lệ dữ liệu tại Client
        if not username or not password or not confirm_password or not email:
            self.show_feedback("Vui lòng nhập đầy đủ tất cả các trường thông tin!", 400)
            return

        if password != confirm_password:
            self.show_feedback("Mật khẩu và xác nhận mật khẩu không trùng khớp!", 400)
            return

        ok_u, msg_u = is_valid_username(username)
        if not ok_u:
            self.show_feedback(msg_u, 400)
            return

        ok_p, msg_p = is_valid_password(password)
        if not ok_p:
            self.show_feedback(msg_p, 400)
            return

        ok_e, msg_e = is_valid_email(email)
        if not ok_e:
            self.show_feedback(msg_e, 400)
            return

        # 2. Lấy cấu hình máy chủ
        host = self.entry_host.get().strip() or DEFAULT_CLIENT_HOST
        try:
            port = int(self.entry_port.get().strip())
        except ValueError:
            self.show_feedback("Cổng kết nối Port phải là số nguyên (ví dụ: 8888)!", 400)
            return

        # Kiểm tra chế độ định dạng dữ liệu (Form hay JSON)
        is_json = "JSON" in self.seg_format.get()

        # 3. Chuyển sang trạng thái đang xử lý (loading)
        self.is_processing = True
        self.btn_register.configure(state="disabled", text="⏳  Đang kết nối Server và gửi yêu cầu...")
        self.hide_feedback()

        # 4. Gửi yêu cầu qua luồng riêng (Threading)
        threading.Thread(
            target=self._send_request_thread,
            args=(host, port, username, password, email, is_json),
            daemon=True
        ).start()

    def _send_request_thread(self, host: str, port: int, username: str, password: str, email: str, is_json: bool) -> None:
        """Hàm chạy trong luồng nền để gửi yêu cầu socket không làm treo giao diện"""
        client = HTTPClient(host=host, port=port, is_json_mode=is_json)
        code, text, json_dict, raw_body = client.send_register_request(username, password, email, use_json=is_json)

        # Lấy thông điệp phản hồi
        msg = json_dict.get("message", "")
        if not msg:
            msg = raw_body or text

        # Cập nhật kết quả an toàn lên giao diện
        self.after(0, lambda: self._on_request_completed(code, msg))

    def _on_request_completed(self, status_code: int, message: str) -> None:
        """Xử lý sau khi nhận được phản hồi từ Server"""
        self.is_processing = False
        self.btn_register.configure(state="normal", text="🚀  ĐĂNG KÝ (REGISTER)")
        self.show_feedback(message, status_code)

        # Nếu đăng ký thành công, tự động xóa mật khẩu để bảo mật
        if status_code == 201:
            self.entry_password.delete(0, "end")
            self.entry_confirm.delete(0, "end")


def run_client_gui():
    """Hàm khởi động giao diện Client"""
    app = RegisterClientGUI()
    app.mainloop()


if __name__ == "__main__":
    run_client_gui()
