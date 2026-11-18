"""
Bộ kiểm thử tự động toàn diện 10 kịch bản (Comprehensive Test Suite)
Kiểm tra đầy đủ 10 trường hợp theo đúng mục IX của yêu cầu đồ án:
- TEST 1: Đăng ký tài khoản mới (201 Created)
- TEST 2: Đăng ký lại username đã tồn tại (409 Conflict)
- TEST 3: Để trống username (400 Bad Request)
- TEST 4: Email sai định dạng (400 Bad Request)
- TEST 5: Nhập sai đường dẫn (404 Not Found)
- TEST 6: Phương thức GET đến /register (405 Method Not Allowed)
- TEST 7: Tắt Server rồi đăng ký (Không kết nối được)
- TEST 8: Hai Client cùng đăng ký một username tại cùng thời điểm (Race Condition Prevention)
- TEST 9: Khởi động lại Server (Dữ liệu users.txt vẫn bảo toàn)
- TEST 10: Đăng ký thành công bằng cả Form URL-encoded và JSON
"""
import sys
import os
import time
import shutil
import threading
from typing import List, Tuple

# Thêm đường dẫn gốc vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import DEFAULT_PORT, DEFAULT_CLIENT_HOST, USERS_FILE
from server.http_server import HTTPServer
from server.user_manager import UserRepository
from client.http_client import HTTPClient


def print_test_header(test_id: int, title: str):
    print("\n" + "=" * 70)
    print(f"▶ CHẠY TEST {test_id}: {title}")
    print("=" * 70)


def run_all_tests():
    # Sử dụng cổng kiểm thử riêng (8889) để không xung đột với ứng dụng chính nếu đang mở
    test_port = 8889
    test_host = "127.0.0.1"
    
    # Tạo UserRepository trỏ vào file tạm để kiểm thử
    temp_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_users.txt")
    if os.path.exists(temp_data_file):
        os.remove(temp_data_file)
        
    test_repo = UserRepository(filepath=temp_data_file)
    server = HTTPServer(host="0.0.0.0", port=test_port, user_repo=test_repo)
    
    # Tắt log in ra console của server trong lúc chạy test để output kiểm thử rõ ràng
    server.log_callback = lambda msg, lvl: None
    
    success, msg = server.start()
    assert success, f"Không thể khởi động test server: {msg}"
    time.sleep(0.3)
    
    client = HTTPClient(host=test_host, port=test_port)
    results = {}

    try:
        # -------------------------------------------------------------
        # TEST 1: Đăng ký tài khoản mới -> 201 Created
        # -------------------------------------------------------------
        print_test_header(1, "Đăng ký tài khoản mới (Kỳ vọng: 201 Created)")
        code, text, json_d, raw = client.send_register_request("user_test1", "Pass123456", "user1@nuce.edu.vn", use_json=False)
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 201, f"Kỳ vọng 201 nhưng nhận được {code}"
        results["TEST 1"] = "PASSED (201 Created)"

        # -------------------------------------------------------------
        # TEST 2: Đăng ký lại username đã tồn tại -> 409 Conflict
        # -------------------------------------------------------------
        print_test_header(2, "Đăng ký lại username đã tồn tại (Kỳ vọng: 409 Conflict)")
        code, text, json_d, raw = client.send_register_request("user_test1", "AnotherPass999", "another@nuce.edu.vn", use_json=False)
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 409, f"Kỳ vọng 409 nhưng nhận được {code}"
        results["TEST 2"] = "PASSED (409 Conflict)"

        # -------------------------------------------------------------
        # TEST 3: Để trống username -> 400 Bad Request
        # -------------------------------------------------------------
        print_test_header(3, "Để trống username (Kỳ vọng: 400 Bad Request)")
        headers, body = client.package_data("", "Pass123456", "user3@nuce.edu.vn", use_json=False)
        code, text, json_d, raw = client.send_custom_request(method="POST", path="/register", headers=headers, body=body)
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 400, f"Kỳ vọng 400 nhưng nhận được {code}"
        results["TEST 3"] = "PASSED (400 Bad Request)"

        # -------------------------------------------------------------
        # TEST 4: Nhập email sai định dạng -> 400 Bad Request
        # -------------------------------------------------------------
        print_test_header(4, "Nhập email sai định dạng (Kỳ vọng: 400 Bad Request)")
        code, text, json_d, raw = client.send_register_request("user_test4", "Pass123456", "email_sai_dinh_dang", use_json=False)
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 400, f"Kỳ vọng 400 nhưng nhận được {code}"
        results["TEST 4"] = "PASSED (400 Bad Request)"

        # -------------------------------------------------------------
        # TEST 5: Nhập sai đường dẫn -> 404 Not Found
        # -------------------------------------------------------------
        print_test_header(5, "Nhập sai đường dẫn /api/login (Kỳ vọng: 404 Not Found)")
        headers, body = client.package_data("user_test5", "Pass123456", "user5@nuce.edu.vn", use_json=False)
        code, text, json_d, raw = client.send_custom_request(method="POST", path="/api/login", headers=headers, body=body)
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 404, f"Kỳ vọng 404 nhưng nhận được {code}"
        results["TEST 5"] = "PASSED (404 Not Found)"

        # -------------------------------------------------------------
        # TEST 6: Gửi phương thức GET đến /register -> 405 Method Not Allowed
        # -------------------------------------------------------------
        print_test_header(6, "Gửi phương thức GET đến /register (Kỳ vọng: 405 Method Not Allowed)")
        code, text, json_d, raw = client.send_custom_request(method="GET", path="/register", headers={}, body="")
        print(f"Kết quả nhận được: HTTP {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 405, f"Kỳ vọng 405 nhưng nhận được {code}"
        results["TEST 6"] = "PASSED (405 Method Not Allowed)"

        # -------------------------------------------------------------
        # TEST 7: Tắt Server rồi thực hiện đăng ký -> Báo lỗi kết nối
        # -------------------------------------------------------------
        print_test_header(7, "Tắt Server rồi thực hiện đăng ký (Kỳ vọng: Lỗi kết nối)")
        server.stop()
        time.sleep(0.3)
        code, text, json_d, raw = client.send_register_request("user_test7", "Pass123456", "user7@nuce.edu.vn")
        print(f"Kết quả nhận được: Status {code} {text} | Thông báo: {json_d.get('message')}")
        assert code == 0, f"Kỳ vọng code=0 (kết nối thất bại) nhưng nhận được {code}"
        results["TEST 7"] = "PASSED (Connection Refused)"

        # Khởi động lại server để tiếp tục các bài test còn lại
        server.start()
        time.sleep(0.3)

        # -------------------------------------------------------------
        # TEST 8: Hai Client cùng đăng ký một username đồng thời (Concurrency)
        # -------------------------------------------------------------
        print_test_header(8, "Hai Client cùng đăng ký một username đồng thời (Kỳ vọng: 1 thành công 201, 1 trùng 409)")
        simultaneous_user = "concurrent_user"
        barrier = threading.Barrier(2)
        sim_results: List[int] = []
        lock = threading.Lock()

        def register_worker():
            c = HTTPClient(host=test_host, port=test_port)
            barrier.wait() # Đồng bộ xuất phát cùng một thời điểm chính xác
            c_code, _, _, _ = c.send_register_request(simultaneous_user, "Pass123456", "sim@nuce.edu.vn")
            with lock:
                sim_results.append(c_code)

        t1 = threading.Thread(target=register_worker)
        t2 = threading.Thread(target=register_worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        print(f"Mã trạng thái nhận được từ 2 Client: {sim_results}")
        assert sorted(sim_results) == [201, 409], f"Kỳ vọng đúng [201, 409] nhưng nhận được {sim_results}"
        results["TEST 8"] = "PASSED (1 Thành công 201, 1 Xung đột 409 - Thread-safe Lock an toàn)"

        # -------------------------------------------------------------
        # TEST 9: Khởi động lại Server -> Dữ liệu users.txt vẫn bảo toàn
        # -------------------------------------------------------------
        print_test_header(9, "Khởi động lại Server và kiểm tra bảo toàn dữ liệu")
        server.stop()
        time.sleep(0.3)
        
        # Khởi động lại Server mới với cùng repository
        server2 = HTTPServer(host="0.0.0.0", port=test_port, user_repo=test_repo)
        server2.log_callback = lambda msg, lvl: None
        server2.start()
        time.sleep(0.3)

        # Kiểm tra tài khoản user_test1 đã đăng ký ở TEST 1 vẫn còn
        found = test_repo.find_by_username("user_test1")
        print(f"Tra cứu user_test1 sau khởi động lại: {found.username if found else 'Không tìm thấy'}")
        assert found is not None and found.username == "user_test1", "Tài khoản bị mất sau khi khởi động lại server!"
        
        # Thử đăng ký trùng trên server mới
        c2 = HTTPClient(host=test_host, port=test_port)
        code, text, json_d, raw = c2.send_register_request("user_test1", "NewPass999", "dup@nuce.edu.vn")
        assert code == 409, f"Kỳ vọng 409 sau khi khởi động lại nhưng nhận {code}"
        results["TEST 9"] = "PASSED (Dữ liệu users.txt vẫn bảo toàn nguyên vẹn)"
        
        server = server2

        # -------------------------------------------------------------
        # TEST 10: Đăng ký bằng cả hai định dạng Form URL-encoded và JSON
        # -------------------------------------------------------------
        print_test_header(10, "Đăng ký bằng cả Form URL-encoded và JSON")
        # 10a. Form URL-encoded
        code_form, _, json_form, _ = client.send_register_request("user_form_fmt", "Pass123456", "form@nuce.edu.vn", use_json=False)
        print(f"10a. Form URL-encoded -> HTTP {code_form}: {json_form.get('message')}")
        assert code_form == 201, f"Form URL-encoded kỳ vọng 201 nhưng nhận {code_form}"

        # 10b. JSON
        code_json, _, json_json, _ = client.send_register_request("user_json_fmt", "Pass123456", "json@nuce.edu.vn", use_json=True)
        print(f"10b. JSON format      -> HTTP {code_json}: {json_json.get('message')}")
        assert code_json == 201, f"JSON format kỳ vọng 201 nhưng nhận {code_json}"

        results["TEST 10"] = "PASSED (Cả hai định dạng Form và JSON đều hoạt động chính xác)"

    finally:
        server.stop()
        if os.path.exists(temp_data_file):
            try:
                os.remove(temp_data_file)
            except Exception:
                pass

    print("\n" + "=" * 70)
    print("                    TỔNG KẾT KẾT QUẢ KIỂM THỬ")
    print("=" * 70)
    all_passed = True
    for test_name, res in results.items():
        print(f"  ✔ {test_name}: {res}")
    print("=" * 70)
    print(">>> TẤT CẢ 10 BÀI TEST ĐỀU ĐẠT CHUẨN 100%! <<<\n")


if __name__ == "__main__":
    run_all_tests()
