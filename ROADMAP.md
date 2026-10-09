# ROADMAP.md — Kế Hoạch Triển Khai Kokoro (心)

> **Single Source of Truth (SSoT)**: Tài liệu theo dõi lộ trình phát triển và danh mục công việc chi tiết của dự án **Kokoro — Personal Diary & Photo Journal PWA**.

---

## 📍 TIẾN ĐỘ TỔNG QUAN

- [x] **Milestone 0: Khởi tạo Dự án & Cơ Sở Hạ Tầng (PostgreSQL & Config)**
  - [x] Khởi tạo Git repo và liên kết Remote `https://github.com/thanhlongts2k/Kokoro.git`.
  - [x] Khảo sát môi trường Python (Python 3.14, Starlette, Uvicorn, Pillow, Google Auth, Psycopg2/3).
  - [x] Kiểm tra và kết nối thành công dịch vụ PostgreSQL 18 trên cổng 5432.
  - [x] Tạo cơ sở dữ liệu `kokoro_db`, chạy migration khởi tạo 5 bảng (`users`, `entries`, `entry_photos`, `tags`, `entry_tags`).
  - [x] Cấu hình file `.env` và module kết nối `app/config.py`, `app/database.py` (ThreadedConnectionPool).
  - [x] Thiết lập chuẩn tài liệu SSoT: `AGENTS.md`, `ARCHITECTURE.md`, `ROADMAP.md`.
  - [x] Thiết kế Mockup giao diện Soft Sakura Pastel / Healing Light Frosted Glassmorphism.

---

## 🚀 CÁC GIAI ĐOẠN TRIỂN KHAI (IMPLEMENTATION PHASES)

### 🔹 Giai đoạn 1: Thiết Kế & Xây Dựng Giao Diện PWA Tương Tác (Soft Sakura Pastel UI First)
- [x] Xây dựng hệ thống Design Tokens CSS Soft Sakura (`static/css/tokens.css`, `static/css/glass.css`, `static/css/layout.css`).
- [x] Thiết kế Layout PWA đa nền tảng Responsive (Theme Hồng Pastel Nhẹ Nhàng / Chữa Lành):
  - [x] Header với Logo hoa anh đào Kokoro (心), Nút cài đặt PWA, Profile Pill (Aria Tanaka).
  - [x] Timeline Feed với các thẻ nhật ký dạng kính mờ màu ngọc trai hồng (Pastel Frosted Glass Cards).
  - [x] Lưới hiển thị ảnh (Responsive Photo Grid: 1 ảnh, 2 ảnh, 3+ ảnh mosaic có badge `+X ảnh`).
  - [x] Bảng chọn cảm xúc (Mood Selector: Serene 🌸, Cozy ☕, Reflective 🌙, Grateful 🍵, Energetic ⚡).
  - [x] Khung lịch thu nhỏ (Mini Calendar View) đánh dấu ngày có nhật ký với chấm sáng hồng.
  - [x] Trình soạn thảo nhật ký tương tác (Modal trên Desktop & Bottom Sheet mượt mà trên Mobile) kèm tính năng kéo thả ảnh.
  - [x] Trình xem ảnh toàn màn hình (Photo Lightbox) hỗ trợ phím Escape và đóng nhanh.
- [x] Cấu hình PWA Manifest (`static/manifest.webmanifest`) và Service Worker (`static/sw.js`) để cài đặt làm ứng dụng độc lập trên điện thoại/máy tính.
- [x] Máy chủ Starlette ASGI hoạt động ổn định trên cổng `5050` (`http://localhost:5050`) kết nối CSDL PostgreSQL 18.

### 🔹 Giai đoạn 2: Xây Dựng Backend Starlette & PostgreSQL REST API
- [x] Thiết lập cấu trúc thư mục backend mô-đun (`app/`) và cấu hình pool kết nối PostgreSQL (`app/database.py`).
- [x] Xây dựng mô-đun Media Processing Pillow (`app/services/media_service.py`):
  - [x] Tiếp nhận file ảnh tải lên từ client (JPEG, PNG, WebP).
  - [x] Nén và chuyển đổi sang định dạng `.webp` chất lượng cao (quality 82%).
  - [x] Scale ảnh lớn về độ phân giải tối đa (max 1600px).
  - [x] Tự động sinh thumbnail WebP (max 400px) cho timeline feed hiển thị nhanh.
  - [x] Hàm dọn dẹp file an toàn trên đĩa khi xóa bài viết.
- [x] Xây dựng REST API cho Entries (`app/routes/entry_routes.py`):
  - [x] `GET /api/entries`: Lọc theo cảm xúc (mood), thẻ (tags), tháng (month), và tìm kiếm (search).
  - [x] `POST /api/entries`: Nhận multipart/form-data kèm nhiều ảnh thật, lưu trọn vẹn trong PostgreSQL transaction.
  - [x] `DELETE /api/entries/{id}`: Xóa bản ghi CSDL và dọn dẹp file ảnh trên đĩa.
  - [x] `PATCH /api/entries/{id}/pin`: Bật/tắt trạng thái ghim bài viết lên đầu trang.
  - [x] `GET /api/stats/summary`: Trả về số liệu thống kê thực tế từ CSDL.
  - [x] Static files endpoint phục vụ ảnh từ thư mục `uploads/` mượt mà qua cả cổng 5050 lẫn proxy sub-path `/kokoro/uploads/`.
- [x] Kết nối Frontend với API thực tế:
  - [x] Tạo `static/js/api.js` với base URL động linh hoạt (`API_BASE`), chống bẫy đường dẫn Nginx sub-path `/kokoro/`.
  - [x] Cập nhật `static/js/editor.js` đóng gói ảnh thật qua `FormData` và hiển thị trạng thái loading.
  - [x] Cập nhật `static/js/app.js` nạp dữ liệu từ PostgreSQL, bộ lọc đồng bộ API, và Toast notification Soft Sakura pastel.
- [x] Viết bộ kiểm thử tích hợp tự động (`tests/test_api_upload.py`) đạt 100% PASS và kiểm thử trực quan qua browser.

### 🔹 Giai đoạn 3: Tích Hợp Đăng Nhập Google Identity Services & Phân Quyền Dữ Liệu
- [x] Cấu hình Google Identity Services (GIS) trên giao diện PWA (`static/js/auth.js`) và Google Sign-In button container.
- [x] Backend xác thực Google ID Token thông qua thư viện `google-auth` (`verify_oauth2_token` trong `app/auth.py`).
- [x] Cơ chế Hybrid Auth linh hoạt: Hỗ trợ tài khoản Google thực tế và Mock Dev Profile (`Aria Tanaka`, `Kenji Sato`) với 1-click switcher.
- [x] Quản lý phiên đăng nhập an toàn bằng JWT Bearer Token & HttpOnly Session Cookie (`kokoro_session`).
- [x] Phân quyền dữ liệu độc lập & Cô lập tuyệt đối: Mọi endpoint `GET`, `POST`, `DELETE`, `PATCH /pin`, `GET /stats` gắn chặt điều kiện `WHERE user_id = :current_user_id`.
- [x] Giao diện Header nâng cấp: Profile Pill tròn, Menu dropdown chuyển đổi tài khoản, nút Đăng xuất, và Welcome / Login overlay dạng kính mờ Soft Sakura.
- [x] Sửa lỗi đồng bộ tài khoản Google OAuth (`upsert_user` với `RealDictCursor`) và phòng thủ phân tích cú pháp JSON cho Safari/iOS PWA.
- [x] Bộ kiểm thử tích hợp bảo mật tự động (`tests/test_auth_isolation.py`) đạt 100% PASS và kiểm thử trực quan trình duyệt.

### 🔹 Giai đoạn 4: Tính Năng Nâng Cao & Trải Nghiệm Ngoại Tuyến (Offline PWA)
- [ ] Lưu trữ bản nháp nhật ký ngoại tuyến (Offline Drafts qua `localStorage` / `IndexedDB`).
- [ ] Tự động đồng bộ bản nháp lên server khi có mạng trở lại.
- [ ] Biểu đồ thống kê tâm trạng (Mood & Writing Streak Stats).
- [ ] Tính năng Xuất dữ liệu nhật ký dự phòng (Export Backup dạng JSON/ZIP kèm ảnh).

### 🔹 Giai đoạn 5: Tối Ưu Hóa, Kiểm Thử & Chạy Production
- [ ] Kiểm thử tải ảnh dung lượng lớn (10MB+, nhiều ảnh cùng lúc).
- [ ] Kiểm thử tương thích trên thiết bị di động (iOS Safari PWA, Android Chrome PWA).
- [ ] Kiểm tra kết nối xuyên qua Nginx Reverse Proxy (Forwarded headers, WebSockets nếu cần).
- [ ] Bàn giao và tài liệu hóa hướng dẫn vận hành.
