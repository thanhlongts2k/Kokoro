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

### 🔹 Giai đoạn 7.5: Tái Cấu Trúc Kiến Trúc & Hệ Thống Multi-View Router (Architectural Refactor & Design System)
- [x] Hệ thống Component-Driven Design System tập trung (`static/css/components.css`):
  - [x] Quy chuẩn hóa các controls cốt lõi: `.c-btn`, `.c-card`, `.c-chip`, `.c-input`, `.c-modal`, `.c-sheet`, `.c-view`.
  - [x] 100% sử dụng CSS Tokens từ `tokens.css` (zero hardcoded static colors `#fff`, `#000`).
  - [x] Dọn dẹp module CSS: giải phóng `layout.css`, loại bỏ CSS trùng lặp.
- [x] Hệ thống Điều hướng Multi-View Router cho PWA (Single Page App View Switcher):
  - [x] **View 1 (`#view-timeline`)**: Nhật ký feed mặc định, thanh tìm kiếm live, danh sách bài viết.
  - [x] **View 2 (`#view-calendar`)**: Lịch tháng toàn màn hình trực quan với Mood Dots, bộ chuyển tháng mượt mà, danh sách bài viết theo ngày được chọn.
  - [x] **Nút trung tâm (`+ Viết bài`)**: Nút hành động chính tại Bottom Nav mở Editor Modal/Bottom-Sheet mà không làm gián đoạn view.
  - [x] **View 3 (`#view-memories`)**: Thư viện ảnh dạng lưới (Photo Gallery Grid) gom tất cả ảnh nhật ký, tích hợp bộ lọc theo tâm trạng và xem phóng to qua Lightbox.
  - [x] **View 4 (`#view-profile`)**: Trang cá nhân hiển thị Avatar, Email, Thẻ thống kê Streak Days, Tổng bài viết, Tỷ lệ mood, Quản lý khóa PIN 4 số, Chế độ ban đêm, Sao lưu/Khôi phục JSON, Cài đặt PWA, Đăng xuất.
- [x] Đồng bộ Responsive Desktop & Mobile:
  - [x] Desktop (>1024px): Bố cục Dashboard 3 cột thông minh và thanh chuyển đổi Desktop View Switcher Tabs.
  - [x] Mobile (<768px): Ẩn Desktop Tabs và nút FAB nổi thừa, điều hướng mượt mà qua Bottom Navigation Bar 5 nút (4 view + 1 nút viết bài trung tâm).
- [x] Kiểm thử thị giác tự động qua Playwright: Chụp và nghiệm thu đầy đủ 8 ảnh chụp Mobile (Light & Dark) và Desktop Calendar View, đảm bảo `scrollWidth <= innerWidth` 100%.

### 🔹 Giai đoạn 7.6: Bản Vá Hotfix PWA Cache-Busting & Lightbox Cảm Ứng (v1.4.1 Release)
- [x] Nâng cấp PWA Service Worker Cache-Busting:
  - [x] Bump `CACHE_NAME` lên `kokoro-v1.4.1` trong `static/sw.js`.
  - [x] Tự động xóa sạch toàn bộ cache cũ khi `activate` (`self.skipWaiting()` + `self.clients.claim()`).
  - [x] Đồng bộ query parameter `?v=1.4.1` trên toàn bộ thẻ script và stylesheet trong `static/index.html`.
  - [x] Bổ sung `reg.update()` trong `static/js/pwa.js` để tự động kiểm tra bản cập nhật mới ngay khi mở trang.
- [x] Khắc phục triệt để tương tác Lightbox Zoom & Pan (`static/js/lightbox.js`, CSS):
  - [x] Gắn thuộc tính CSS `touch-action: none !important; user-select: none !important; transition: transform 0.1s ease-out;` cho `#lightbox-img`.
  - [x] Đăng ký sự kiện Touch chuẩn Mobile với `{ passive: false }` và gọi `e.preventDefault()` khi Pinch Zoom 2 ngón hoặc Pan kéo ảnh khi đang zoom.
  - [x] Cụm nút điều khiển nổi `#lightbox-controls-bar` đạt `z-index: 10000 !important;` luôn hiển thị trên cùng.
  - [x] Hỗ trợ các nấc zoom theo bậc: `[+]` (1.5x -> 2.0x -> 2.5x -> 3.0x -> 3.5x), `[-]` (thu nhỏ theo bậc), `[↺]` (reset về 1.0x tâm giữa).
  - [x] Đồng bộ phiên bản ứng dụng toàn diện lên `v1.4.1` trên Footer, `app/config.py`, và `README.md`.

### 🔹 Giai đoạn 7.7: Tái Cấu Trúc Toàn Diện Media Lifecycle & Vá Tràn Ngang Mobile (v1.5.0 Go-Live Readiness)
- [x] Hoàn thiện nghiệp vụ hình ảnh & vòng đời ảnh (Media Lifecycle):
  - [x] Tái cấu trúc Data Model trong Editor: `existingPhotos`, `deletedPhotoIds`, `selectedFiles`.
  - [x] Chuẩn hóa `.preview-thumb-box` khung vuông 1:1, ảnh `object-fit: cover`.
  - [x] Nút xóa nổi bật 28x28px (`.preview-remove-btn`) trên góc tất cả ảnh thumbnail (cũ và mới).
  - [x] Backend xóa nguyên tử DB `entry_photos` và xóa file vật lý `.webp` / `_thumb.webp` trong `uploads/` trên ổ đĩa.
- [x] Triệt tiêu hoàn toàn lỗi tràn ngang Modal / Bottom Sheet trên Mobile (375x812 & 390x844):
  - [x] Thay thế toàn bộ `100vw` bằng `width: 100% !important; max-width: 100% !important; box-sizing: border-box !important;`.
  - [x] Khóa cứng `overflow-x: hidden !important; touch-action: pan-y !important; min-width: 0 !important;` trên `.modal-overlay`, `.editor-dialog`, `.editor-body`.
  - [x] Playwright E2E assert `scrollWidth <= innerWidth` 100% PASS.
- [x] Vá lỗ hổng xác thực & cô lập dữ liệu đa tài khoản:
  - [x] Lưu `user_id` vào IndexedDB offline queue; chỉ đồng bộ bài viết của current user.
  - [x] `onUserChanged` làm mới cả 4 views và xóa trắng Editor form.
  - [x] Khi bật khóa PIN, chỉ nạp dữ liệu bài viết sau khi nhập đúng mã PIN (`onPinUnlocked`).
- [x] Xử lý ma trận Edge Cases:
  - [x] Cho phép đăng bài viết chỉ có ảnh (content rỗng).
  - [x] Cho phép xóa sạch toàn bộ ảnh cũ chuyển thành bài thuần văn bản.
  - [x] Tự động xóa tags mồ côi trong PostgreSQL.
- [x] Bộ test hồi quy và test mới pass 100% (`test_v15_media_lifecycle.py`, `verify_mobile_editor_overflow.py`).

### 🔹 Giai đoạn 7.8: Sửa Lỗi WebKit iOS PWA, Quản Lý Thẻ & Tối Ưu Preview (v1.5.2 & v1.5.3 Release)
- [x] Bypass triệt để Service Worker với toàn bộ API (`/api/`) ngăn Safari WebKit nuốt body stream multipart khi tạo/sửa bài.
- [x] Tích hợp `pillow-heif` giải mã ảnh chụp iPhone `.heic`/`.heif` sang `.webp` chuẩn hóa.
- [x] Khóa cứng `#lightbox-controls-bar` triệt tiêu lỗi thanh công cụ phóng to ảnh nổi lơ lửng khi modal đóng.
- [x] Nâng cấp kích thước và tỷ lệ lưới xem trước ảnh thumbnail trong Editor (`minmax(96px, 1fr)`).
- [x] Xây dựng endpoint `GET /api/tags` và đồng bộ số lượng thẻ chủ đề, tâm trạng ngoài trang chủ.

### 🔹 Giai đoạn 7.9: Tái Cấu Trúc Bẻ Khóa God Component, Datetime Picker & Capsule Mood Chips (v1.5.4 Release)
- [x] Tái cấu trúc chip cảm xúc Mobile thành thanh kẹo con nhộng (`.mood-chip-pill`, `.mood-count-badge`), fix triệt để lỗi đếm số 0 bằng hàm SSoT `updateMoodCountBadges(stats)`.
- [x] Xây dựng module Custom Date & Time Picker độc lập (`static/js/datetime-picker.js`), mini-calendar + time spinners, trigger pill `📅 DD/MM/YYYY, HH:MM`, backend hỗ trợ `created_at` tùy chỉnh.
- [x] Bẻ khóa God Component (Decoupling Architecture):
  - [x] Tách `static/js/toast.js` (`window.KokoroToast`) quản lý deduplication và giới hạn tối đa 2 toast.
  - [x] Tách `static/js/tag-manager.js` (`window.KokoroTagManager`) quản lý quick chips và popular tags widget.
  - [x] Tinh gọn `editor.js` và `app.js` theo Clean Architecture.
- [x] Cập nhật phiên bản hệ thống lên `v1.5.4` (`app/config.py`, `static/sw.js`, `static/index.html`).
- [x] Bộ kiểm thử tự động đạt 100% PASS.

### 🔹 Giai đoạn 7.10: Tái Cấu Trúc Toàn Diện Giao Diện, Smooth Time Wheel, State Isolation & Tag Management (v1.5.5 Release)
- [x] Khóa cứng `#lightbox-controls-bar` tại DOM inline style và JS hard-lock `lightbox.js`, tiêu diệt 100% bug thanh điều khiển nổi lơ lửng.
- [x] Khắc phục méo/dẹp ảnh dọc chụp màn hình điện thoại (9:16, 9:20) trên Timeline Feed bằng Adaptive Container (`aspect-ratio: auto; max-height: 480px; object-fit: contain;`).
- [x] Nâng cấp bộ chọn giờ Smooth Time Picker cho Mobile: Soft Sakura Time Wheel Card + `<input type="time">` kích hoạt Native iOS/Android drum wheel spinner với haptics và quán tính cuộn.
- [x] Tái cấu trúc Kho Kỷ Niệm (`#view-memories`): Cô lập dải filter của Timeline vào trong `#view-timeline`, thiết kế lại thanh filter Kho Kỷ niệm thành capsule pills `.memories-mood-scroll`, bổ sung bộ lọc Hashtag cuộn ngang `#memories-tag-chips`.
- [x] Cô lập trạng thái (State Isolation): Duy trì snapshot `allEntries` bất biến, tách biệt `timelineState` và `memoriesState`, chống rò rỉ bộ lọc giữa các màn hình.
- [x] Sửa lỗi sticky hover/focus chip hashtag trên mobile (`chip.blur()`, `@media (hover: hover)`, `:active` scale).
- [x] Bổ sung phân hệ "Quản lý Danh mục & Thẻ chủ đề" trong Profile (`#category-tag-manager-modal`) với 2 tab (Tâm trạng & Thẻ), đổi tên thẻ, merge tự động, xóa thẻ và dọn dẹp thẻ mồ côi 0 bài.
- [x] Bổ sung Backend REST API: `PUT /api/tags/{id}`, `DELETE /api/tags/{id}`, `DELETE /api/tags/cleanup-orphans`.
- [x] Nâng phiên bản hệ thống lên `v1.5.5` và kiểm thử tự động toàn diện đạt 100% PASS.

### 🔹 Giai đoạn 7.11: Hotfix v1.5.6 — Vá Dứt Điểm 5 Bug Audit Độc Lập (P0 - P3)
- [x] **[P0 - CRITICAL SECURITY] Vá triệt để lỗ hổng Stored XSS**:
  - [x] Xây dựng hàm `escapeHtml(unsafe)` trong `static/js/api.js`, export qua `window.escapeHtml` và `window.KokoroAPI.escapeHtml`.
  - [x] Bọc mã hóa dữ liệu người dùng render qua innerHTML trong `app.js` (`buildEntryCardHtml`, Lịch, Kỷ niệm), `tag-manager.js`, `auth.js`, và `editor.js`.
- [x] **[P1 - HIGH INTERACTION] Sửa lỗi modal Quản lý Danh mục bị kẹt pointer-events**:
  - [x] Bổ sung `modalEl.classList.add('active')` và `lockBodyScroll(true)` trong `openManagerModal`.
  - [x] Bổ sung `modalEl.classList.remove('active')` và `lockBodyScroll(false)` trong `closeManagerModal`.
- [x] **[P2 - SECURITY CONFIG] Bổ sung cờ `Secure=True` cho Session Cookie**:
  - [x] Bổ sung `secure=True` cho `response.set_cookie(...)` tại `mock_login` và `google_login` trong `app/routes/auth_routes.py`.
- [x] **[P2 - USER EXPERIENCE] Đồng bộ HTML5 History API cho điều hướng Tabs**:
  - [x] Tích hợp `history.pushState({ view: viewName }, '', '#' + viewName)` vào `switchView`.
  - [x] Lắng nghe sự kiện toàn cục `popstate` và khôi phục hash router ban đầu.
- [x] **[P3 - MOBILE ACCESSIBILITY] Chuẩn hóa kích thước vùng chạm Touch Targets >= 44px**:
  - [x] Cấu hình `min-width: 40px; min-height: 40px;` kèm pseudo-element `::before` (`inset: -4px`) cho các icon tròn.
  - [x] Cấu hình `.mood-option-chip` đạt `min-height: 44px; padding: 0 16px;`.
  - [x] Đảm bảo nút điều hướng tháng trên lịch đạt kích thước chuẩn.
- [x] **Nâng cấp phiên bản hệ thống lên v1.5.6**:
  - [x] Cập nhật `app/config.py`, `static/sw.js`, và `static/index.html`.

### 🔹 Giai đoạn 8: Cảm Hứng & Chia Sẻ (v1.6.0 - Planned)
- [ ] Gợi ý câu hỏi suy ngẫm mỗi ngày (Daily Zen Prompt):
  - [ ] Bộ danh mục 60+ câu hỏi chánh niệm, triết lý sống Nhật Bản offline trong `static/js/daily-prompt.js`.
  - [ ] Thuật toán chọn câu hỏi theo ngày (deterministic seed hash theo `YYYY-MM-DD`), offline 100%, bảo mật riêng tư tuyệt đối, tự đổi câu hỏi vào 00:00.
  - [ ] Giao diện thẻ kính mờ Soft Sakura "Góc Suy Ngẫm Hôm Nay ✨" ở đầu Timeline Feed, hỗ trợ thu gọn/đóng trong ngày.
  - [ ] Tương tác 1-click: Nhấp vào prompt tự động mở Editor Modal và chèn câu hỏi làm gợi ý viết bài.
  - [ ] Nút "Đổi câu khác 🎲" xoay vòng câu hỏi ngẫu nhiên trong ngày.
- [ ] Xuất bài viết thành ảnh thẻ kỷ niệm (Aesthetic Journal Card Export):
  - [ ] Pure HTML5 Canvas 2D Engine (`static/js/card-export.js`) không dùng thư viện ngoài (0KB external dependency), 100% offline-first.
  - [ ] Render ảnh thẻ độ phân giải cao 2K sắc nét cho thiết bị di động / màn hình Retina.
  - [ ] Hỗ trợ 2 phong cách giao diện: Soft Sakura 🌸 (Hồng phấn thanh nhã) và Night Sakura 🌙 (Tím sương khói huyền bí).
  - [ ] Hỗ trợ 2 tỉ lệ chuẩn mạng xã hội: Thẻ vuông 1:1 (1080x1080) và Story 9:16 (1080x1920).
  - [ ] Bổ sung nút "Lưu ảnh kỷ niệm 📷" trên từng thẻ bài viết ở Timeline Feed.
  - [ ] Modal xem trước tương tác (`#card-export-modal`) cho phép tùy chọn theme, tỉ lệ và bấm 1-click tải ảnh PNG về máy.
- [ ] Nâng cấp Service Worker cache lên `kokoro-v1.5.0` và kiểm thử hồi quy toàn diện.


