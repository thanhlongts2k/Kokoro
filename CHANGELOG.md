# CHANGELOG.md — Nhật Ký Thay Đổi Kokoro (心)

Tất cả các thay đổi đáng chú ý của dự án **Kokoro — Personal Diary & Photo Journal PWA** được ghi nhận chi tiết tại tệp này theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) và tuân thủ [Semantic Versioning (SemVer)](https://semver.org/).

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
