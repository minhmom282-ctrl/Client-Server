"""
Điểm khởi chạy chương trình HTTP CLIENT (Client Entry Point)
Mặc định mở giao diện đồ họa GUI hiện đại.
Hỗ trợ cờ --cli để chạy ở chế độ dòng lệnh thuần (CLI) theo đúng tài liệu.
"""
import sys
import os

# Thêm thư mục hiện tại vào sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.register_gui import run_client_gui
from client.http_client import HTTPClient
from common.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT


def run_client_cli():
    """Chế độ dòng lệnh CLI theo đặc tả Use Case UC01, UC02 trong tài liệu"""
    print("=" * 65)
    print("      HTTP CLIENT - CHẾ ĐỘ DÒNG LỆNH (CLI MODE)")
    print("      Cú pháp: register <username> <password> <email>")
    print("      Lệnh khác: mode json / mode form, quit / exit")
    print("=" * 65)
    
    use_json = "--json" in sys.argv
    client = HTTPClient(is_json_mode=use_json)
    print(f"[*] Chế độ đóng gói hiện tại: {'JSON' if client.is_json_mode else 'Form URL-encoded (mặc định)'}")
    
    while True:
        try:
            line = input("client> ").strip()
            if not line:
                continue
            
            if line in ("quit", "exit"):
                print("[*] Đã thoát chương trình Client.")
                break
            
            if line == "mode json":
                client.is_json_mode = True
                print("[*] Đã chuyển sang chế độ đóng gói JSON (application/json)")
                continue
            elif line == "mode form":
                client.is_json_mode = False
                print("[*] Đã chuyển sang chế độ đóng gói Form (application/x-www-form-urlencoded)")
                continue
            
            parts = line.split()
            if parts[0] == "register":
                if len(parts) != 4:
                    print("[!] Cú pháp đúng: register <username> <password> <email>")
                    continue
                
                cmd, username, password, email = parts
                print(f"[*] Đang gửi yêu cầu đăng ký cho user: '{username}'...")
                
                code, text, json_dict, raw_body = client.send_register_request(username, password, email)
                
                msg = json_dict.get("message", raw_body or text)
                print(f"\n<<< PHẢN HỒI TỪ SERVER >>>")
                print(f"Mã trạng thái: HTTP/1.1 {code} {text}")
                print(f"Thông báo:     {msg}")
                print("-" * 50)
            else:
                print(f"[!] Lệnh không hợp lệ: '{line}'. Vui lòng dùng: register <username> <password> <email>")
                
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Đã thoát Client.")
            break


def main():
    if "--cli" in sys.argv:
        run_client_cli()
    else:
        run_client_gui()


if __name__ == "__main__":
    main()
