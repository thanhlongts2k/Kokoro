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
- [x] Lưu trữ bản nháp nhật ký ngoại tuyến (Offline Drafts qua `localStorage` với debounce 1s theo `user_id` kèm nút xóa bản nháp).
- [x] Hàng đợi ngoại tuyến (Offline Queue qua `IndexedDB` lưu Blob/File an toàn, tự động đồng bộ khi có mạng trở lại qua sự kiện `online`).
- [x] Biểu đồ thống kê tâm trạng đa phân đoạn (Multi-segment Mood Progress Bar) & Tính toán chuỗi ngày viết liên tiếp (Streak Days).
- [x] Tính năng Xuất dữ liệu nhật ký dự phòng cô lập theo người dùng (`GET /api/entries/export` file JSON attachment).
- [x] Tích hợp mục "Sao lưu dữ liệu (JSON)" vào Profile Dropdown Header và Toast thông báo trạng thái mạng Online/Offline.
- [x] Viết bộ kiểm thử tích hợp tự động `tests/test_phase4_features.py` đạt 100% PASS và kiểm thử trực quan trình duyệt.

### 🔹 Giai đoạn 5: Tối Ưu Hóa, Kiểm Thử & Chạy Production
- [x] Tối ưu hóa bộ nhớ đệm HTTP: Header `Cache-Control: public, max-age=31536000, immutable` cho ảnh tĩnh và `no-cache` cho HTML.
- [x] Service Worker (`sw.js`): Nâng cấp cache name lên `kokoro-v1.2.0`, tối ưu chiến lược Cache-First và Network-First.
- [x] Stress Test & Xử lý ảnh lớn: Kiểm thử tải lên 4 ảnh 4000x3000 đa luồng, xử lý EXIF Orientation xoay tự động, tỷ lệ nén WebP đạt 98.4%.
- [x] Tối ưu hóa Reverse Proxy: Middleware ASGI xử lý `X-Forwarded-Proto`, `X-Forwarded-Prefix`, tin cậy proxy IP và mở rộng CORS `Content-Disposition`.
- [x] Tính năng Khôi phục Dữ liệu (`POST /api/entries/import`): Hỗ trợ nhập lại file sao lưu JSON an toàn vào tài khoản người dùng kèm UI 1-click.
- [x] Toàn bộ 4 bộ test suite (`test_api_upload`, `test_auth_isolation`, `test_phase4_features`, `test_phase5_stress`) đạt 100% PASS.

### 🔹 Giai đoạn 6: Hoàn Thiện Trải Nghiệm & Core CRUD (v1.3.0 Release)
- [x] Tính năng Chỉnh sửa Nhật ký (`PUT /api/entries/{id}`):
  - [x] Backend Starlette: Xác thực quyền sở hữu `user_id`, cập nhật `title`, `content`, `mood`, `weather`, `entry_date`, `tags`, và đính kèm thêm ảnh WebP qua Pillow.
  - [x] Frontend Editor: Nút icon bút chì trên thẻ bài viết, nạp sẵn dữ liệu cũ (prefill) và nút bấm "Cập nhật bài viết ✨".
- [x] Hộp thoại xác nhận xóa tùy biến (Soft Sakura Confirm Modal):
  - [x] Loại bỏ hoàn toàn `window.confirm()` mặc định; xây dựng modal `#delete-confirm-modal` kính mờ Soft Sakura với icon hoa anh đào, thông điệp "Buông Bỏ Khoảnh Khắc 🍃", 2 nút bấm bo tròn "Giữ lại" và "Xác nhận xóa", hỗ trợ phím `Esc` và click backdrop.
- [x] Tìm kiếm tức thì (Debounced Live Search 300ms):
  - [x] Tự động lọc realtime bài viết theo tiêu đề, nội dung và hashtag mà không cần bấm Enter; có nút `[x]` xóa nhanh từ khóa.
- [x] Chế độ ban đêm "Night Sakura" (Dark Theme Toggle 🌙🌸):
  - [x] Bộ token CSS `[data-theme="dark"]` trong `tokens.css`: Tím than / đen sương khói dịu mắt (`#0f1016` ~ `#161622`), kính mờ tối (`rgba(26, 25, 40, 0.78)`), chữ xám ngọc trai (`#f8fafc`) và phát quang hồng neon pastel (`#f472b6`).
  - [x] Nút Sun/Moon trên Header chuyển đổi mượt mà, lưu trạng thái lâu dài qua `localStorage('kokoro_theme')`.
- [x] Kiểm thử toàn diện: Bổ sung `tests/test_edit_and_ux.py` đạt 100% PASS; toàn bộ 5 test suites của dự án đều đạt 100% PASS.

### 🔹 Giai đoạn 7: Bảo Mật & Không Gian Chữa Lành (v1.4.0 Release)
- [x] Khóa bảo mật mã PIN 4 số (`static/js/passcode.js`):
  - [x] Mã hóa mật khẩu phía client chuẩn WebCrypto API SHA-256 kết hợp 128-bit random salt, lưu trữ an toàn trong `localStorage`.
  - [x] Giao diện màn hình khóa kính mờ Soft Sakura (`#passcode-lock-overlay`, `backdrop-filter: blur(32px)`), 4 chấm PIN hoa anh đào phát quang khi nhập.
  - [x] Bàn phím số ảo 0-9 mượt mà, hỗ trợ cả bàn phím vật lý từ máy tính (phím số, Backspace, Esc, Enter), hiệu ứng rung lắc (shake animation) khi sai PIN.
  - [x] Cơ chế tự động khóa tạm 30 giây khi nhập sai liên tiếp quá 5 lần để phòng chống brute-force.
  - [x] Quản lý phiên mở khóa an toàn qua `sessionStorage`, bộ đếm thời gian tự khóa khi không tương tác (Inactivity Timer: 2m/5m) và khóa tức thì khi chuyển tab/ẩn ứng dụng.
  - [x] Tích hợp cài đặt trong Profile Menu: Bật/Tắt khóa PIN, Đổi mã PIN, cài đặt thời gian tự khóa, và nút Khóa màn hình tức thì.
- [x] Bộ phát âm thanh thư giãn Zen Ambient Sound Player (`static/js/zen-audio.js`):
  - [x] Bổ sung 4 bản âm thanh ambient nhẹ nhàng, nén nhẹ chuẩn 64kbps trong `static/audio/` (tổng ~627KB): `rain.mp3`, `furin.mp3`, `waves.mp3`, `stream.mp3`.
  - [x] Vòng lặp liền mạch (`seamless loop`), tự động chuyển bài mượt mà, hỗ trợ hiệu ứng chuyển âm tăng/giảm từ từ (smooth volume fading).
  - [x] Thanh điều chỉnh âm lượng (Volume Slider), nút bật/tắt tiếng (Mute toggle) và ghi nhớ mức âm lượng qua `localStorage`.
  - [x] Widget Mini Player tinh tế tại Header với icon sóng âm hoạt họa (`soundwave bars`) phát quang khi phát, bảng điều khiển mở rộng dạng popover kính mờ.
  - [x] Hỗ trợ đường dẫn tương đối động (`dynamic base path`) chống bẫy sub-path Nginx và tuân thủ Autoplay Policy.
- [x] Nâng cấp Service Worker & Cache ngoại tuyến:
  - [x] Cập nhật cache name lên `kokoro-v1.4.0` trong `static/sw.js`, nạp trước 4 file audio cho trải nghiệm phát nhạc hoàn toàn ngoại tuyến.
  - [x] Cập nhật số hiệu phiên bản `v1.4.0` đồng bộ trên Footer và `app/config.py`.
- [x] Kiểm thử toàn diện & Nghiệm thu:
  - [x] Bổ sung test suite `tests/test_v14_features.py` đạt 100% PASS; toàn bộ 6 test suites của dự án đều đạt 100% PASS.
