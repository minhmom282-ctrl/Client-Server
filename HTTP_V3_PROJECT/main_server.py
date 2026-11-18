"""
Điểm khởi chạy chương trình HTTP SERVER (Server Entry Point)
Mặc định mở giao diện đồ họa GUI hiện đại.
Hỗ trợ cờ --cli để chạy ở chế độ dòng lệnh thuần (CLI) theo đúng tài liệu.
"""
import sys
import os

# Thêm thư mục hiện tại vào sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.server_gui import run_server_gui
from server.http_server import HTTPServer


def run_server_cli():
    """Chế độ dòng lệnh CLI theo đặc tả Use Case UC06, UC07 trong tài liệu"""
    print("=" * 60)
    print("      HTTP SERVER - CHẾ ĐỘ DÒNG LỆNH (CLI MODE)")
    print("      Lệnh hỗ trợ: start, stop, exit/quit")
    print("=" * 60)
    
    server = HTTPServer()
    
    while True:
        try:
            cmd = input("server> ").strip()
            if not cmd:
                continue
            
            if cmd == "start":
                success, msg = server.start()
                print(f"[*] {msg}")
            elif cmd == "stop":
                success, msg = server.stop()
                print(f"[*] {msg}")
            elif cmd in ("exit", "quit"):
                if server.is_running:
                    server.stop()
                print("[*] Đã đóng chương trình Server. Tạm biệt!")
                break
            else:
                print(f"[!] Lệnh không hợp lệ: '{cmd}'. Chỉ hỗ trợ: start, stop, exit")
        except (KeyboardInterrupt, EOFError):
            if server.is_running:
                server.stop()
            print("\n[*] Đã thoát Server.")
            break


def main():
    if "--cli" in sys.argv:
        run_server_cli()
    else:
        run_server_gui()


if __name__ == "__main__":
    main()
