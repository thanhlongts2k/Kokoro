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

### 🔹 Giai đoạn 8: Phân Hệ Quản Lý Danh Mục Cảm Xúc & Thẻ Chủ Đề (v1.6.0 Architecture)
- [x] **Giai đoạn 8.1 (v1.6.0-beta.1) — CSDL & Hệ Thống REST API Backend:**
  - [x] Tạo bảng `categories` và khóa ngoại `entries.category_id REFERENCES categories(id) ON DELETE SET NULL`.
  - [x] Đánh chỉ mục hiệu năng `idx_categories_user`, `idx_entries_user_cat`, `idx_entry_tags_tag_id`.
  - [x] Khởi tạo 5 tâm trạng cốt lõi (Bình yên 🌸, Ấm áp ☕, Chiêm nghiệm 🌙, Biết ơn 🍵, Năng lượng ⚡) làm danh mục mặc định.
  - [x] Xây dựng đầy đủ REST API: `GET /api/categories`, `POST /api/categories`, `PUT /api/categories/{id}`, `DELETE /api/categories/{id}`.
  - [x] Bổ sung API `POST /api/tags` chủ động tạo thẻ mới trước khi viết bài.
  - [x] Cập nhật API bài viết: `GET /api/entries`, `POST /api/entries`, `PUT /api/entries/{id}` hỗ trợ `category_id`.
  - [x] Chuẩn hóa token precedence trong `app/auth.py` và bổ sung phương thức client trong `static/js/api.js`.
  - [x] Viết bộ kiểm thử tích hợp tự động `tests/test_v160_backend_api.py` đạt 100% PASS (7/7 tests).
- [x] **Giai đoạn 8.2 (v1.6.0-beta.2) — Modal Quản Lý Danh Mục & Thẻ Client UI:**
  - [x] Khắc phục triệt để lỗi kéo chéo / xô lệch thanh danh mục trên iOS PWA (`overflow-y: hidden`, `touch-action: pan-x`).
  - [x] Thiết kế lại Modal `#category-tag-manager-modal` với Tab 1 "📁 Danh mục cảm xúc" và Tab 2 "🏷️ Thẻ chủ đề".
  - [x] Bộ chọn Emoji Popover (20 icon tinh tế) và bảng 7 mã màu Pastel chữa lành.
  - [x] Bộ điều khiển `static/js/tag-manager.js` kết nối đầy đủ CRUD API cho cả danh mục và thẻ.
  - [x] Viết bộ kiểm thử giao diện `tests/test_v160_modal_client.py` đạt 100% PASS.
- [x] **Giai đoạn 8.3 (v1.6.0 Release) — Tích Hợp Đồng Bộ Toàn Hệ Thống:**
  - [x] Tích hợp bộ chọn Mood/Danh mục động vào Form Soạn thảo (`static/js/editor.js`).
  - [x] Tích hợp bộ lọc Mood/Danh mục động ngoài Timeline Feed và Kho Kỷ niệm (`static/js/app.js`).
  - [x] Nâng cấp Service Worker cache lên `kokoro-v1.6.0` và kiểm thử hồi quy toàn diện.
  - [x] Viết bộ kiểm thử tích hợp tự động `tests/test_v160_full_integration.py` đạt 100% PASS (13/13 tests toàn hệ thống).

### 🔹 Giai đoạn 9: Bản Phát Hành v1.6.1 — Toàn Vẹn Dữ Liệu Ngoại Tuyến, Sao Lưu JSON & Weather Selector UI
- [x] **Vá Lỗ Hổng Toàn Vẹn Dữ Liệu Ngoại Tuyến IndexedDB (`static/js/api.js`):**
  - [x] Lưu trữ `category_id` chuẩn kiểu số nguyên vào cơ sở dữ liệu ngoại tuyến trong `saveOfflineEntry()`.
  - [x] Phòng chống triệt để bẫy ép kiểu chuỗi `"null"` khi mạng kết nối lại trong `syncOfflineQueue()`, loại trừ lỗi `ValueError` HTTP 500.
- [x] **Nâng Cấp Hệ Thống Sao Lưu & Khôi Phục JSON (`app/routes/entry_routes.py`):**
  - [x] **Xuất Dữ Liệu (`GET /api/entries/export`):** Bổ sung bảng `categories` tùy chỉnh và xuất kèm `category_id`, `category_name`, `category_icon`, `category_color` trong từng bài viết (`export_version = "1.1"`).
  - [x] **Khôi Phục Dữ Liệu (`POST /api/entries/import`):** Tự động nạp và ánh xạ lại `categories` tùy chỉnh với xử lý xung đột `ON CONFLICT (user_id, name)` và cơ chế kiểm tra dự phòng (pre-check query fallback).
  - [x] **Tương Thích Ngược 100% (Backward Compatibility):** Khôi phục trơn tru các tệp sao lưu v1.0 cũ không có trường `category_id` hoặc thiếu bảng `categories`, không bao giờ phát sinh `KeyError`.
  - [x] Bảo toàn mốc thời gian nguyên bản `created_at` và `updated_at` của bài viết khi khôi phục từ tệp sao lưu.
- [x] **Trình Chọn Thời Tiết Trực Quan Trong Editor (`static/index.html`, `static/css/components.css`, `static/js/editor.js`):**
  - [x] Bổ sung thanh chọn thời tiết capsule chips (`#editor-weather-picker-list`) gồm 5 trạng thái thời tiết: Nắng ☀️ (`sunny`), Mưa 🌧️ (`rainy`), Nhiều mây ⛅ (`cloudy`), Gió 🍃 (`windy`), Tuyết ❄️ (`snowy`).
  - [x] Đồng bộ trường thời tiết với vòng đời biên tập: Tự động lưu và khôi phục trong bản nháp (`localStorage`), nạp thời tiết khi chỉnh sửa bài viết cũ, và gửi chính xác lên máy chủ (thay thế giá trị `'sunny'` cố định).
  - [x] Hiển thị biểu tượng thời tiết `.weather-badge-pill` tinh tế trên tiêu đề thẻ bài viết Dòng thời gian (`static/js/app.js`).
- [x] **Xác Thực Tuyệt Đối Cập Nhật Bài Viết (`PUT /api/entries/{id}`):**
  - [x] Đảm bảo câu lệnh SQL UPDATE cập nhật chuẩn xác trường `weather = %s` cùng `category_id` trên mọi nhánh điều kiện.
- [x] **Tự Động Nạp Lại Mã Nguồn Trong Môi Trường Phát Triển (`server.py`):**
  - [x] Kích hoạt tham số `reload=Config.DEBUG` trong `uvicorn.run()` giúp máy chủ tự động nạp lại khi sửa mã nguồn.
- [x] **Nâng Cấp Phiên Bản Ứng Dụng & Cache PWA (`app/config.py`, `static/sw.js`, `static/index.html`):**
  - [x] Tăng phiên bản chính thức lên `v1.6.1` trong `Config.APP_VERSION`.
  - [x] Nâng cấp bộ nhớ đệm Service Worker lên `kokoro-v1.6.1` và cập nhật chuỗi truy vấn tài nguyên `?v=1.6.1`.
- [x] **Bộ Kiểm Thử Tự Động Toàn Diện Cho Tính Toàn Vẹn Dữ Liệu (`tests/test_v161_data_integrity.py`):**
  - [x] Đạt 100% PASS cho toàn bộ các ca kiểm thử tính toàn vẹn dữ liệu và tương thích ngược.

### 🔹 Giai đoạn 10: Bản Phát Hành v1.6.2 — Gợi Ý Suy Ngẫm Chánh Niệm Mỗi Ngày (Daily Zen Prompt)
- [x] **Kho 36 Câu Hỏi Gợi Ý Chánh Niệm (`static/js/zen-prompts.js`):**
  - [x] Kho 36 câu hỏi suy ngẫm chữa lành trải đều trên 4 trụ cột (Grateful 🍵, Reflective 🌙, Serene 🌸, Energetic ⚡).
  - [x] Thuật toán chọn câu hỏi theo seed ngày cục bộ client (`getLocalDateString()`), chống lệch múi giờ UTC, đổi mới câu hỏi lúc 00:00.
  - [x] Xúc xắc ngẫu nhiên 🎲 (`getRandomPrompt()`) kèm hiệu ứng xoay `@keyframes spinDice` và lưu trạng thái vào `localStorage`.
  - [x] Tùy chọn đóng/thu gọn thẻ hôm nay với bộ nhớ `kokoro_zen_dismissed_date`.
- [x] **Thẻ Hiển Thị Gợi Ý Ngoài Timeline (`static/index.html`, `static/css/components.css`, `static/js/app.js`):**
  - [x] Thẻ kính mờ `#daily-zen-card` đặt đầu Timeline Feed với icon anh đào, câu hỏi, nút xúc xắc và nút đóng/thu gọn.
  - [x] Nút "Viết theo gợi ý này ✨" mở Editor kèm câu hỏi và tâm trạng đề xuất.
- [x] **Tích Hợp An Toàn Bản Nháp Vào Trình Soạn Thảo (`static/js/editor.js`):**
  - [x] Hiển thị hint pill `#editor-zen-prompt-hint` trong modal/sheet soạn thảo.
  - [x] **Draft Safety:** Nếu đã có nội dung trong ô soạn thảo, chèn trích dẫn `> 🌸 "${promptText}"\n\n` lên đầu và đặt con trỏ chuột (`setSelectionRange`) ngay sau trích dẫn thay vì ghi đè.
  - [x] Tự động chọn sẵn tâm trạng đề xuất (`suggestedMood`).
- [x] **Nâng Cấp Service Worker & Cache PWA (`static/sw.js`, `app/config.py`, `static/index.html`):**
  - [x] Cập nhật `Config.APP_VERSION = "v1.6.2"`.
  - [x] Nâng cấp bộ nhớ đệm Service Worker lên `kokoro-v1.6.2` và thêm `zen-prompts.js?v=1.6.2` (Offline-First 100%).
  - [x] Đảm bảo thẻ script `zen-prompts.js` được nạp trước `editor.js` và `app.js` trong `index.html`.
- [x] **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_v162_zen_prompts.py`):**
  - [x] 100% PASS bộ kiểm thử tính nhất quán của seed ngày cục bộ, 36 câu hỏi, draft safety và hợp đồng UI.

### 🔹 Giai đoạn 11: Bản Phát Hành v1.6.3 — Xuất Thẻ Ảnh Kỷ Niệm (Daily Card Export)
- [x] **Công Cụ Render Canvas Chuẩn 1080p (`static/js/card-export.js`):**
  - [x] Khóa cứng kích thước bộ đệm vật lý 1080p (Vuông 1080x1080 & Story 1080x1920), triệt tiêu bẫy quá tải bộ nhớ và crash Safari trên iOS.
  - [x] Cổng chặn tải font async `document.fonts.ready` đảm bảo 100% font chữ tiếng Việt và emoji hiển thị chuẩn xác.
  - [x] Thuật toán bẻ dòng thông minh `wrapAndFitText()` bảo toàn dấu ngắt đoạn của người dùng, tự động cắt tỉa an toàn kèm dấu ba chấm "..." tránh tràn đè nội dung.
  - [x] Bố cục thích ứng (Adaptive Layout): Chế độ Thuần chữ dạng Zen Quote nghệ thuật và Chế độ Có ảnh kèm khung bo góc & badge "+X ảnh".
  - [x] Tiền tạo sẵn Blob/File (`currentExportFile`) để gọi Web Share API tức thì trong User Gesture, phòng chống lỗi `NotAllowedError` trên iOS Safari.
  - [x] Dọn dẹp bộ nhớ nghiêm ngặt qua `URL.revokeObjectURL()` và reset kích thước canvas khi đóng modal.
- [x] **Giao Diện Modal Xuất Thẻ & Nút Thao Tác Timeline (`static/index.html`, `static/css/components.css`, `static/js/app.js`):**
  - [x] Thêm nút icon `[ 🖼️ Xuất ảnh ]` trên thanh công cụ mỗi thẻ bài viết Dòng thời gian.
  - [x] Hộp thoại `#card-export-modal` phong cách Soft Sakura Glass với bộ gạt chọn tỷ lệ [ Vuông 1:1 ] / [ Story 9:16 ], preview canvas responsive mượt mà và nút Tải về / Chia sẻ.
- [x] **Nâng Cấp Service Worker & Cache PWA (`static/sw.js`, `app/config.py`, `static/index.html`):**
  - [x] Tăng phiên bản chính thức lên `v1.6.3` trong `Config.APP_VERSION`.
  - [x] Nâng cấp bộ nhớ đệm Service Worker lên `kokoro-v1.6.3` và thêm `card-export.js?v=1.6.3` vào danh sách pre-cache.
### 🔹 Giai đoạn 12: Bản Phát Hành v1.6.4 — Dọn Dẹp Ảnh Mồ Côi, Caching CDN & Phân Trang Lũy Tiến (Sprint 2 Gap Closure)
- [x] **Động Cơ Dọn Dẹp Ảnh Mồ Côi Bảo Vệ Dữ Liệu (`app/services/media_service.py` & `app/routes/entry_routes.py`):**
  - [x] Phương thức `MediaService.scan_and_cleanup_orphans(grace_period_hours=2.0)` quét đối soát đĩa vật lý và bảng `entry_photos`.
  - [x] **Chống bẫy đường dẫn Windows:** Chuẩn hóa và so sánh theo tên file thuần túy (`os.path.basename(path.replace('\\', '/'))`), loại bỏ nguy cơ xóa nhầm ảnh do lệch dấu gạch chéo giữa OS và DB.
  - [x] **Grace Period 2 giờ:** Bỏ qua các tệp unreferenced mới tạo trong vòng 2 giờ (`mtime > cutoff_time`), bảo vệ an toàn các ảnh bản nháp đang soạn thảo.
  - [x] Endpoint bảo trì an toàn `POST /api/maintenance/cleanup-orphaned-media` (yêu cầu đăng nhập, trả về số file và MB giải phóng).
- [x] **Tối Ưu Service Worker & Cache CDN Ngoại Tuyến (`static/sw.js`, `app/config.py`, `static/index.html`):**
  - [x] Nâng cấp `Config.APP_VERSION = "v1.6.4"` và bộ nhớ đệm `kokoro-v1.6.4`.
  - [x] Cập nhật whitelist CDN cho phép cache ngoại tuyến Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) và Bootstrap Icons (`cdn.jsdelivr.net`).
  - [x] Hỗ trợ runtime caching cho response `opaque` (status 0) và `cors`, cache runtime ảnh thumbnail bài viết (`/uploads/thumbnails/`).
- [x] **Phân Trang Lũy Tiến & Trải Nghiệm Cuộn Mượt Mà Trên Mobile (`static/js/app.js` & `static/css/components.css`):**
  - [x] Thiết lập `timelinePagination` (15 bài / trang) và nút Soft Sakura `[ 🍃 Xem thêm bài viết cũ hơn... ]` ở cuối feed.
  - [x] Giữ scroll offset ổn định tuyệt đối trên mobile bằng kỹ thuật append `DocumentFragment` trực tiếp, không re-render các card cũ.
  - [x] Reset `visibleLimit = 15` khi thay đổi bất kỳ bộ lọc nào, bảo toàn 100% snapshot dữ liệu cho Mini Calendar và Memories Stats.
- [x] **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_sprint2_gap_closure.py`):**
  - [x] 100% PASS trên toàn bộ test runner của dự án Kokoro.

### 🔹 Giai đoạn 13: Chuẩn Hóa Kiến Trúc Clean Architecture & Strict Typing (Phased Refactoring: Giai đoạn 1 & 2)
- [x] **Giai đoạn 1: Thiết Lập Toàn Bộ Contracts & Schemas (`app/schemas/`):**
  - [x] `app/schemas/category.py`: `CategoryDTO`, `CategoryCreateDTO`, `CategoryUpdateDTO`.
  - [x] `app/schemas/tag.py`: `TagDTO`, `TagCreateDTO`, `TagUpdateDTO`.
  - [x] `app/schemas/stats.py`: `StatsSummaryDTO`, `MoodCountDTO`.
  - [x] `app/schemas/user.py`: `UserDTO`, `UserSessionDTO`.
  - [x] `app/schemas/entry.py`: `EntryDTO`, `EntryCreateDTO`, `EntryPhotoDTO`.
  - [x] `app/schemas/maintenance.py`: `CleanupStatsDTO`, `MaintenanceResponseDTO`.
  - [x] 100% sử dụng typed dataclass, loại bỏ hoàn toàn untyped dictionaries thô.
- [x] **Giai đoạn 2: Bóc Tách Các Phân Hệ Độc Lập (Category, Tag, Stats, Maintenance):**
  - [x] **Phân hệ Danh mục (Category):** Bóc tách `app/repositories/category_repository.py` & `app/routes/category_routes.py`.
  - [x] **Phân hệ Thẻ (Tag):** Bóc tách `app/repositories/tag_repository.py` & `app/routes/tag_routes.py`.
  - [x] **Phân hệ Thống kê (Stats):** Bóc tách `app/repositories/stats_repository.py` & `app/routes/stats_routes.py`.
  - [x] **Phân hệ Bảo trì (Maintenance):** Bóc tách `app/repositories/photo_repository.py` & `app/routes/maintenance_routes.py`.
  - [x] **Giải phóng God-file:** Cắt giảm 503 dòng code rườm rà và raw SQL trực tiếp khỏi `entry_routes.py` (giảm từ 1.568 dòng xuống 1.065 dòng).
  - [x] Đăng ký các router module vào `server.py` và duy trì 100% PASS trên bộ kiểm thử tự động `tests/test_modular_schemas_and_repositories.py`.

### 🔹 Giai đoạn 14: Chuẩn Hóa Kiến Trúc Clean Architecture (Giai đoạn 3 — Phân Hệ User & Entry)
- [x] **Khôi Phục & Đồng Bộ Test Runner Suite Toàn Hệ Thống:**
  - [x] Khôi phục toàn bộ 10 file test in-memory vào thư mục `tests/` gốc (`test_compliance_p0.py`, `test_v156_hotfix.py`, `test_v160_*`, `test_v161_*`, `test_v162_*`, `test_v163_*`, `test_sprint2_gap_closure.py`, `test_modular_schemas_and_repositories.py`).
  - [x] Đồng bộ kiểm thử phiên bản `v1.6.4` và cơ chế dọn dẹp isolation trong `setUp()`.
  - [x] Test runner discovery `python -m unittest discover -s tests` chạy đầy đủ và đạt **57/57 tests PASS 100%**.
- [x] **Phân Hệ Người Dùng & Xác Thực (User & Auth Module):**
  - [x] Tạo `app/repositories/user_repository.py` đóng gói toàn bộ raw SQL truy vấn người dùng (`get_by_id`, `get_first_user`, `list_all_users`, `upsert_user`).
  - [x] Tái cấu trúc `app/auth.py` và `app/routes/auth_routes.py` qua `UserRepository` & `UserDTO`, triệt tiêu 100% raw SQL trong controller.
- [x] **Phân Hệ Nhật Ký Lõi (Entry Module):**
  - [x] Bổ sung `EntryFilterDTO`, `EntryUpdateDTO` trong `app/schemas/entry.py`.
  - [x] Tạo `app/repositories/entry_repository.py` (~720 dòng) đóng gói toàn bộ raw SQL: lọc bài viết, chi tiết, thêm mới, sửa đổi kèm đồng bộ ảnh & tag, xóa, toggle pin, xuất/nhập JSON backup.
  - [x] Tái cấu trúc `app/routes/entry_routes.py` thành Pure Presentation Controller: chỉ xử lý HTTP, validate DTO, gọi EntryRepository & MediaService.
  - [x] **Cắt giảm triệt để dung lượng:** Thu gọn `entry_routes.py` từ 1.568 dòng ban đầu (1.065 dòng sau Phase 2) xuống còn **291 dòng code** (đạt hợp đồng < 300 dòng code).

### 🔹 Giai đoạn 15: Bản Phát Hành v1.6.5 — Memory Studio Đa Phong Cách & Dọn Dẹp Nợ Kỹ Thuật (Sprint Release)
- [x] **Memory Studio Đa Phong Cách (`static/js/card-export.js`, `static/index.html`, `static/css/components.css`):**
  - [x] Tích hợp thanh cuộn Theme Switcher Pill Buttons (5 themes: Sakura, Polaroid, Scrapbook, Music, Editorial).
  - [x] Scrapbook Craftsmanship: Nền dot-grid bullet journal #faf6ed, ảnh Polaroid nghiêng -2.8° kèm drop shadow mềm, Washi Tape họa tiết caro pastel, dấu bưu điện kép tròn AIR MAIL.
  - [x] Music Player Widget: Mini playback bar, sóng âm, tính toán toạ độ Y động chống đè văn bản bài viết.
  - [x] Chuẩn hóa tên file xuất ảnh: `kokoro_{theme}_{layout}_{yyyyMMdd_HHmmss}.jpg`.
- [x] **Vá Lỗ Hổng Dữ Liệu Ngoại Tuyến & Error Handling (`static/js/api.js`, `app/routes/maintenance_routes.py`):**
  - [x] Sửa `syncOfflineQueue()` không xóa bài khỏi IndexedDB khi gặp mã 401/403.
  - [x] Triệt tiêu 100% khối nuốt lỗi (empty catch blocks) trên cả Backend (`maintenance_routes.py`) và Frontend (`api.js`, `app.js`, `card-export.js`, `zen-prompts.js`).
- [x] **Chuẩn Hóa Layer Isolation (`server.py`, `app/database.py`):**
  - [x] Đóng gói hàm `check_db_connection()` trong `app/database.py`, loại bỏ hoàn toàn cursor/raw SQL khỏi `server.py`.
- [x] **Dọn Dẹp Dead Code & Workspace SSoT:**
  - [x] Xóa bỏ tệp `mock-data.js` và toàn bộ tham chiếu trong `index.html` và `sw.js`.
  - [x] Dọn dẹp tài liệu báo cáo và các file probe/log tạm thời trong `EVD/`.
- [x] **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_v165_release.py`):**
  - [x] Đạt **74/74 tests PASS 100%** trên toàn bộ hệ thống test runner.

### 🔹 Giai đoạn 16: Bản Phát Hành v1.7.0 — Đại Phẫu Thuật God-File `app.js`, Frontend Modularization & Khép Lại Khoảng Mù Kiểm Thử
- [x] **Tối Ưu CSDL & Secret Hygiene (Sprint 1):**
  - [x] Database Composite Indexing (`app/database.py`): `CREATE INDEX IF NOT EXISTS idx_entries_pinned_date ON entries(user_id, is_pinned DESC, entry_date DESC, created_at DESC);`
  - [x] Secret Hygiene (`app/config.py`): Loại bỏ fallback im lặng, cảnh báo môi trường và chặn khởi động ở production nếu thiếu `SECRET_KEY`.
- [x] **Tập Trung Hóa Hằng Số & Triệt Tiêu Magic Numbers (Sprint 2):**
  - [x] Tạo `static/js/constants.js`: Định nghĩa `KokoroConstants` (PAGINATION, TIMEOUTS, STORAGE_KEYS, MOODS, VIEWS, EXPORT_THEMES).
  - [x] Nạp `constants.js` vào `index.html` và danh sách cache `sw.js`.
  - [x] Tái cấu trúc `editor.js` và `app.js` loại bỏ số/chuỗi ma thuật thô.
- [x] **Đại Phẫu Thuật God-File `app.js` (Sprint 3):**
  - [x] Bóc tách 4 phân hệ hiển thị chuyên biệt:
    - `static/js/timeline-feed.js`: Timeline feed cards, progressive pagination, card action delegates.
    - `static/js/calendar-view.js`: Monthly calendar grid, mini calendar widget, `isSameDay`.
    - `static/js/memories-view.js`: Memories album gallery, hashtag chips, mood filter chips.
    - `static/js/profile-stats.js`: Profile header & metrics, mood distribution breakdown, `calculateStreak`.
  - [x] Rút gọn `app.js` từ 2.025 dòng xuống **386 dòng** (đạt xuất sắc hợp đồng < 400 dòng), chỉ giữ vai trò Bootstrap, View Routing và Event Coordinator.
- [x] **Khép Lại Khoảng Mù Kiểm Thử & Phát Hành v1.7.0 (Sprint 4):**
  - [x] Tạo bộ kiểm thử tự động `tests/test_v170_frontend_contracts.py` bao quát 7 hợp đồng frontend, CSDL và bảo mật.
  - [x] Nâng cấp phiên bản đồng bộ lên `v1.7.0` (`config.py`, `index.html`, `sw.js`).
  - [x] Toàn bộ test runner đạt **81/81 tests PASS 100%**.
- [x] **Bản Phát Hành Hotfix v1.7.1 (Navigation, Data Integrity Audit & API Contract Sync):**
  - [x] Kiểm toán toàn vẹn CSDL tài khoản `thanhlongts2k@gmail.com` (User 38): Khẳng định 100% dữ liệu gốc (6 bài viết, 7 ảnh WebP, 4 tags, 5 danh mục) tồn tại nguyên vẹn trong PostgreSQL, không bị mất mát hay xóa nhầm.
  - [x] Khắc phục lỗi ánh xạ hợp đồng REST API trong `static/js/app.js`: Chuyển từ `res.data` sang `res.entries || res.data` và `res.categories || res.data`, triệt tiêu lỗi gán `entries = []` khi nạp dữ liệu.
  - [x] Bổ sung hàm vòng đời `onUserChanged(user)` đồng bộ nạp lại dữ liệu người dùng khi login/switch user.
  - [x] Khắc phục lệch bộ chọn sự kiện điều hướng (`[data-switch-view]`, `.bottom-nav-item[data-tab]`, `[data-view-target]`) trong `static/js/app.js`.
  - [x] Đồng bộ cơ chế ẩn hiện phân vùng view container `.c-view, .app-view` trong `switchView()`.
  - [x] Kích hoạt sự kiện click mở menu `#user-profile-pill` và điều hướng Profile View từ dropdown menu.
  - [x] Nâng cấp `APP_VERSION = "v1.7.1"`, bộ nhớ đệm `CACHE_NAME = 'kokoro-v1.7.1'`, query string `?v=1.7.1` và badge `v1.7.1`.
  - [x] Kiểm thử tự động E2E bằng Playwright trên Microsoft Edge xác nhận chuyển đổi trơn tru 4 view và dropdown menu.
  - [x] Toàn bộ 81/81 regression tests PASS 100%.

### 🔹 Giai đoạn 17: Bản Phát Hành v1.7.2 — Chuẩn Bị Triển Khai Production & Bảo Vệ Riêng Tư (Production Hardening & Privacy Gate)
- [x] **Dọn Dẹp Triệt Để Tài Khoản Test & Dữ Liệu Rác (Mock Accounts Cleanup):**
  - [x] Xóa bỏ hoàn toàn các tài khoản mock dev (`aria.tanaka@kokoro.me`, `kenji.sato@kokoro.me`) cùng 90 bài viết mẫu và 158 tệp ảnh rác khỏi CSDL PostgreSQL `kokoro_db`.
  - [x] Bảo toàn tuyệt đối tài khoản thật `thanhlongts2k@gmail.com` (6 bài viết, 7 ảnh WebP, 4 tags, 5 categories).
- [x] **Vá Lỗ Hổng Hiển Thị & Bảo Vệ Riêng Tư Tài Khoản Thật (Privacy Guard Gate):**
  - [x] Bổ sung `UserRepository.list_mock_users()`: Chỉ truy vấn người dùng có `google_id LIKE 'mock_%' OR email LIKE '%@kokoro.me'`, loại trừ hoàn toàn tài khoản cá nhân thật (`*@gmail.com`) khỏi endpoint `GET /api/auth/mock-users`.
  - [x] Thắt chặt rào chắn `POST /api/auth/mock-login`: Chặn đứng hành vi đăng nhập trái phép vào tài khoản thật thông qua mock login (trả về `403 Forbidden`).
  - [x] Cấu hình Production: Đặt `MOCK_AUTH=False` trong `.env`.
  - [x] Cập nhật `static/js/auth.js`: Khi `MOCK_AUTH=False` hoặc danh sách mock users rỗng, frontend ẩn hoàn toàn `#mock-account-switcher`, `#mock-account-divider`, `#login-divider`, và `#login-quick-dev-section`, chuyển giao diện về trạng thái Production chuẩn chỉ hiển thị nút Google Sign-In chính thức.
  - [x] Tối ưu hóa Database Seeding cho Unit Tests: Chuyển mock seeding từ `init_db()` sang các hàm kiểm thử chuyên biệt `seed_mock_users_for_testing()` và `clean_mock_users_after_testing()`, đảm bảo toàn bộ 81/81 unit test PASS 100% trong khi CSDL production giữ sạch tuyệt đối.
  - [x] Nâng cấp phiên bản toàn hệ thống lên `v1.7.2` (`app/config.py`, `static/sw.js`, `static/index.html`, `README.md`, `CHANGELOG.md`).

### 🔹 Giai đoạn 18: Bản Phát Hành v1.7.3 — Hoàn Thiện Tương Tác Mobile/PWA & Khép Kín Hệ Thống Kiểm Thử Trình Duyệt E2E
- [x] **Khắc Phục Lỗi Đổi Nhạc Nền Zen Audio Trên Mobile/PWA & Desktop (`static/css/layout.css`, `static/js/zen-audio.js`):**
  - [x] Cho phép nút `.zen-expand-btn` hiển thị dạng compact button tròn (`inline-flex`, ẩn text label) trên mobile thay vì `display: none !important;` giúp người dùng PWA có thể mở panel đổi nhạc.
  - [x] Thiết lập `.zen-player-panel` co giãn linh hoạt trên mobile với `max-width: calc(100vw - 24px)`.
  - [x] Bổ sung phím tắt `Escape` tự động đóng bảng phát nhạc.
- [x] **Khắc Phục Sự Kiện Thiết Lập & Đổi Mã PIN Passcode (`static/js/passcode.js`, `static/js/auth.js`, `static/js/profile-stats.js`):**
  - [x] Gắn kết đầy đủ sự kiện DOM cho `#passcode-change-btn`, `#passcode-toggle-switch`, `#passcode-timeout-select`, `#passcode-close-settings-btn`.
  - [x] Thêm hàm `isPasscodeSetForUser()` và hàm vòng đời `onUserChanged(userId)` cách ly cấu hình mã PIN độc lập theo từng tài khoản.
  - [x] Đồng bộ badge trạng thái `#profile-action-pin-badge` ("Đang bật" / "Chưa bật") tức thì sau khi người dùng tạo hoặc xóa PIN.
- [x] **Khắc Phục Thanh Lọc Cảm Xúc Kho Kỷ Niệm (`static/index.html`, `static/js/app.js`):**
  - [x] Đồng bộ ID container `#memories-mood-filters` với CSS class `.memories-mood-scroll`, tương thích hoàn hảo giữa frontend component và test contracts.
- [x] **Khắc Phục Lỗi Dính Cụm Thẻ & Xử Lý Ảnh 404 Fallback (`static/js/timeline-feed.js`, `static/js/memories-view.js`, `static/css/components.css`):**
  - [x] Bổ sung bộ xử lý lỗi ảnh `onerror` nạp ảnh hoa anh đào dự phòng (`./icons/sakura.svg`) kèm hiệu ứng `.img-fallback` mờ thủy tinh.
  - [x] Đảm bảo không làm vỡ tỉ lệ lưới ảnh mosaic hoặc dính cụm khi ảnh tải thất bại.
- [x] **Khắc Phục Điều Hướng Tablet & Nút Đóng Login Modal (`static/css/layout.css`, `static/index.html`, `static/js/auth.js`):**
  - [x] Bổ sung media query `@media (min-width: 769px)` trong `layout.css` đảm bảo cụm tab `.desktop-view-tabs` luôn hiển thị trên tablet.
  - [x] Thêm nút đóng `#login-modal-close-btn` và xử lý click backdrop cho modal đăng nhập.
- [x] **Bộ Kiểm Thử Tự Động Toàn Hệ Thống (E2E & Unit Test Suites):**
  - [x] `tests/test_full_system_e2e.py`: Kiểm thử tích hợp 6 kịch bản bao phủ toàn diện 13 module cốt lõi (Auth, Entries, Editor, Weather, Categories, Tags, JSON Export v1.1, 31 Static Assets) ➔ PASS 6/6 (100%).
  - [x] `tests/test_interactive_browser_e2e.py`: Kiểm thử tương tác Playwright trực tiếp trên trình duyệt thật (Zen Audio, Passcode PIN flow, Memories mood chips, Calendar navigation, Card Export Modal) ➔ PASS 100% với 0 lỗi console JavaScript.
  - [x] Toàn bộ 87/87 unit tests trong `tests/` PASS 100%.
  - [x] Nâng cấp phiên bản toàn hệ thống lên `v1.7.3` (`app/config.py`, `sw.js`, `index.html`).

### 🔹 Giai đoạn 19: Bản Phát Hành v1.7.4 — Khắc Phục Động Cơ Xóa Ảnh & Đồng Bộ Tài Sản Đĩa - CSDL (Photo Deletion Engine & Asset Reconciliation)
- [x] **Khắc Phục Động Cơ Xóa Ảnh Trong Trình Soạn Thảo (`static/js/editor.js`, `app/routes/entry_routes.py`, `app/repositories/entry_repository.py`):**
  - [x] Giải quyết triệt để sự sai lệch tham số giữa frontend (`deleted_photo_ids` JSON array) và backend (`form.get('deleted_photos')`).
  - [x] Xây dựng hàm helper `_parse_deleted_photo_ids(form)` nhận diện cả JSON array string, comma-separated string và các giá trị mảng lặp lại.
  - [x] Bổ sung REST endpoint `DELETE /api/entries/{id}/photos/{photo_id}` và phương thức `EntryRepository.delete_single_photo()` cho phép xóa ảnh đơn lẻ nguyên tử.
  - [x] Bổ sung phương thức `KokoroAPI.deleteEntryPhoto(entryId, photoId)` trong `static/js/api.js`.
- [x] **Dọn Dẹp & Đồng Bộ Tài Sản Đĩa - CSDL (Database Asset Reconciliation):**
  - [x] Xóa 7 bản ghi ảnh mồ côi trong `entry_photos` mà tệp vật lý WebP đã bị dọn dẹp trước đó, bảo toàn 100% các bản ghi ảnh hợp lệ có tệp tồn tại thực tế trên đĩa.
- [x] **Kiểm Thử Hồi Quy Độc Lập:**
  - [x] Xây dựng `tests/test_photo_deletion.py` kiểm thử luồng xóa ảnh ➔ PASS 2/2 (100%).
  - [x] Toàn bộ 89/89 unit tests trong hệ thống PASS 100%.
  - [x] Nâng cấp phiên bản toàn hệ thống lên `v1.7.4` (`app/config.py`, `sw.js`, `index.html`, test suites).


