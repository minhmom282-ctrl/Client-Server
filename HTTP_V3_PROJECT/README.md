# HTTP v3 – CHƯƠNG TRÌNH ĐĂNG KÝ TÀI KHOẢN MÔ HÌNH CLIENT–SERVER
**Đồ án môn học:** Lập trình hệ thống mạng  
**Đơn vị:** Khoa Công nghệ Thông tin – Trường Đại học Xây dựng Hà Nội (HUCE)  
**Nhóm thực hiện:** Nhóm 6  
**Giảng viên hướng dẫn:** ThS. Lê Đức Quang  

---

## 📖 GIỚI THIỆU ĐỀ TÀI
Chương trình hiện thực hóa mô hình **Client – Server** cho phép người dùng đăng ký tài khoản từ xa qua giao thức **HTTP/1.1** được lập trình trực tiếp trên nền **TCP Socket thô (Raw Socket)**, hoàn toàn không phụ thuộc vào các framework web có sẵn như Flask hay Django.

* **Cổng dịch vụ mặc định:** `TCP 8888`
* **Địa chỉ Server:** Lắng nghe trên `0.0.0.0`
* **Phương thức:** `POST`
* **Đường dẫn API:** `/register`
* **Định dạng dữ liệu hỗ trợ:**
  * `application/x-www-form-urlencoded` (Mặc định)
  * `application/json` (Tùy chọn)
* **Kho lưu trữ:** Tệp văn bản thuần `data/users.txt`
* **Mã hóa mật khẩu:** Băm chuẩn an toàn `SHA-256` (không lưu plain-text)
* **Xử lý đồng thời:** Đa luồng (`threading`) với khóa kiểm soát tranh chấp (`threading.Lock`) ngăn chặn Race Condition.

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```text
HTTP_V3_PROJECT/
│
├── main_server.py            # Điểm khởi chạy HTTP Server (mặc định GUI, hỗ trợ --cli)
├── main_client.py            # Điểm khởi chạy HTTP Client (mặc định GUI, hỗ trợ --cli)
├── run_server.bat            # Script khởi động nhanh Server GUI (Double-click trên Windows)
├── run_client.bat            # Script khởi động nhanh Client GUI (Double-click trên Windows)
├── run_server_cli.bat        # Script khởi động nhanh Server CLI
├── run_client_cli.bat        # Script khởi động nhanh Client CLI
├── run_tests.bat             # Script chạy kiểm thử tự động 10 kịch bản
│
├── server/                   # Module máy chủ (Server Engine)
│   ├── __init__.py
│   ├── http_server.py        # Socket TCP đa luồng, xử lý Request & Response
│   ├── request_handler.py    # Phân tích HTTPRequest và đóng gói HTTPResponse
│   ├── user_manager.py       # Quản lý tệp users.txt, băm SHA-256, khóa Lock Thread-safe
│   └── server_gui.py         # Giao diện đồ họa Server GUI (CustomTkinter)
│
├── client/                   # Module máy khách (Client Engine)
│   ├── __init__.py
│   ├── http_client.py        # Client Socket TCP, đóng gói POST Form/JSON
│   └── register_gui.py       # Giao diện đồ họa Client GUI (CustomTkinter)
│
├── common/                   # Tiện ích và cấu hình dùng chung
│   ├── __init__.py
│   ├── config.py             # Cấu hình Host, Port, Timeout, Path, HTTP Status
│   └── utils.py              # Băm SHA-256, Regex kiểm tra Email, Username, Password
│
├── data/
│   └── users.txt             # Lưu trữ: username<TAB>SHA-256(password)<TAB>email
│
├── logs/
│   └── server.log            # File nhật ký hoạt động thời gian thực của Server
│
├── tests/
│   └── test_all_cases.py     # Bộ kiểm thử tự động toàn diện 10 kịch bản
│
├── requirements.txt          # Thư viện phụ thuộc (customtkinter)
└── README.md                 # Hướng dẫn sử dụng và tài liệu kỹ thuật
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY CHƯƠNG TRÌNH

### 1. Yêu cầu môi trường
* **Hệ điều hành:** Windows 10/11, Linux hoặc macOS.
* **Ngôn ngữ:** Python 3.10 trở lên (khuyên dùng Python 3.12).

### 2. Cài đặt thư viện giao diện
Mở terminal hoặc PowerShell tại thư mục `HTTP_V3_PROJECT`:
```bash
pip install -r requirements.txt
```

---

### 3. Khởi chạy Server (Máy chủ)

#### Cách 1: Sử dụng giao diện đồ họa (Khuyên dùng)
* Nhấp đúp vào file `run_server.bat`  
* Hoặc chạy lệnh trong terminal:
```bash
python main_server.py
```
> **Thao tác trên giao diện:**
> 1. Nhấn nút **`START SERVER`** để mở cổng kết nối `8888`.
> 2. Theo dõi trạng thái chuyển sang **`ĐANG CHẠY`** (màu xanh lục).
> 3. Xem các chỉ số KPI thống kê và danh sách tài khoản đã đăng ký trên tab **`Quản lý tài khoản`**.
> 4. Nhấn **`STOP SERVER`** khi muốn tạm dừng hoặc giải phóng cổng mạng.

#### Cách 2: Sử dụng dòng lệnh (CLI Mode)
* Nhấp đúp vào file `run_server_cli.bat`
* Hoặc chạy lệnh:
```bash
python main_server.py --cli
```
* Nhập `start` để khởi động, `stop` để dừng, `exit` để thoát.

---

### 4. Khởi chạy Client (Máy khách đăng ký)

#### Cách 1: Sử dụng giao diện đồ họa (Khuyên dùng)
* Nhấp đúp vào file `run_client.bat`  
* Hoặc chạy lệnh trong terminal:
```bash
python main_client.py
```
> **Thao tác trên giao diện:**
> 1. Nhập **Tên đăng nhập (Username)**, **Mật khẩu (Password)**, **Xác nhận mật khẩu** và **Email**.
> 2. Có thể chọn định dạng gửi: **Form URL-encoded** hoặc **JSON**.
> 3. Nhấn nút biểu tượng mắt `👁` để ẩn/hiện mật khẩu.
> 4. Nhấn **`REGISTER`** để gửi yêu cầu đăng ký lên Server.
> 5. Quan sát thông báo kết quả trả về:
>    * 🟢 **201 Created:** Đăng ký thành công.
>    * 🟡 **409 Conflict:** Tên đăng nhập đã được sử dụng.
>    * 🔴 **400 Bad Request:** Dữ liệu trống hoặc sai định dạng.

#### Cách 2: Sử dụng dòng lệnh (CLI Mode)
* Nhấp đúp vào file `run_client_cli.bat`
* Hoặc chạy lệnh:
```bash
python main_client.py --cli
```
* Đăng ký tài khoản bằng cú pháp:
```text
client> register <username> <password> <email>
```
* Ví dụ:
```text
client> register tuan_kd MatKhau123 tuan@nuce.edu.vn
```

---

## 🧪 KẾT QUẢ KIỂM THỬ 10 KỊCH BẢN (TEST SUITE)

Hệ thống đã được tích hợp bộ kiểm thử tự động toàn diện trong `tests/test_all_cases.py`.  
Để chạy toàn bộ kiểm thử, nhấp đúp vào `run_tests.bat` hoặc thực hiện lệnh:
```bash
python tests/test_all_cases.py
```

### Bảng tổng hợp kết quả kiểm thử:

| STT | Kịch bản kiểm thử | Mô tả kịch bản | Kết quả đạt được |
| :---: | :--- | :--- | :---: |
| **TEST 1** | Đăng ký tài khoản mới | Gửi thông tin hợp lệ | **HTTP 201 Created** ✔ |
| **TEST 2** | Đăng ký lại username đã tồn tại | Gửi trùng username đã có | **HTTP 409 Conflict** ✔ |
| **TEST 3** | Để trống username | Gửi dữ liệu thiếu trường | **HTTP 400 Bad Request** ✔ |
| **TEST 4** | Nhập email sai định dạng | Nhập email không có `@` hoặc sai regex | **HTTP 400 Bad Request** ✔ |
| **TEST 5** | Nhập sai đường dẫn | Gửi POST đến `/api/login` | **HTTP 404 Not Found** ✔ |
| **TEST 6** | Sai phương thức | Gửi GET đến `/register` | **HTTP 405 Method Not Allowed** ✔ |
| **TEST 7** | Tắt Server rồi đăng ký | Thao tác khi Server đang STOP | **Connection Refused (Báo lỗi mất kết nối)** ✔ |
| **TEST 8** | Hai Client đồng thời đăng ký cùng username | Mô phỏng Race condition qua Barrier | **1 Client đạt 201, 1 Client nhận 409 (Thread-safe Lock)** ✔ |
| **TEST 9** | Khởi động lại Server | Tắt Server và mở lại | **Dữ liệu users.txt vẫn bảo toàn nguyên vẹn** ✔ |
| **TEST 10**| Đăng ký bằng cả hai định dạng | Kiểm thử Form URL-encoded và JSON | **Cả hai định dạng đều phản hồi 201 Created** ✔ |

---

## 🔒 AN TOÀN BẢO MẬT & ĐỒNG BỘ DỮ LIỆU

1. **Băm mật khẩu SHA-256:**  
   Mật khẩu không bao giờ được lưu dưới dạng văn bản thô. Tệp `users.txt` chỉ lưu trữ chuỗi băm hex 64 ký tự.
2. **Ngăn chặn Race Condition:**  
   Thao tác tra cứu username và ghi tệp được đồng bộ hóa tuyệt đối bằng `threading.Lock()` trong lớp `UserRepository`.
3. **Phòng chống tấn công cạn kiệt bộ nhớ:**  
   Header `Content-Length` được kiểm soát giới hạn tối đa `MAX_PAYLOAD_SIZE = 1MB`. Nếu vượt quá sẽ trả về mã `413 Payload Too Large`.
4. **Kiểm soát nghẽn kết nối (Timeout):**  
   Socket Client có thời gian chờ tối đa 10 giây. Sau thời gian này nếu không gửi đủ dữ liệu, kết nối sẽ bị đóng an toàn với mã `400 Bad Request`.
