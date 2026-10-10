# CHANGELOG.md — Nhật Ký Thay Đổi Kokoro (心)

Tất cả các thay đổi đáng chú ý của dự án **Kokoro — Personal Diary & Photo Journal PWA** được ghi nhận chi tiết tại tệp này theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) và tuân thủ [Semantic Versioning (SemVer)](https://semver.org/).

---

## [1.4.0] - 2026-10-10
### Added
- **Khóa Bảo Mật Mã PIN 4 Số (Passcode Lock - WebCrypto SHA-256 + Salt):**
  - Bảo mật phía Client: Ứng dụng WebCrypto API tiêu chuẩn (`window.crypto.subtle.digest('SHA-256', ...)`) kết hợp Salt 128-bit ngẫu nhiên (`crypto.getRandomValues`) lưu trữ tại `localStorage`, triệt tiêu hoàn toàn nguy cơ tấn công Rainbow Table.
  - Giao diện Màn hình khóa Soft Sakura Kính mờ (`#passcode-lock-overlay`): Nền blur cao (`backdrop-filter: blur(32px)`) che mờ hoàn toàn nội dung nhật ký, 4 chấm PIN bo tròn dạng hoa anh đào đổi màu và phát quang hồng pastel khi nhập.
  - Bàn phím số ảo 0-9 mượt mà, hỗ trợ cả bàn phím vật lý từ máy tính (hỗ trợ Backspace, Enter, Esc), hiệu ứng rung lắc (shake animation) khi nhập sai PIN.
  - Cơ chế tự khóa tạm 30 giây khi nhập sai liên tiếp quá 5 lần để phòng chống tấn công brute-force.
  - Quản lý phiên mở khóa an toàn qua `sessionStorage`, đi kèm bộ hẹn giờ tự động khóa khi không tương tác (Inactivity Timer: 2 phút / 5 phút / Không bao giờ) và khóa ngay lập tức khi chuyển tab (`visibilitychange`).
  - Tích hợp menu tùy chọn trong Profile Dropdown: Bật/Tắt khóa PIN, Đổi mã PIN, cài đặt thời gian tự khóa, và nút "Khóa màn hình ngay 🔒".
- **Bộ Phát Âm Thanh Thư Giãn (Zen Ambient Sound Player):**
  - Bổ sung 4 bản âm thanh ambient chất lượng cao, nén nhẹ chuẩn 64kbps trong `static/audio/` (tổng dung lượng ~627KB):
    * `rain.mp3` (Mưa rơi êm đềm — 145.1 KB)
    * `furin.mp3` (Chuông gió Nhật Bản — 160.7 KB)
    * `waves.mp3` (Sóng biển đêm — 176.4 KB)
    * `stream.mp3` (Suối thiền Zen — 145.1 KB)
  - Kiến trúc phát âm thanh: Vòng lặp liền mạch (`seamless loop`), tự động chuyển bài mượt mà, hỗ trợ hiệu ứng chuyển âm tăng/giảm từ từ (smooth volume fading).
  - Thanh điều chỉnh âm lượng (Volume Slider) mượt mà kèm nút bật/tắt tiếng (Mute toggle) và ghi nhớ âm lượng qua `localStorage`.
  - Widget Mini Player tinh tế tại Header với icon sóng âm hoạt họa (`soundwave bars`) phát quang khi đang phát âm thanh, bảng điều khiển mở rộng dạng popover kính mờ.
  - Tương thích 100% với chính sách Autoplay Policy của trình duyệt và hỗ trợ đường dẫn tương đối động (`dynamic base path`).
- **Nâng Cấp Service Worker & Cache Ngoại Tuyến (Offline PWA):**
  - Nâng cấp phiên bản cache Service Worker lên `kokoro-v1.4.0` trong `static/sw.js`.
  - Nạp trước toàn bộ 4 file âm thanh trong `static/audio/` cùng các file kịch bản mới (`passcode.js`, `zen-audio.js`), cho phép trải nghiệm phát nhạc thiền hoàn toàn ngoại tuyến khi mất mạng.
  - Cập nhật số hiệu phiên bản ứng dụng `v1.4.0` đồng bộ trên Footer và `app/config.py`.
- **Kiểm Thử Tự Động & Hồi Quy:**
  - Bổ sung test suite `tests/test_v14_features.py` kiểm thử 5 bước: Kiểm tra version endpoint `GET /api/health`, tính toàn vẹn 4 file audio trên đĩa và phục vụ qua HTTP, thuật toán mã hóa SHA-256 + 128-bit salt, và kiểm tra hồi quy CRUD; đạt 100% PASS trên tất cả các bộ test suite.

---

## [1.3.0] - 2026-10-10
### Added
- **Tính Năng Chỉnh Sửa Nhật Ký (Edit Entry - PUT /api/entries/{id}):**
  - Backend: Thêm endpoint `PUT /api/entries/{id:int}` phân quyền nghiêm ngặt theo `current_user_id`, cập nhật metadata (`title`, `content`, `mood`, `weather`, `entry_date`, `tags`, `updated_at`) và hỗ trợ bổ sung ảnh mới nén WebP bằng Pillow.
  - Client: Bổ sung phương thức `KokoroAPI.updateEntry(id, formData)`, thêm nút icon bút chì (`data-action="edit"`) trên từng thẻ bài viết, nạp sẵn dữ liệu cũ (prefill) vào Editor modal và đổi nhãn nút lưu thành "Cập nhật bài viết ✨".
- **Hộp Thoại Xác Nhận Xóa Tùy Biến (Soft Sakura Confirm Modal):**
  - Loại bỏ hoàn toàn `window.confirm()` mặc định của trình duyệt; xây dựng `#delete-confirm-modal` phong cách kính mờ Soft Sakura với icon hoa rơi, thông điệp chữa lành *"Bạn có chắc muốn buông bỏ khoảnh khắc này không? 🍃"*, hai nút bo tròn "Giữ lại" và "Xác nhận xóa", hỗ trợ phím tắt `Esc` và click backdrop.
- **Tìm Kiếm Tức Thì (Debounced Live Search 300ms):**
  - Tích hợp thanh tìm kiếm `#search-input` với kỹ thuật debounce 300ms, tự động lọc danh sách bài viết theo tiêu đề, nội dung và thẻ chủ đề mà không cần bấm Enter; có nút xóa nhanh `[x]`.
- **Chế Độ Ban Đêm "Night Sakura" (Dark Theme Toggle 🌙🌸):**
  - Thiết lập bảng màu Dark Mode `[data-theme="dark"]` trong `tokens.css`: Nền tối tím than / đen sương khói dịu mắt (`#0f1016` ~ `#161622`), thẻ bài viết kính mờ tối (`rgba(26, 25, 40, 0.78)`), chữ xám ngọc trai (`#f8fafc`), viền và điểm nhấn phát quang hồng neon pastel nhẹ nhàng (`#f472b6`).
  - Thêm nút Sun/Moon trên Header, tự động lưu và khôi phục theme qua `localStorage('kokoro_theme')`.
- **Kiểm Thử Tự Động (Test Suite):**
  - Bổ sung `tests/test_edit_and_ux.py` kiểm thử 11 bước bao gồm tính cô lập dữ liệu khi sửa bài, cập nhật ảnh, validation nội dung rỗng và tìm kiếm từ khóa, đạt 100% PASS. Toàn bộ 5 test suites của dự án đều đạt 100% PASS.

---

## [1.2.0] - 2026-10-10
### Added
- **Tối Ưu Bộ Nhớ Đệm & Header Caching:**
  - Áp dụng cấu hình `ImmutableStaticFiles` cho toàn bộ media tải lên trong `uploads/originals/` và `uploads/thumbnails/` với header `Cache-Control: public, max-age=31536000, immutable`.
  - Cấu hình `AppStaticFiles` thiết lập `Cache-Control: no-cache, must-revalidate` cho file HTML để đảm bảo client luôn nhận phiên bản giao diện mới nhất, kết hợp cache 24h cho các asset tĩnh (`.css`, `.js`, `.svg`).
  - Nâng cấp Service Worker cache name lên `kokoro-v1.2.0` trong `static/sw.js`.
- **Tối Ưu Nginx Reverse Proxy & CORS:**
  - Bổ sung `ProxyHeadersMiddleware` tin cậy và xử lý đúng `X-Forwarded-Proto` (HTTPS) và `X-Forwarded-Prefix` (hỗ trợ sub-path `/kokoro/`).
  - Mở rộng CORS Middleware hỗ trợ đầy đủ các phương thức HTTP và phơi bày header `Access-Control-Expose-Headers: Content-Disposition` phục vụ tải file đính kèm.
- **Tính Năng Khôi Phục Dữ Liệu (Import Backup JSON):**
  - Endpoint `POST /api/entries/import`: Tiếp nhận file JSON backup hoặc payload, khôi phục toàn bộ bài viết, tâm trạng, thời gian, tags và ảnh liên kết vào tài khoản người dùng hiện tại trong một database transaction an toàn.
  - Giao diện người dùng: Tích hợp nút "Khôi phục dữ liệu (JSON)" và input file ẩn trong Profile Dropdown menu, tự động reload feed và thống kê sau khi import thành công.
- **Stress Test & Xử Lý Ảnh Lớn (EXIF Orientation):**
  - Bổ sung `tests/test_phase5_stress.py`: Kiểm thử tải đồng thời 4 ảnh độ phân giải 4000x3000 kèm EXIF orientation tag 6 (xoay 90 độ), xác nhận ảnh được xoay đúng chiều chân dung, resize về max 1600px và nén WebP giảm dung lượng đến 98.4%.

---

## [1.1.0] - 2026-10-10
### Added
- **Offline Storage & Auto-Save:**
  - Tự động lưu bản nháp (Editor Drafts) với debounce 1s vào `localStorage` phân tách theo `user_id`. Tự động khôi phục bản nháp kèm banner trực quan và nút "Xóa bản nháp" khi mở lại modal/sheet.
  - Hàng đợi ngoại tuyến (Offline Queue) qua `IndexedDB` (`kokoro_offline_db` / store `pending_entries`) lưu trữ an toàn các đối tượng `File`/`Blob` và bài viết chữ khi mất kết nối mạng, triệt tiêu hoàn toàn rủi ro tràn hạn mức 5MB của `localStorage`.
  - Tự động lắng nghe sự kiện `window.addEventListener('online')` để duyệt hàng đợi gửi lên backend và hiển thị Toast thông báo: *"Đã đồng bộ bài viết ngoại tuyến thành công! 🌸"*.
- **Backend API Export & Rich Stats (`app/routes/entry_routes.py`):**
  - `GET /api/entries/export`: Xuất dữ liệu nhật ký của người dùng hiện tại dưới dạng file JSON đính kèm header `Content-Disposition: attachment; filename=kokoro_backup_{date}.json`, bao gồm đầy đủ metadata, danh sách tags và ảnh. Đảm bảo cô lập dữ liệu 100%.
  - `GET /api/stats/summary`: Làm giàu số liệu thống kê với phân bổ chi tiết 5 tâm trạng (`serene`, `cozy`, `reflective`, `grateful`, `energetic`) gồm số lượng và tỷ lệ %, cùng thuật toán tính toán chuỗi ngày viết liên tiếp (Streak Days) thực tế dựa trên trường `entry_date`.
- **Nâng Cấp Giao Diện Soft Sakura UI/UX:**
  - Thẻ "Hành trình cảm xúc" trang bị thanh tiến trình đa phân đoạn (Multi-segment progress bar) phân bổ trực quan tỷ lệ 5 cảm xúc kèm các điểm chú thích (legend dots) màu pastel hài hòa.
  - Bổ sung tùy chọn "Sao lưu dữ liệu (JSON)" vào Profile Dropdown menu ở Header.
  - Tích hợp Toast thông báo trạng thái kết nối mạng khi chuyển đổi Online/Offline.
- **Kiểm Thử Tự Động Toàn Diện:**
  - Bộ test suite `tests/test_phase4_features.py` kiểm thử 6 bước: chặn xuất dữ liệu unauthenticated, xuất JSON backup, xác thực tính cô lập dữ liệu 2 chiều giữa các tài khoản, kiểm tra cấu trúc Rich Stats và thuật toán tính Streak Days (đạt 100% PASS).

---

## [1.0.3] - 2026-10-09
### Fixed
- **Google OAuth Upsert Crash:** Sửa lỗi `TypeError: object is not iterable` khi gọi `dict(user)` trong `app/auth.py` bằng cách chỉ định `cursor_factory=RealDictCursor`.
- **Safari WebKit Error Parsing:** Triệt tiêu lỗi `SyntaxError: The string did not match the expected pattern` trên Safari iOS bằng cách xây dựng hàm `parseResponse()` an toàn đọc raw text trước khi `JSON.parse` trong `static/js/api.js`.
- **Database Conflict Handling:** Cải tiến logic `upsert_user` kiểm tra đồng thời cả `google_id` và `email` để cập nhật an toàn, tránh vi phạm ràng buộc Unique constraint khi liên kết tài khoản.
- **Starlette Error Handling:** Bọc `try...except` và ghi log chi tiết trong endpoint `POST /api/auth/google`, đảm bảo luôn trả về JSON có cấu trúc.
- **Windows IPv6 Network Latency:** Chuyển đổi BASE_URL trong các bộ test tích hợp sang `127.0.0.1:5050` để loại bỏ 100% độ trễ phân giải IPv6 trên Windows.

### Added
- Thêm Soft Sakura Footer hiển thị thông tin bản quyền, công nghệ nền tảng và huy hiệu phiên bản `v1.0.3`.
- Bổ sung trường `version` trong endpoint `GET /api/health` và `GET /api/auth/config`.
- Đồng bộ hiển thị phiên bản động trên giao diện PWA client qua `static/js/auth.js`.
- Bổ sung `CHANGELOG.md` vào quy chuẩn tài liệu SSoT trong `AGENTS.md`.

---

## [1.0.2] - 2026-10-09
### Added
- **Google Identity Services (GIS):** Tích hợp đăng nhập Google One Tap & Google Sign-In button container trên giao diện PWA (`static/js/auth.js`).
- **Google OAuth Backend Verification:** Thư viện `google-auth` xác thực Google ID Token an toàn (`app/auth.py`).
- **Hybrid Dev Auth Switcher:** Hỗ trợ chuyển đổi nhanh 1-click giữa các tài khoản Mock Dev (`Aria Tanaka`, `Kenji Sato`) và Google Account thực tế.
- **Bảo mật phiên đăng nhập:** Quản lý phiên làm việc qua JWT Bearer Token và HttpOnly Cookie `kokoro_session` với thời hạn 30 ngày.
- **Cô lập dữ liệu tuyệt đối (Data Isolation):** Toàn bộ truy vấn nhật ký, upload, sửa ghim, xóa bài viết được gắn chặt với `user_id` của tài khoản hiện tại.
- **UI Header nâng cấp:** Profile Pill tròn, Dropdown chuyển tài khoản mượt mà, nút Đăng xuất và Welcome Login Modal kính mờ Soft Sakura.
- **Bộ test bảo mật tự động:** Tạo `tests/test_auth_isolation.py` kiểm thử 10 bước độc lập, đạt 100% PASS.

---

## [1.0.1] - 2026-10-09
### Added
- **Mô-đun Media Processing Pillow (`app/services/media_service.py`):** Nén và chuyển đổi ảnh sang định dạng `.webp` chất lượng cao (quality 82%), tự động co tỷ lệ (max 1600px) và sinh thumbnail (max 400px).
- **PostgreSQL 18 REST API (`app/routes/entry_routes.py`):**
  - `GET /api/entries`: Lọc đa năng theo Mood, Tag, Tháng, Từ khóa tìm kiếm.
  - `POST /api/entries`: Nhận `multipart/form-data` kèm nhiều ảnh thật, lưu trọn vẹn trong PostgreSQL transaction.
  - `DELETE /api/entries/{id}`: Xóa nhật ký và dọn dẹp file ảnh WebP trên ổ đĩa.
  - `PATCH /api/entries/{id}/pin`: Bật/tắt trạng thái ghim bài viết lên đầu trang.
  - `GET /api/stats/summary`: Tính toán số liệu thống kê thực tế từ CSDL PostgreSQL.
- **Nginx Reverse Proxy Subpath Support:** Thiết kế `static/js/api.js` với `API_BASE` tự động thích ứng với cả cổng 5050 lẫn sub-path `/kokoro/`.
- **Bộ test tích hợp API & Media:** Tạo `tests/test_api_upload.py` kiểm thử nén WebP và lưu CSDL đạt 100% PASS.

---

## [1.0.0] - 2026-10-09
### Added
- Khởi tạo kiến trúc PWA Fullstack cho **Kokoro (心)**: Backend Starlette + Uvicorn (Port 5050), CSDL PostgreSQL 18.
- Xây dựng hệ thống Design Tokens CSS Soft Sakura (`tokens.css`, `glass.css`, `layout.css`): Tông màu hồng phấn dịu nhẹ, phong cách chữa lành Á Đông (Light Frosted Glassmorphism).
- Giao diện Adaptive Responsive hỗ trợ toàn diện Mobile (Bottom Nav, Touch Gestures), Tablet và Desktop (3-column layout).
- Các thành phần giao diện PWA:
  - Header với Logo hoa anh đào Sakura, Profile Pill và Nút cài đặt PWA.
  - Timeline Feed với các thẻ nhật ký ngọc trai hồng và photo grid mosaic.
  - Mini Calendar View đánh dấu ngày có nhật ký.
  - Modal soạn thảo trên Desktop và Bottom Sheet cảm ứng trên Mobile kèm kéo thả ảnh.
  - Fullscreen Photo Lightbox hỗ trợ phím Escape.
- Cấu hình PWA Manifest (`manifest.webmanifest`) và Service Worker (`sw.js`).
- Khởi tạo schema CSDL `kokoro_db` với 5 bảng: `users`, `entries`, `entry_photos`, `tags`, `entry_tags`.
