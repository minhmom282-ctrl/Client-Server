"""
Giao diện đồ họa Server (Server GUI)
Thiết kế hiện đại, chuyên nghiệp sử dụng CustomTkinter.
Hiển thị trạng thái, bảng thống kê thời gian thực, nhật ký sự kiện và quản lý tài khoản.
"""
import sys
import os
import socket
import threading
from typing import Optional

# Thêm đường dẫn gốc vào sys.path để import các module trong dự án
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from common.config import DEFAULT_PORT, DEFAULT_HOST
from server.http_server import HTTPServer
from server.user_manager import UserRepository

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")  # Giao diện Dark Mode hiện đại
ctk.set_default_color_theme("blue")


class ServerGUI(ctk.CTk):
    """
    Cửa sổ điều khiển quản trị máy chủ HTTP Server
    """
    def __init__(self, port: int = DEFAULT_PORT):
        super().__init__()
        self.port = port
        self.user_repo = UserRepository()
        self.server = HTTPServer(host=DEFAULT_HOST, port=self.port, user_repo=self.user_repo)

        # Cài đặt cửa sổ chính
        self.title("HTTP Server Management - Đồ án Lập trình Hệ thống Mạng")
        self.geometry("980 x 720")
        self.minsize(900, 640)

        # Đăng ký các callback của Server lên giao diện
        self.server.log_callback = self.add_log_safe
        self.server.stats_callback = self.update_stats_safe
        self.server.state_callback = self.update_state_safe
        self.server.user_callback = self.on_user_registered_safe

        # Tự động lấy IP cục bộ của máy
        self.local_ip = self._get_local_ip()

        # Xây dựng các thành phần giao diện
        self._init_ui()

        # Nạp dữ liệu tài khoản ban đầu
        self.refresh_user_list()

        # Bắt sự kiện đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def _get_local_ip(self) -> str:
        """Lấy địa chỉ IP mạng nội bộ của máy tính"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _init_ui(self) -> None:
        """Khởi tạo toàn bộ bố cục giao diện"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ==================== 1. THANH TIÊU ĐỀ & TRẠNG THÁI ====================
        header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#E2E8F0", "#1E293B"))
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        # Logo / Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        title_lbl = ctk.CTkLabel(
            title_box, 
            text="⚡ HTTP SERVER MANAGEMENT", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            title_box, 
            text="Giao thức HTTP/1.1 trên TCP Socket · Nhóm 6", 
            font=ctk.CTkFont(size=12),
            text_color=("#64748B", "#94A3B8")
        )
        subtitle_lbl.pack(anchor="w")

        # Status & Network Badges
        badge_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        badge_box.grid(row=0, column=2, padx=15, pady=12, sticky="e")

        self.net_badge = ctk.CTkLabel(
            badge_box,
            text=f"🌐 IP: {self.local_ip} | Cổng: {self.port}",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#CBD5E1", "#334155"),
            corner_radius=8,
            padx=12,
            pady=6
        )
        self.net_badge.pack(side="left", padx=6)

        self.status_badge = ctk.CTkLabel(
            badge_box,
            text="● ĐANG DỪNG",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#EF4444",  # Đỏ
            corner_radius=8,
            padx=14,
            pady=6
        )
        self.status_badge.pack(side="left", padx=6)

        # ==================== 2. KHU VỰC ĐIỀU KHIỂN (CONTROLS) ====================
        control_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#F1F5F9", "#0F172A"))
        control_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        # Nút Start Server
        self.btn_start = ctk.CTkButton(
            control_frame,
            text="▶  START SERVER",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",  # Xanh lục
            hover_color="#059669",
            height=40,
            command=self.start_server
        )
        self.btn_start.pack(side="left", padx=12, pady=10)

        # Nút Stop Server
        self.btn_stop = ctk.CTkButton(
            control_frame,
            text="⏹  STOP SERVER",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#DC2626",  # Đỏ
            hover_color="#B91C1C",
            height=40,
            state="disabled",
            command=self.stop_server
        )
        self.btn_stop.pack(side="left", padx=6, pady=10)

        # Nút Xóa Log
        self.btn_clear_log = ctk.CTkButton(
            control_frame,
            text="🗑  Xóa Nhật Ký",
            font=ctk.CTkFont(size=13),
            fg_color=("#64748B", "#475569"),
            hover_color=("#475569", "#334155"),
            height=40,
            command=self.clear_log
        )
        self.btn_clear_log.pack(side="left", padx=6, pady=10)

        # Nút Thoát
        self.btn_exit = ctk.CTkButton(
            control_frame,
            text="🚪  Thoát (Exit)",
            font=ctk.CTkFont(size=13),
            fg_color=("#94A3B8", "#334155"),
            hover_color=("#64748B", "#1E293B"),
            height=40,
            command=self.on_exit
        )
        self.btn_exit.pack(side="right", padx=12, pady=10)

        # ==================== 3. KHU VỰC THỐNG KÊ (STATISTICS CARDS) ====================
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew")
        for i in range(5):
            stats_frame.grid_columnconfigure(i, weight=1)

        # 5 Thẻ thống kê
        self.card_total = self._create_stat_card(stats_frame, 0, "Tổng yêu cầu", "0", "#3B82F6")
        self.card_success = self._create_stat_card(stats_frame, 1, "Thành công (201)", "0", "#10B981")
        self.card_conflict = self._create_stat_card(stats_frame, 2, "Trùng tên (409)", "0", "#F59E0B")
        self.card_error = self._create_stat_card(stats_frame, 3, "Yêu cầu lỗi (4xx/5xx)", "0", "#EF4444")
        self.card_active = self._create_stat_card(stats_frame, 4, "Client đang xử lý", "0", "#8B5CF6")

        # ==================== 4. TABVIEW: LOGS & ACCOUNTS ====================
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="nsew")

        # Tab 1: Server Log
        self.tab_log = self.tabview.add("📜  NHẬT KÝ SERVER (LOG)")
        self._init_log_tab()

        # Tab 2: User Accounts Management
        self.tab_users = self.tabview.add("👥  QUẢN LÝ TÀI KHOẢN (USERS.TXT)")
        self._init_users_tab()

    def _create_stat_card(self, parent: ctk.CTkFrame, col: int, title: str, value: str, color: str) -> ctk.CTkLabel:
        """Tạo thẻ thống kê KPI hiển thị đẹp mắt"""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=("#E2E8F0", "#1E293B"))
        card.grid(row=0, column=col, padx=4, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=("#64748B", "#94A3B8"))
        lbl_title.pack(pady=(8, 2))

        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
        lbl_val.pack(pady=(0, 8))
        return lbl_val

    def _init_log_tab(self) -> None:
        """Khởi tạo tab hiển thị log sự kiện theo thời gian thực"""
        self.tab_log.grid_columnconfigure(0, weight=1)
        self.tab_log.grid_rowconfigure(0, weight=1)

        # Hộp văn bản hiển thị Log
        self.log_textbox = ctk.CTkTextbox(
            self.tab_log,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
            corner_radius=8
        )
        self.log_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Cấu hình màu sắc tag theo cấp độ log
        self.log_textbox.tag_config("SUCCESS", foreground="#10B981")
        self.log_textbox.tag_config("ERROR", foreground="#EF4444")
        self.log_textbox.tag_config("WARNING", foreground="#F59E0B")
        self.log_textbox.tag_config("CLIENT", foreground="#8B5CF6")
        self.log_textbox.tag_config("INFO", foreground="#38BDF8")

        # Ghi log chào mừng ban đầu
        self.add_log_safe("=== CHƯƠNG TRÌNH HTTP SERVER ĐÃ SẴN SÀNG ===", "INFO")
        self.add_log_safe(f"Địa chỉ bind: 0.0.0.0 | Cổng mặc định: {self.port} | Nhấn 'START SERVER' để bắt đầu.", "INFO")

    def _init_users_tab(self) -> None:
        """Khởi tạo tab hiển thị danh sách tài khoản đã đăng ký"""
        self.tab_users.grid_columnconfigure(0, weight=1)
        self.tab_users.grid_rowconfigure(1, weight=1)

        # Thanh công cụ bảng
        bar = ctk.CTkFrame(self.tab_users, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 5))

        self.lbl_user_count = ctk.CTkLabel(
            bar,
            text="Tổng số tài khoản: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1E293B", "#F8FAFC")
        )
        self.lbl_user_count.pack(side="left", padx=5)

        btn_refresh = ctk.CTkButton(
            bar,
            text="🔄  Làm mới danh sách",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150,
            command=self.refresh_user_list
        )
        btn_refresh.pack(side="right", padx=5)

        # Bảng hiển thị người dùng bằng Treeview
        tree_frame = ctk.CTkFrame(self.tab_users, corner_radius=8)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("stt", "username", "email")
        self.user_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        self.user_tree.heading("stt", text="STT")
        self.user_tree.heading("username", text="Tên đăng nhập (Username)")
        self.user_tree.heading("email", text="Địa chỉ Email")

        self.user_tree.column("stt", width=60, anchor="center")
        self.user_tree.column("username", width=300, anchor="w")
        self.user_tree.column("email", width=450, anchor="w")

        # Scrollbar cho bảng
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)

        self.user_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Chú thích an toàn thông tin
        notice = ctk.CTkLabel(
            self.tab_users,
            text="🔒 Mật khẩu được băm chuẩn SHA-256 trong file users.txt và không hiển thị trên giao diện theo quy chuẩn an toàn.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        notice.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 5))

    # ==================== ĐIỀU KHIỂN SERVER ====================

    def start_server(self) -> None:
        """Bắt đầu chạy Server"""
        success, msg = self.server.start()
        if not success:
            messagebox.showerror("Lỗi Khởi Động", msg)

    def stop_server(self) -> None:
        """Dừng Server"""
        success, msg = self.server.stop()
        if not success:
            messagebox.showwarning("Cảnh báo", msg)

    def clear_log(self) -> None:
        """Xóa toàn bộ nội dung trong ô log"""
        self.log_textbox.delete("1.0", "end")
        self.add_log_safe("Nhật ký đã được xóa.", "INFO")

    def on_exit(self) -> None:
        """Xử lý an toàn khi tắt ứng dụng"""
        if self.server.is_running:
            self.server.stop()
        self.destroy()

    # ==================== CẬP NHẬT GIAO DIỆN THREAD-SAFE ====================

    def add_log_safe(self, text: str, level: str = "INFO") -> None:
        """Ghi log an toàn giữa các luồng giao diện"""
        def _add():
            try:
                self.log_textbox.insert("end", text + "\n", level)
                self.log_textbox.see("end")
            except Exception:
                pass
        self.after(0, _add)

    def update_state_safe(self, is_running: bool) -> None:
        """Cập nhật trạng thái Server (ĐANG CHẠY / ĐANG DỪNG)"""
        def _update():
            if is_running:
                self.status_badge.configure(text="● ĐANG CHẠY", fg_color="#10B981")
                self.btn_start.configure(state="disabled")
                self.btn_stop.configure(state="normal")
            else:
                self.status_badge.configure(text="● ĐANG DỪNG", fg_color="#EF4444")
                self.btn_start.configure(state="normal")
                self.btn_stop.configure(state="disabled")
        self.after(0, _update)

    def update_stats_safe(self, stats: dict) -> None:
        """Cập nhật các số liệu thống kê lên các thẻ KPI"""
        def _update():
            self.card_total.configure(text=str(stats.get("total_requests", 0)))
            self.card_success.configure(text=str(stats.get("success_count", 0)))
            self.card_conflict.configure(text=str(stats.get("conflict_count", 0)))
            self.card_error.configure(text=str(stats.get("error_count", 0)))
            self.card_active.configure(text=str(stats.get("active_clients", 0)))
        self.after(0, _update)

    def on_user_registered_safe(self, username: str, email: str) -> None:
        """Tự động cập nhật bảng tài khoản khi có người dùng đăng ký thành công"""
        self.after(0, self.refresh_user_list)

    def refresh_user_list(self) -> None:
        """Đọc users.txt và nạp lại dữ liệu lên bảng tài khoản"""
        for row in self.user_tree.get_children():
            self.user_tree.delete(row)

        users = self.user_repo.get_all_users_for_display()
        for idx, (uname, uemail) in enumerate(users, start=1):
            self.user_tree.insert("", "end", values=(idx, uname, uemail))

        self.lbl_user_count.configure(text=f"Tổng số tài khoản: {len(users)}")


def run_server_gui():
    """Hàm khởi động giao diện Server"""
    app = ServerGUI()
    app.mainloop()


if __name__ == "__main__":
    run_server_gui()
