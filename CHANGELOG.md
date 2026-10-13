# CHANGELOG.md — Nhật Ký Thay Đổi Kokoro (心)

Tất cả các thay đổi đáng chú ý của dự án **Kokoro — Personal Diary & Photo Journal PWA** được ghi nhận chi tiết tại tệp này theo chuẩn [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) và tuân thủ [Semantic Versioning (SemVer)](https://semver.org/).

---

## [1.6.4] - 2026-10-13
### Refactored & Architectural Excellence (Clean Architecture & Strict Typing Transition)
- **Tách Lớp Kiến Trúc Độc Lập (Modular Layered Architecture & Layer Isolation):**
  * **Repositories Layer (`app/repositories/`):** Đóng gói 100% raw SQL vào các DAO chuyên biệt: `EntryRepository`, `UserRepository`, `CategoryRepository`, `TagRepository`, `StatsRepository`, `PhotoRepository`.
  * **Controllers Layer (`app/routes/`):** Tái cấu trúc thành Pure Controllers không chứa bất kỳ câu lệnh raw SQL nào.
  * **Thu gọn God-file:** Rút gọn `app/routes/entry_routes.py` từ 1.568 dòng xuống còn **291 dòng code** (đạt xuất sắc chuẩn < 300 dòng code).
  * **Strict Typing DTOs (`app/schemas/`):** Chuẩn hóa toàn bộ dữ liệu trao đổi bằng typed dataclasses (`EntryDTO`, `EntryFilterDTO`, `EntryCreateDTO`, `EntryUpdateDTO`, `UserDTO`, `UserSessionDTO`, `CategoryDTO`, `TagDTO`, `StatsSummaryDTO`, `CleanupStatsDTO`), triệt tiêu hoàn toàn untyped dictionaries thô.
- **Khôi Phục & Đồng Bộ Bộ Kiểm Thử Tự Động (Test Suite Standardization):**
  * Khôi phục toàn bộ 10 file test in-memory vào `tests/` gốc.
  * Chạy `python -m unittest discover -s tests` đạt đầy đủ **57/57 tests PASS 100%**.

### Added & Maintenance (Sprint 2 Gap Closure — Dọn Dẹp Ảnh Mồ Côi, Caching CDN & Phân Trang Lũy Tiến)
- **Động Cơ Dọn Dẹp Ảnh Mồ Côi Bảo Vệ Dữ Liệu (`app/services/media_service.py` & `app/routes/entry_routes.py`):**
  * Logic `MediaService.scan_and_cleanup_orphans(grace_period_hours=2.0)` quét đối soát toàn diện giữa kho ảnh vật lý (`uploads/originals/`, `uploads/thumbnails/`) và cơ sở dữ liệu PostgreSQL (`entry_photos`).
  * **Triệt tiêu bẫy đường dẫn Windows:** Chuẩn hóa và chỉ so sánh theo tên file thuần túy (`os.path.basename(path.replace('\\', '/'))`) giữa đĩa và CSDL, loại bỏ hoàn toàn nguy cơ lệch dấu gạch chéo (`/` vs `\`) làm xóa nhầm ảnh thật của người dùng.
  * **Khoảng đệm an toàn Grace Period 2 giờ:** Tự động bảo vệ và bỏ qua mọi tệp unreferenced mới tải lên trong vòng 2 giờ (`mtime > cutoff_time`), chống xóa nhầm ảnh khi người dùng đang soạn thảo dở dang chưa bấm lưu bài.
  * Endpoint bảo trì an toàn `POST /api/maintenance/cleanup-orphaned-media` yêu cầu xác thực người dùng, trả về số lượng tệp giải phóng và dung lượng MB chi tiết.
- **Tối Ưu Service Worker & Cache CDN Ngoại Tuyến (`static/sw.js`, `app/config.py`, `static/index.html`):**
  * Nâng cấp phiên bản bộ nhớ đệm lên `kokoro-v1.6.4`.
  * Bổ sung whitelist máy chủ CDN ngoại tuyến: Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) và Bootstrap Icons (`cdn.jsdelivr.net`).
  * Hỗ trợ lưu trữ runtime cho các phản hồi cross-origin (`opaque` và `cors`), đồng thời cache runtime ảnh thumbnail bài viết (`/uploads/thumbnails/`), giúp PWA hiển thị trọn vẹn ngoại tuyến ngay cả khi không có kết nối mạng.
  * Chặn triệt để các yêu cầu không phải GET (`request.method !== 'GET'`) và duy trì native bypass tuyệt đối cho `/api/`.
- **Phân Trang Lũy Tiến & Trải Nghiệm Cuộn Mượt Mà Trên Mobile (`static/js/app.js` & `static/css/components.css`):**
  * Tích hợp `timelinePagination` (15 bài viết / trang) và nút Soft Sakura `[ 🍃 Xem thêm bài viết cũ hơn... ]` ở cuối dòng thời gian.
  * **Chống giật layout & giữ scroll offset trên mobile:** Khi bấm "Xem thêm", hệ thống append trực tiếp các thẻ bài viết mới vào DOM qua `DocumentFragment` mà không re-render các thẻ cũ, loại bỏ hiện tượng giật giật layout hoặc nhảy vị trí cuộn lên đầu trang trên iOS Safari và Android Chrome.
  * Tự động reset giới hạn hiển thị về 15 khi người dùng đổi bộ lọc (mood, tag, search, date), đảm bảo Mini Calendar và thống kê toàn bộ nhật ký luôn giữ nguyên vẹn 100% snapshot dữ liệu.
- **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_sprint2_gap_closure.py`):**
  * Thêm 6 ca kiểm thử độc lập bao quát: Chuẩn hóa phiên bản v1.6.4, Bẫy đường dẫn Windows, Grace Period 2 giờ, Endpoint bảo trì, Service Worker CDN Whitelist, và Hợp đồng phân trang frontend.
  * Đạt 100% PASS (49/49 tests) trên toàn bộ test runner của dự án Kokoro.

## [1.6.3] - 2026-10-13
### Added & Visual (Daily Card Export — Xuất Thẻ Ảnh Kỷ Niệm Canvas)
- **Công Cụ Render Canvas Chuẩn 1080p Chống Crash Safari (`static/js/card-export.js`):**
  * Khóa cứng kích thước bộ đệm vật lý của Canvas đúng chuẩn Full HD: Vuông 1:1 (`1080 × 1080 px`) và Story 9:16 (`1080 × 1920 px`). Tuyệt đối không nhân DPR vào kích thước buffer vật lý, triệt tiêu hoàn toàn nguy cơ vượt ngưỡng 16.7 triệu pixel gây crash WebKit/Safari trên iOS.
  * Cổng chặn tải font async (`document.fonts.ready`): Đảm bảo 100% font chữ Google Fonts (`Outfit`, `Plus Jakarta Sans`) và hệ thống emoji đã sẵn sàng trước khi vẽ, chống lệch dòng hoặc lỗi ô vuông tofu (`[]`).
  * Thuật toán bẻ dòng thông minh & bảo toàn đoạn văn (`wrapAndFitText`): Tách đoạn theo `\r?\n` trước khi bẻ dòng theo từ, tự động cắt tỉa và gắn dấu ba chấm `"..."` tinh tế khi vượt quá chiều cao khả dụng, không bao giờ tràn đè lên footer, thời tiết hoặc watermark.
  * Bố cục thích ứng (Adaptive Layout):
    - Chế độ Thuần chữ: Bố cục Zen Quote thanh thoát, font lớn, biểu tượng đóa hoa anh đào chìm nghệ thuật.
    - Chế độ Có ảnh: Khung ảnh bo tròn tinh tế (hỗ trợ badge `+X ảnh` nếu có nhiều ảnh) kết hợp tiêu đề & trích đoạn hài hòa.
  * Web Share API tức thì & Chống lỗi `NotAllowedError`: Tiền tạo sẵn Blob/File (`currentExportFile`) ngay sau khi render xong preview để gọi trực tiếp `navigator.share({ files })` trong User Gesture. Tự động fallback sang tải về trực tiếp trên Desktop.
  * Dọn dẹp bộ nhớ nghiêm ngặt: Tự động thu hồi `URL.revokeObjectURL(activeBlobUrl)` và reset kích thước canvas về 0 khi đóng modal hoặc đổi tỷ lệ.
- **Giao Diện Modal Xuất Thẻ & Tích Hợp Timeline (`static/index.html`, `static/css/components.css`, `static/js/app.js`):**
  * Hộp thoại `#card-export-modal` phong cách Soft Sakura Glass với bộ gạt chọn tỷ lệ [ Vuông 1:1 ] / [ Story 9:16 ], preview canvas responsive mượt mà và 2 nút hành động [ Tải ảnh về ] và [ Chia sẻ ngay ].
  * Bổ sung nút icon `[ 🖼️ Xuất ảnh ]` trên thanh công cụ mỗi thẻ bài viết ngoài Timeline.
- **Nâng Cấp Service Worker & Cache PWA (`static/sw.js`, `app/config.py`, `static/index.html`):**
  * Nâng cấp phiên bản bộ nhớ đệm lên `kokoro-v1.6.3`.
  * Thêm `card-export.js?v=1.6.3` vào danh sách tài nguyên ngoại tuyến (Offline-First 100%).
  * Đặt thẻ script `card-export.js` trước `app.js` đảm bảo thứ tự nạp DOM an toàn.
  * Cập nhật `Config.APP_VERSION = "v1.6.3"` và version badge footer.
- **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_v163_card_export.py`):**
  * Đạt 100% PASS bộ kiểm thử mới kiểm tra kích thước buffer 1080p, thuật toán bẻ dòng ngắt đoạn tiếng Việt, layout modes, share flow và dọn dẹp bộ nhớ.

## [1.6.2] - 2026-10-13
### Added & Mindful (Daily Zen Prompt — Gợi Ý Suy Ngẫm Chánh Niệm Mỗi Ngày)
- **Kho 36 Câu Hỏi Gợi Ý Chánh Niệm Kokoro (`static/js/zen-prompts.js`):**
  * Kho tàng 36 câu hỏi suy ngẫm chữa lành phân bổ cân bằng trên 4 trụ cột cảm xúc: Biết ơn (Gratitude 🍵), Buông bỏ & Xoa dịu (Letting Go 🌙), Hiện diện & Tận hưởng (Presence 🌸), Phát triển & Nội lực (Growth ⚡).
  * Thuật toán chọn câu hỏi tất định theo ngày (Deterministic Local Date Seed): Chống triệt để bẫy lệch múi giờ UTC (`getLocalDateString()` tính theo ngày lịch cục bộ máy client), câu hỏi đổi mới đồng bộ chính xác lúc 00:00 đêm.
  * Hỗ trợ nút xúc xắc ngẫu nhiên 🎲 (`getRandomPrompt()`) với hiệu ứng xoay mượt mà `@keyframes spinDice` và lưu trữ trạng thái câu hỏi hiện tại trong `localStorage`.
  * Cơ chế ghi nhớ trạng thái đóng/thu gọn thẻ hôm nay (`localStorage: kokoro_zen_dismissed_date`), tự động hiển thị lại khi sang ngày mới.
- **Thẻ Gợi Ý Chánh Niệm Ngoài Timeline (`static/index.html`, `static/css/components.css`):**
  * Thẻ kính mờ `#daily-zen-card` đặt trang trọng ngay đầu dòng thời gian với icon đóa hoa anh đào, nút đổi câu hỏi 🎲 và nút đóng/mở thu gọn.
  * Nút "Viết theo gợi ý này ✨" chuyển mượt mà vào trình soạn thảo.
- **Tích Hợp An Toàn Tuyệt Đối Bản Nháp Vào Trình Soạn Thảo Editor (`static/js/editor.js`):**
  * Bổ sung thanh trạng thái hint pill `#editor-zen-prompt-hint` trong modal/bottom sheet editor để người dùng luôn thấy câu hỏi gợi ý khi đang viết.
  * **Draft Safety Protocol:** Bảo vệ bản nháp 100%. Nếu người dùng đã có nội dung trong ô soạn thảo, hệ thống không ghi đè mà chèn trích dẫn chuẩn Markdown `> 🌸 "${promptText}"\n\n` lên đầu bài viết, đồng thời đặt con trỏ chuột (`setSelectionRange`) ngay sau câu trích dẫn để người dùng viết tiếp tự nhiên.
  * Tự động chọn sẵn tâm trạng đề xuất (`suggestedMood`) phù hợp với nội dung câu hỏi.
- **Nâng Cấp Service Worker & Cache PWA (`static/sw.js`, `app/config.py`, `static/index.html`):**
  * Nâng cấp phiên bản bộ nhớ đệm lên `kokoro-v1.6.2`.
  * Thêm `zen-prompts.js?v=1.6.2` vào danh sách tài nguyên ngoại tuyến (Offline-First 100%).
  * Đặt thẻ script `zen-prompts.js` trước `editor.js` và `app.js` trong `index.html` đảm bảo thứ tự nạp DOM an toàn.
  * Cập nhật `Config.APP_VERSION = "v1.6.2"`.
- **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_v162_zen_prompts.py`):**
  * Kiểm tra tính nhất quán của seed ngày cục bộ, phân bổ 4 trụ cột của 36 câu hỏi, bảo toàn bản nháp trong Editor, và hợp đồng giao diện DOM/CSS.

## [1.6.1] - 2026-10-13
### Added & Enhanced (Data Integrity, Weather Selector UI & Dev Hot-Reload)
- **Vá Lỗ Hổng Toàn Vẹn Dữ Liệu Ngoại Tuyến IndexedDB (`static/js/api.js`):**
  * Lưu trữ `category_id` chuẩn kiểu số nguyên vào cơ sở dữ liệu ngoại tuyến `offline_entries` trong `saveOfflineEntry()`.
  * Phòng chống triệt để bẫy ép kiểu chuỗi `"null"` khi mạng kết nối lại trong `syncOfflineQueue()`. Chỉ đính kèm trường `category_id` vào `FormData` khi thực sự mang giá trị hợp lệ, triệt tiêu hoàn toàn lỗi `ValueError` HTTP 500 do backend parse `int("null")`.
- **Nâng Cấp Hệ Thống Sao Lưu & Khôi Phục JSON (`app/routes/entry_routes.py`):**
  * **Xuất Dữ Liệu (`GET /api/entries/export`):** Bổ sung danh sách bảng `categories` tùy chỉnh của người dùng (`id`, `name`, `icon`, `color`, `sort_order`) và đính kèm `category_id`, `category_name`, `category_icon`, `category_color` vào từng bài viết với phiên bản định dạng `export_version = "1.1"`.
  * **Khôi Phục Dữ Liệu (`POST /api/entries/import`):** Tự động nạp và ánh xạ lại `categories` tùy chỉnh từ tệp sao lưu; tự động map lại `category_id` mới với xử lý xung đột `ON CONFLICT (user_id, name)` và cơ chế kiểm tra dự phòng (pre-check query fallback).
  * **Tương Thích Ngược 100% (Backward Compatibility):** Khôi phục trơn tru và hoàn hảo các tệp sao lưu chuẩn v1.0 cũ không có trường `category_id` hoặc thiếu bảng `categories`, không bao giờ phát sinh `KeyError`.
  * Bảo toàn mốc thời gian nguyên bản `created_at` và `updated_at` của bài viết khi khôi phục từ tệp sao lưu.
- **Trình Chọn Thời Tiết Trực Quan Trong Editor (`static/index.html`, `static/css/components.css`, `static/js/editor.js`):**
  * Bổ sung thanh chọn thời tiết capsule chips (`#editor-weather-picker-list`) gồm 5 trạng thái thời tiết tinh tế: Nắng ☀️ (`sunny`), Mưa 🌧️ (`rainy`), Nhiều mây ⛅ (`cloudy`), Gió 🍃 (`windy`), Tuyết ❄️ (`snowy`).
  * Đồng bộ trường thời tiết với vòng đời biên tập: Tự động lưu và khôi phục trong bản nháp (`localStorage`), nạp thời tiết khi chỉnh sửa bài viết cũ, và gửi chính xác lên máy chủ (thay thế giá trị `'sunny'` cố định trước đây).
  * Hiển thị biểu tượng thời tiết `.weather-badge-pill` tinh tế trên tiêu đề thẻ bài viết Dòng thời gian (`static/js/app.js`).
- **Xác Thực Tuyệt Đối Cập Nhật Bài Viết (`PUT /api/entries/{id}`):**
  * Xác minh và đảm bảo 100% câu lệnh SQL UPDATE cập nhật chuẩn xác trường `weather = %s` cùng `category_id` trên mọi nhánh điều kiện.
- **Tự Động Nạp Lại Mã Nguồn Trong Môi Trường Phát Triển (`server.py`):**
  * Kích hoạt tham số `reload=Config.DEBUG` trong `uvicorn.run()` giúp máy chủ tự động cập nhật khi mã nguồn thay đổi mà không cần khởi động lại thủ công.
- **Nâng Cấp Phiên Bản Ứng Dụng & Cache PWA (`app/config.py`, `static/sw.js`, `static/index.html`):**
  * Tăng phiên bản chính thức lên `v1.6.1` trong `Config.APP_VERSION`.
  * Nâng cấp bộ nhớ đệm Service Worker lên `kokoro-v1.6.1` và cập nhật chuỗi truy vấn tài nguyên `?v=1.6.1`.
- **Bộ Kiểm Thử Tự Động Toàn Diện Cho Tính Toàn Vẹn Dữ Liệu (`tests/test_v161_data_integrity.py`):**
  * 100% PASS bộ kiểm thử mới kiểm tra toàn diện: Vòng đời thời tiết (Create/Read/Update), Đồng bộ ngoại tuyến không có chuỗi "null", Xuất/Nhập JSON v1.1 có danh mục, Tương thích ngược với tệp JSON v1.0, và Bảo toàn mốc thời gian.

## [1.6.0] - 2026-10-12
### Added & Unified (Official Release: Dynamic Mood & Category Management System)
- **Hệ Thống Quản Lý Danh Mục & Cảm Xúc Động (Dynamic Mood Taxonomy & Unified Categories):**
  * Thống nhất triệt để khái niệm "Danh mục" và "Cảm xúc" thành Một Nguồn Chân Lý Duy Nhất (Single Source of Truth - SSoT). Người dùng có toàn quyền Thêm / Sửa / Đổi icon emoji / Đổi màu / Xóa các tâm trạng & đề tài cuộc sống.
  * Bảng CSDL PostgreSQL `categories` độc lập kết hợp khóa ngoại `entries.category_id REFERENCES categories(id) ON DELETE SET NULL`. Bảo vệ an toàn tuyệt đối 100% bài viết của người dùng (không bao giờ xóa mất bài viết khi xóa danh mục).
  * 3 Chỉ mục hiệu năng cao: `idx_categories_user`, `idx_entries_user_cat`, `idx_entry_tags_tag_id`.
  * Khởi tạo sẵn 5 tâm trạng cốt lõi của Kokoro làm danh mục mặc định (`Bình yên 🌸`, `Ấm áp ☕`, `Chiêm nghiệm 🌙`, `Biết ơn 🍵`, `Năng lượng ⚡`).
- **Trình Soạn Thảo Nhật Ký Đa Năng (`static/js/editor.js`, `static/index.html`):**
  * Tự động nạp danh sách danh mục động qua REST API (`KokoroAPI.getCategories()`).
  * Giao diện chip capsule trực quan (`#editor-mood-picker-list`) kèm link tắt mở nhanh modal quản lý (`#editor-manage-categories-link`).
  * Hỗ trợ lưu trữ `category_id` vào multipart upload, bản nháp `localStorage` tự động lưu/khôi phục, và hàng đợi ngoại tuyến IndexedDB.
- **Dòng Thời Gian & Thẻ Bài Viết Kính Mờ (`static/js/app.js`):**
  * Đồng bộ hóa dải chip lọc danh mục trên Desktop Sidebar (`#sidebar-mood-filters`) và Mobile Horizontal Scroll (`#mobile-mood-chips`).
  * Thẻ bài viết tự động hiển thị `.category-badge-pill` với biểu tượng Emoji và màu sắc Pastel tùy chỉnh; hỗ trợ fallback mượt mà cho các bài viết cũ.
  * Lọc bài viết chính xác theo `category_id` hoặc tên cảm xúc.
- **Kho Kỷ Niệm Hình Ảnh (`static/js/app.js`):**
  * Thanh lọc cảm xúc ảnh (`#memories-mood-filters`) tự động cập nhật theo danh mục động, hiển thị số lượng ảnh thực tế theo từng danh mục.
  * Lớp phủ thông tin ảnh kỷ niệm hiển thị chuẩn xác tên và icon danh mục kèm ngày giờ.
- **Hạ Tầng PWA & Cache Busting (`static/sw.js`, `app/config.py`):**
  * Tăng phiên bản ứng dụng chính thức lên `v1.6.0` trong `Config.APP_VERSION` và `GET /api/auth/config`.
  * Nâng cấp Service Worker cache lên `kokoro-v1.6.0`, đồng bộ truy vấn phiên bản `?v=1.6.0` cho toàn bộ tài nguyên CSS/JS.
- **Hệ Thống Kiểm Thử Tự Động Toàn Diện (`tests/`):**
  * 13/13 Ca kiểm thử tự động đạt 100% PASS (`test_v160_backend_api.py`, `test_v160_modal_client.py`, `test_v160_full_integration.py`).

## [1.6.0-beta.2] - 2026-10-12
### Added & Enhanced (Category & Tag Manager Modal UI, Emoji Picker & iOS PWA Diagonal Drag Fix)
- **Thiết Kế Lại Toàn Diện Modal Quản Lý Danh Mục & Thẻ (`static/index.html`, `static/css/components.css`):**
  - **Tab 1 — Cảm xúc & Tâm trạng (Moods/Categories Manager):**
    * Thanh tạo mới: Ô nhập tên cảm xúc mới + Nút chọn Icon Emoji (popover 20 icon tinh tế: 🌸, ☕, 🌙, 🍵, ⚡, 🥰, 🌈, 🌧️...) + Bảng 7 màu Pastel nhận diện + Nút `[ + Thêm ]`.
    * Danh sách danh mục cảm xúc dạng thẻ kính mờ: Hiển thị badge pill với icon lớn, tên, màu sắc, số lượng bài viết (`usage_count`), nút `[ ✏️ Đổi tên / Sửa icon ]`, và nút `[ 🗑️ Xóa danh mục ]` an toàn.
  - **Tab 2 — Thẻ chủ đề (Hashtags Manager):**
    * Thanh tạo thẻ chủ động: Ô nhập `#Nhập tên thẻ mới...` + Nút `[ + Tạo Thẻ ]` chuẩn hóa hashtag.
    * Thống kê tổng số lượng thẻ, nút `[ 🧹 Dọn dẹp thẻ 0 bài ]`, nút đổi tên và xóa thẻ.
- **Khắc Phục Dứt Điểm Bug Kéo Chéo / Xô Lệch Trên iOS PWA (`static/css/layout.css`, `static/css/components.css`):**
  - Áp dụng cơ chế khóa cứng trục Y (Strict Y-axis Locking): `overflow-y: hidden !important; touch-action: pan-x !important; overscroll-behavior-x: contain !important; overscroll-behavior-y: none !important; -webkit-overflow-scrolling: touch !important;` trên `.mobile-mood-scroll`, `#mobile-mood-chips`, `.memories-mood-scroll`, `.memories-tags-scroll`, và `.category-picker-scroll`.
  - Triệt tiêu 100% hiện tượng rung lắc xô lệch chéo (diagonal rubber-band dragging) khi người dùng lướt ngón tay ngang trên màn hình cảm ứng iPhone.
- **Bộ Điều Khiển Tương Tác Phía Client (`static/js/tag-manager.js`):**
  - Kết nối trọn vẹn các phương thức REST API `KokoroAPI.getCategories()`, `createCategory()`, `updateCategory()`, `deleteCategory()`, `createTag()`.
  - Cơ chế đồng bộ phản ứng tức thì (Reactive Callback): Khi thêm/sửa/xóa danh mục hoặc thẻ, tự động thông báo và làm mới giao diện Editor Modal và Dòng thời gian.
- **Bộ Kiểm Thử Tự Động Giao Diện (`tests/test_v160_modal_client.py`):**
  - Kiểm tra toàn vẹn cấu trúc DOM, các quy chuẩn CSS khóa trục Pan-X, kích thước vùng chạm WCAG 2.5.5 >= 44px và phương thức JS đạt 100% PASS.

## [1.6.0-beta.1] - 2026-10-12
### Added & Architected (Database Migration & Dynamic Moods / Categories REST API)
- **Thiết Kế & Triển Khai Bảng `categories` & Khóa Ngoại `entries.category_id` (`app/database.py`):**
  - Tạo bảng `categories` (id SERIAL PRIMARY KEY, user_id INT FK, name VARCHAR(100), icon VARCHAR(50), color VARCHAR(50), sort_order INT, created_at TIMESTAMPTZ, UNIQUE(user_id, name)).
  - Bổ sung cột khóa ngoại `entries.category_id REFERENCES categories(id) ON DELETE SET NULL` bảo vệ an toàn 100% dữ liệu nhật ký khi xóa danh mục/mood.
  - Tối ưu hóa truy vấn với 3 chỉ mục PostgreSQL: `idx_categories_user`, `idx_entries_user_cat`, và `idx_entry_tags_tag_id`.
  - Khởi tạo 5 tâm trạng cốt lõi của Kokoro làm danh mục mặc định: Bình yên 🌸 (`#ec4899`), Ấm áp ☕ (`#f59e0b`), Chiêm nghiệm 🌙 (`#8b5cf6`), Biết ơn 🍵 (`#10b981`), Năng lượng ⚡ (`#3b82f6`).
- **Hệ Thống REST API CRUD Danh Mục / Moods Đầy Đủ (`app/routes/entry_routes.py`):**
  - `GET /api/categories`: Lấy danh sách danh mục/moods thuộc sở hữu của người dùng hiện tại kèm số lượng bài viết (`usage_count`) và sắp xếp theo `sort_order`.
  - `POST /api/categories`: Tạo danh mục/mood mới, validate tên không được rỗng và kiểm tra trùng lặp tên.
  - `PUT /api/categories/{id}`: Cập nhật tên, icon emoji, màu sắc và tự động đồng bộ trường `entries.mood`.
  - `DELETE /api/categories/{id}`: Xóa danh mục an toàn, tự động chuyển các bài viết liên kết về `category_id = NULL` và fallback `mood = 'serene'`, không xóa bài viết.
  - `POST /api/tags`: Cho phép chủ động tạo hashtag mới trước khi viết bài với chuẩn hóa ký tự `#`.
  - Cập nhật `GET /api/entries`, `POST /api/entries`, `PUT /api/entries/{id}` hỗ trợ lọc và lưu trữ `category_id` kết hợp metadata (tên, icon, màu).
- **Chuẩn Hóa Ưu Tiên Xác Thực API Token & Cô Lập Người Dùng (`app/auth.py`):**
  - Ưu tiên cờ `Authorization: Bearer <token>` trước cookie trình duyệt, đảm bảo các API clients và test suites vận hành độc lập, không bị rò rỉ session giữa các người dùng.
- **Client API Wrapper Cho Categories & Tags (`static/js/api.js`):**
  - Bổ sung `getCategories()`, `createCategory()`, `updateCategory()`, `deleteCategory()`, `createTag()`.
- **Bộ Kiểm Thử Tự Động Toàn Diện (`tests/test_v160_backend_api.py`):**
  - Bao phủ 7 ca kiểm thử nghiêm ngặt đạt 100% PASS (Seeding, Validation, Update Sync, Safe Delete, Proactive Tag, Data Isolation, Entry Joined Filter).

## [1.5.6] - 2026-10-12
### Fixed & Hardened (Security Hotfix, Stored XSS Mitigation, History API & Mobile Accessibility)
- **[P0 - CRITICAL SECURITY] Vá Triệt Để Lỗ Hổng Stored XSS (`static/js/api.js`, `static/js/app.js`, `static/js/tag-manager.js`, `static/js/auth.js`, `static/js/editor.js`):**
  - Xây dựng tiện ích chuẩn hóa `escapeHtml(unsafe)` trong `api.js`, đăng ký toàn cục tại `window.escapeHtml` và `window.KokoroAPI.escapeHtml`.
  - Bọc mã hóa 100% dữ liệu người dùng render qua `innerHTML`: tiêu đề (`entry.title`), nội dung (`entry.content`), nhãn thẻ (`tag.name`, `tagsHtml`), tên ảnh đính kèm (`p.name`, `file.name`), ngày giờ (`displayDate`), và thông tin tài khoản mock/profile.
  - Ngăn chặn hoàn toàn mọi payload script injection, mã HTML độc hại khi render trên Timeline Feed, Full Calendar, Memories Gallery, và Tag Manager.
- **[P1 - HIGH INTERACTION] Khắc Phục Lỗi Modal Quản Lý Danh Mục Bị Kẹt Pointer-Events (`static/js/tag-manager.js`):**
  - Cập nhật `openManagerModal(tab)`: Thêm `modalEl.classList.add('active')` và `window.lockBodyScroll(true)` để kích hoạt thuộc tính CSS `pointer-events: auto`.
  - Cập nhật `closeManagerModal()`: Gỡ bỏ `modalEl.classList.remove('active')` và `window.lockBodyScroll(false)` đồng bộ.
  - Người dùng có thể click tương tác mượt mà với các tab, nút đổi tên, nút xóa thẻ, và nút đóng modal.
- **[P2 - SECURITY CONFIG] Bổ Sung Cờ `secure=True` Cho Session Cookie (`app/routes/auth_routes.py`):**
  - Thêm chỉ thị `secure=True` cho tất cả các lời gọi `response.set_cookie(...)` tại endpoint `mock_login` và `google_login`.
  - Đảm bảo session cookie luôn được truyền tải an toàn độc quyền qua kênh mã hóa HTTPS, ngăn chặn rò rỉ cookie trên môi trường mạng.
- **[P2 - USER EXPERIENCE] Đồng Bộ HTML5 History API Cho Điều Hướng Tabs (`static/js/app.js`):**
  - Bổ sung `history.pushState({ view: viewName }, '', '#' + viewName)` vào hàm `switchView(viewName, updateHistory = true)`.
  - Lắng nghe sự kiện `popstate` toàn cục để điều hướng tab liền mạch khi người dùng nhấn nút Back / Forward của trình duyệt hoặc cử chỉ vuốt quay lại trên điện thoại.
  - Hỗ trợ khôi phục deep link hash (`#calendar`, `#memories`, `#profile`) khi tải lại trang mà không làm mất lịch sử duyệt.
- **[P3 - MOBILE ACCESSIBILITY] Chuẩn Hóa Kích Thước Vùng Chạm Touch Targets >= 44px (`static/css/components.css`, `static/css/layout.css`):**
  - Mở rộng kích thước nút icon tròn (`#theme-toggle-btn`, `#zen-toggle-btn`, `.action-icon-btn`): `min-width: 40px; min-height: 40px;` kèm pseudo-element `::before` (`inset: -4px`) tạo diện tích chạm xúc giác đạt chuẩn WCAG 2.5.5 (48x48px).
  - Chuẩn hóa các chip chọn cảm xúc `.mood-option-chip`: `min-height: 44px; padding: 0 16px;`.
  - Mở rộng kích thước nút điều hướng tháng trên lịch (`#full-cal-prev-btn`, `#dt-cal-prev-btn`, v.v.): `min-width: 36px; min-height: 36px; padding: 6px;` kèm vùng đệm mở rộng `::before`.
- **Nâng Cấp Phiên Bản Hệ Thống Lên v1.5.6:**
  - Đồng bộ `APP_VERSION = "v1.5.6"` trong `app/config.py`.
  - Cập nhật `CACHE_NAME = 'kokoro-v1.5.6'` và query params trong `static/sw.js`.
  - Cập nhật phiên bản badge `v1.5.6` và query string cache-busting trong `static/index.html`.

## [1.5.5] - 2026-10-12
### Added & Fixed (System Refactor, Adaptive Media, Smooth Time Wheel, Memories Redesign & Tag Management)
- **Tiêu Diệt Triệt Để Ghost Lightbox Controls (`static/index.html`, `static/js/lightbox.js`, `static/css/components.css`, `static/css/layout.css`):**
  - Khóa cứng tại cây DOM với inline style phòng thủ trực tiếp: `style="display: none !important; opacity: 0 !important; pointer-events: none !important;"`.
  - JS Hard-Lock trong `lightbox.js`: Quản lý `this.controlsBarEl.style.cssText` trực tiếp trong `init()`, `open()`, và `close()`.
  - Dọn sạch CSS selector, triệt tiêu 100% tình trạng thanh công cụ nổi lơ lửng khi modal đóng.
- **Khắc Phục Lỗi Méo / Dẹp Ảnh Dọc Chụp Màn Hình Điện Thoại (`static/css/layout.css`, `static/css/components.css`):**
  - Xóa bỏ `aspect-ratio: 16 / 9;` cứng nhắc ở bài viết 1 ảnh trên Timeline Feed. Chuyển sang cơ chế Adaptive Container: `aspect-ratio: auto !important; max-height: 480px !important; display: flex !important; align-items: center !important; justify-content: center !important; background: rgba(0, 0, 0, 0.03);`.
  - Ảnh hiển thị `object-fit: contain !important; max-height: 480px !important; width: auto !important; max-width: 100% !important; border-radius: var(--radius-md);`, bảo toàn hoàn hảo tỷ lệ dọc 9:16, 9:20 của ảnh chụp màn hình điện thoại.
  - Khung xem trước Editor Preview: Thêm `object-fit: cover !important; object-position: center !important;`.
- **Nâng Cấp Bộ Chọn Giờ Smooth Time Picker Cho Mobile (`static/js/datetime-picker.js`, `static/index.html`, `static/css/components.css`):**
  - Thay thế cụm nút bấm mũi tên `^`/`v` thô sơ bằng khối "Soft Sakura Time Wheel Card" thanh nhã `[ 🕒 14 : 34 ]` kèm nhãn phụ `Chạm để cuộn giờ ✨`.
  - Phủ vô hình `<input type="time" id="dt-native-time-input">` (`opacity: 0; position: absolute; inset: 0; width: 100%; height: 100%; cursor: pointer;`) kích hoạt trực tiếp **Bộ bánh xe cuộn Native (iOS Drum Wheel Spinner)** có sẵn quán tính mượt mà và haptic feedback trên iPhone/Android.
  - Tự động cập nhật giờ:phút hiển thị theo thời gian thực khi cuộn; giữ nguyên phím tắt `[ ⏱️ Hiện tại ]` và `[ ✨ Xác nhận ]`.
- **Tái Cấu Trúc Đồng Bộ Màn Hình "Kho Kỷ Niệm" (`#view-memories`) (`static/index.html`, `static/js/app.js`, `static/css/components.css`):**
  - Di chuyển container `#mobile-mood-chips` vào hẳn bên trong `#view-timeline`, đảm bảo thanh này chỉ xuất hiện ở tab Timeline, không bao giờ xuất hiện ở Kỷ niệm hay Lịch.
  - Thay thế cụm nút tròn cũ bị bóp méo trong Kho Kỷ niệm bằng thanh nhộng nằm ngang `.memories-mood-scroll` chứa các chip `.mood-chip-pill` chuẩn Design System.
  - Bổ sung bộ lọc Hashtag cuộn ngang cho Kho Kỷ niệm (`#memories-tag-chips`): Tự động trích xuất các hashtag từ những bài viết có ảnh; bấm vào tag để lọc nhanh ảnh theo chủ đề (toggle filter).
- **Cô Lập Trạng Thái (State Isolation) & Chống Rò Rỉ Filter Giữa Các Màn Hình (`static/js/app.js`):**
  - Giữ nguyên bản snapshot dữ liệu bài viết đầy đủ `this.allEntries`, không bao giờ bị ghi đè bởi kết quả filter tạm thời.
  - Tách biệt hoàn toàn trạng thái lọc giữa các màn hình: `this.timelineState = { mood: 'all', tag: null, search: '' }` và `this.memoriesState = { mood: 'all', tag: null }`.
  - Khi chuyển từ Timeline sang Memories: Tự động render kho ảnh độc lập, không bị kẹt query tìm kiếm hay tag từ Timeline.
- **Fix Chip Hashtag Dính Focus & Bổ Sung Phân Hệ Quản Lý Danh Mục Thẻ (`static/js/tag-manager.js`, `static/css/components.css`, `static/index.html`, `app/routes/entry_routes.py`, `static/js/api.js`):**
  - Fix Sticky Hover trên Mobile: Gọi `e.currentTarget.blur()` giải phóng focus state sau khi chạm chip; bọc hover vào `@media (hover: hover)`; hàm `syncChipStates()` đồng bộ trạng thái `.selected` chuẩn xác.
  - Thêm phân hệ "Quản lý Danh mục & Thẻ" trong Trang Cá nhân (`#view-profile`) với modal kính mờ `#category-tag-manager-modal`:
    + Tab 1 - Tâm trạng: Xem số lượng và tỷ lệ phần trăm bài viết theo từng mood.
    + Tab 2 - Thẻ chủ đề: Xem danh sách toàn bộ tag, số lượng bài dùng (`usage_count`), nút `[ ✏️ Đổi tên ]`, nút `[ 🗑️ Xóa ]` và nút `[ 🧹 Dọn dẹp thẻ mồ côi (0 bài) ]`.
  - Backend REST API hỗ trợ:
    + `PUT /api/tags/{id}`: Đổi tên thẻ chủ đề (tự động merge nếu tên mới đã tồn tại).
    + `DELETE /api/tags/{id}`: Xóa thẻ chủ đề và gỡ khỏi các bài viết liên quan.
    + `DELETE /api/tags/cleanup-orphans`: Xóa sạch toàn bộ thẻ mồ côi (usage_count = 0) của user hiện tại.
- **Nâng Cấp Phiên Bản Hệ Thống Lên v1.5.5:**
  - Cập nhật `APP_VERSION = "v1.5.5"` trong `app/config.py`.
  - Cập nhật `CACHE_NAME = 'kokoro-v1.5.5'` và hash assets trong `static/sw.js`.
  - Cập nhật toàn bộ script/link query string `?v=1.5.5` trong `static/index.html`.
  - Viết test suite `tests/test_v155_tag_manager_and_media.py` kiểm thử toàn diện các API mới và chạy toàn bộ regression tests đạt **PASS 100%**.

## [1.5.4] - 2026-10-12
### Added & Refactored (Decoupling Architecture, Custom Date & Time Picker & Capsule Mood Chips)
- **Tái Cấu Trúc Dải Chip Cảm Xúc Mobile & Khắc Phục Triệt Để Bug Đếm Số 0 (`static/css/layout.css`, `static/css/components.css`, `static/index.html`, `static/js/app.js`):**
  - Chuyển đổi dải chip trên Mobile từ dạng hình bầu dục méo mó sang thanh kẹo con nhộng (Horizontal Capsule/Pill) sang trọng: `.mobile-mood-scroll` (`overflow-x: auto; white-space: nowrap; scrollbar-width: none;`), `.mood-chip-pill` (`height: 36px; border-radius: 20px; white-space: nowrap; flex-shrink: 0; padding: 0 14px; font-size: 13px; font-weight: 600;`).
  - Badge số lượng `.mood-count-badge`: Viên nhộng nhỏ 18px (`min-width: 18px; height: 18px; border-radius: 10px; font-size: 11px;`), ẩn khi rỗng (`:empty { display: none !important; }`), đảm bảo hiển thị trên 1 dòng duy nhất `[Icon] [Tên Mood] [Số Lượng]`, triệt tiêu hoàn toàn rớt dòng chữ.
  - Sửa lỗi số đếm về 0: Khởi tạo badge rỗng trong HTML, hợp nhất cập nhật số đếm về một hàm SSoT duy nhất `updateMoodCountBadges(stats)` với fallback an toàn `(stats.moodCounts && stats.moodCounts[moodKey]) ? stats.moodCounts[moodKey] : 0`, gọi đồng bộ trong cả `loadStats()` và `loadEntries()`.
- **Xây Dựng Module Custom Date & Time Picker Độc Lập (`static/js/datetime-picker.js`, `app/routes/entry_routes.py`, `static/css/components.css`, `static/index.html`):**
  - Module `window.KokoroDateTimePicker` độc lập hoàn toàn, không nhồi nhét vào `editor.js`.
  - Giao diện kính mờ Soft Sakura gồm Mini Calendar chọn ngày, chuyển tháng trước/sau, bộ chọn Giờ (00-23) và Phút (00-59) cảm ứng, phím tắt "⏱️ Hiện tại" và nút "✨ Xác nhận".
  - Tích hợp trigger pill `📅 DD/MM/YYYY, HH:MM` ngay phía trên tiêu đề trong Editor Modal; tự động nạp thời gian khi sửa bài cũ.
  - Backend `app/routes/entry_routes.py`: Hỗ trợ `create_entry` và `update_entry` nhận `created_at` ISO-8601 tùy chỉnh từ client và lưu trực tiếp vào cột `created_at` trong PostgreSQL `entries`.
- **Bẻ Khóa God Component & Tái Cấu Trúc Kiến Trúc (Decoupling Architecture) (`static/js/toast.js`, `static/js/tag-manager.js`, `static/js/editor.js`, `static/js/app.js`):**
  - **Tách Toast Notification sang `static/js/toast.js` (`window.KokoroToast`):** Độc lập quản lý deduplication, giới hạn tối đa 2 toast, timer và animation Soft Sakura; `app.js` đóng vai trò coordinator ủy quyền.
  - **Tách Tag Management sang `static/js/tag-manager.js` (`window.KokoroTagManager`):** Độc lập quản lý gợi ý Quick Tag Chips trong Editor và Popular Tags Widget ở Desktop Sidebar; chuẩn hóa prefix `#` và đồng bộ highlight.
  - **Tinh Gọn `editor.js` & `app.js`:** `editor.js` chỉ giữ vai trò Form & Media Controller; `app.js` chỉ giữ vai trò App Coordinator điều phối Router Views và Auth.
- **Nâng Cấp Phiên Bản Hệ Thống Lên v1.5.4:**
  - Cập nhật `APP_VERSION = "v1.5.4"` trong `app/config.py`.
  - Cập nhật `CACHE_NAME = 'kokoro-v1.5.4'` và danh mục assets trong `static/sw.js`.
  - Nhúng các file script mới vào `index.html` kèm tham số chống cache `?v=1.5.4`.

## [1.5.3] - 2026-10-12
### Added & Fixed (Tag Management, Dynamic Category Synchronization & Lightbox Guard)
- **Khắc Phục Triệt Để Bug Ghost Lightbox Controls (`static/css/layout.css`, `static/css/components.css`):**
  - Khóa cứng thanh công cụ `#lightbox-controls-bar` ở trạng thái mặc định (khi modal đóng):
    `display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important;`.
  - Chỉ khi modal có class `.active` (`.lightbox-modal.active #lightbox-controls-bar`), thanh công cụ mới hiển thị:
    `display: flex !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;`.
  - Triệt tiêu 100% tình trạng thanh điều khiển phóng to ảnh nổi lơ lửng ở góc trên bên phải màn hình khi mở Editor Modal hoặc duyệt bài viết.
- **Nâng Cấp Lưới Thumbnail Preview Trong Editor (`static/css/components.css`, `static/css/layout.css`):**
  - Tái cấu trúc `.uploaded-previews-grid`: Tăng kích thước ô preview lên `minmax(96px, 1fr)` trên Mobile và `minmax(110px, 1fr)` trên Desktop, khoảng cách `gap: 12px`.
  - `.preview-thumb-box`: Bo góc `12px`, viền kính mờ tinh tế, đổ bóng nhẹ `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)`.
  - Nút xóa `✕` (`.preview-remove-btn`): Kích thước chuẩn 26x26px, đặt gọn gàng ở góc trên bên phải (`top: 6px; right: 6px;`), không che khuất trọng tâm ảnh.
  - Khung ảnh giữ nguyên `aspect-ratio: 1`, `object-fit: cover;`, hiển thị đầy đặn, không méo hình khi chọn nhiều ảnh cùng lúc.
- **Xây Dựng Hệ Thống Quản Lý & Gợi Ý Thẻ Chủ Đề (Tag Management & Quick Chips) (`app/routes/entry_routes.py`, `static/js/api.js`, `static/js/editor.js`, `static/index.html`):**
  - **Backend API:** Thêm endpoint `GET /api/tags` xác thực nghiêm ngặt theo `user_id`. Truy vấn bảng `tags`, `entry_tags` và `entries`, trả về danh sách thẻ chủ đề kèm số lượng bài viết (`usage_count`), sắp xếp giảm dần theo độ phổ biến (`ORDER BY usage_count DESC, t.name ASC`).
  - **Frontend Client:** Bổ sung phương thức `KokoroAPI.getTags()`.
  - **Editor Quick Chips:** Thêm vùng chứa chip `#editor-suggested-tags` ngay dưới `#editor-tag-input`. Khi mở Editor, tự động tải các tag của người dùng và render dạng chip nhanh kèm số bài viết. Bấm vào chip gợi ý sẽ toggle thêm/bớt tag trực tiếp vào ô nhập liệu và cập nhật highlight tức thì.
- **Đồng Bộ Động Số Lượng Danh Mục & Thẻ Chủ Đề Ngoài Trang Chủ (`static/js/app.js`, `static/index.html`):**
  - Xóa bỏ hoàn toàn các thẻ hashtag tĩnh và số đếm tĩnh hardcoded ở Sidebar Desktop và Mobile Chips.
  - Tự động đồng bộ số lượng bài viết lên các nút lọc Cảm xúc (Mood Filters) ở cả Desktop Sidebar và Mobile Chips: `Tất cả bài viết (N)`, `Thanh bình (N)`, `Ấm áp (N)`... từ PostgreSQL qua `KokoroAPI.getStats()`.
  - Tải danh sách tag từ `KokoroAPI.getTags()` và render động toàn bộ Widget "Thẻ chủ đề" (Popular Tags) ở Sidebar Desktop kèm số lượng bài tương ứng. Bấm vào thẻ chủ đề sẽ kích hoạt ngay bộ lọc bài viết theo tag đó.
- **Kiểm Thử & Xác Nhận Hệ Thống:**
  - Viết test suite tự động `tests/test_v153_tags_and_sync.py` kiểm tra xác thực, bảo mật cô lập tài khoản, sắp xếp `usage_count DESC`, và tăng/giảm đếm tag khi tạo/xóa bài viết — Kết quả: **PASS 100%**.
  - Toàn bộ regression suites (`test_v15_media_lifecycle.py`, `test_v14_features.py`, `test_audit_ios_update.py`) đạt **PASS 100%**.

## [1.5.2] - 2026-10-12
### Fixed & Hardened (iOS WebKit Service Worker Bypass & HEIC/HEIF Integration)
- **Bypass Triệt Để Service Worker Với Toàn Bộ API (`static/sw.js`):**
  - Chuyển toàn bộ request `/api/` sang chế độ Pure Native Bypass (`if (url.pathname.includes('/api/')) return;`), nhường 100% quyền xử lý cho native network fetch của trình duyệt.
  - Xóa bỏ hoàn toàn bug WebKit trên iOS Safari làm rỗng stream `multipart/form-data` của request PUT/POST khi bị proxy qua `event.respondWith()`.
  - Loại bỏ bẫy mã HTTP 200 OK giả mạo khi khối `catch` trong Service Worker vô tình nuốt lỗi kết nối.
  - Nâng cấp `CACHE_NAME` lên `kokoro-v1.5.2` và cập nhật query string `?v=1.5.2` cho toàn bộ tài nguyên tĩnh.
- **Hỗ Trợ Định Dạng Ảnh iPhone HEIC/HEIF Ở Frontend (`static/js/editor.js`, `static/index.html`):**
  - Khắc phục hiện tượng iOS Safari trả về `file.type = ""` cho file ảnh `.heic`/`.heif` bằng cách bổ sung kiểm tra phần mở rộng file (`.jpg`, `.jpeg`, `.png`, `.webp`, `.heic`, `.heif`).
  - Hiển thị placeholder biểu tượng camera thanh lịch kèm tên file và nút xóa `✕` cho ảnh HEIC trong trường hợp trình duyệt chưa hỗ trợ hiển thị Blob URL của file HEIC.
  - Cập nhật thuộc tính `accept="image/*,.heic,.heif,image/heic,image/heif"` trên `<input type="file">`.
- **Tích Hợp `pillow-heif` Ở Backend Cho Media Lifecycle (`app/services/media_service.py`):**
  - Cài đặt thư viện `pillow-heif` (v1.8.1) và tự động đăng ký `register_heif_opener()` khi nạp module.
  - Pillow hiện tự động giải mã và chuyển đổi trơn tru mọi ảnh chụp trực tiếp từ camera/thư viện iPhone (`.heic`, `.heif`) sang chuẩn `.webp` chất lượng cao kèm thumbnail 400px.
- **Thắt Chặt Toàn Vẹn Dữ Liệu PUT Entry (`app/routes/entry_routes.py`):**
  - Bổ sung Payload Integrity Guard trong `update_entry`: Nếu form nhận vào hoàn toàn trống trơn (do WebKit rỗng body hoặc request dị thường), server lập tức từ chối với lỗi `HTTP 400: Dữ liệu cập nhật không hợp lệ hoặc payload bị rỗng`.
  - Bảo đảm không bao giờ xảy ra tình trạng silent pass gán dữ liệu mặc định rỗng vào bài viết đã có dữ liệu.

## [1.5.1] - 2026-10-12
### Fixed & Hardened (iOS PWA & Media Lifecycle Hardening Release)
- **Triệt Tiêu Bug "Báo Cập Nhật Thành Công Nhưng Dữ Liệu & Ảnh Không Đổi" Trên iPhone (`app/routes/entry_routes.py`, `static/js/api.js`):**
  - **Backend Invariant:** Bổ sung kiểm tra nghiêm ngặt `if cur.rowcount == 0: return 404` trong `update_entry`, xóa bỏ hoàn toàn lỗ hổng silent pass khi ID hoặc `user_id` không khớp.
  - **Chống Aggressive Safari Caching:** Đính kèm header chống cache tuyệt đối (`Cache-Control: no-cache, no-store, must-revalidate, max-age=0`, `Pragma: no-cache`, `Expires: 0`) trên toàn bộ endpoint `GET /api/entries`, `GET /api/entries/{id}`, `GET /api/stats/summary`.
  - **Client Cache-Busting:** Bổ sung timestamp param `_t=${Date.now()}` và cấu hình `{ cache: 'no-store' }` vào fetch request trong `KokoroAPI.getEntries()`.
- **Dọn Dẹp Deadlock Offline Queue & Vòng Lặp 17 Lỗi 400 (`static/js/api.js`):**
  - Trong `syncOfflineQueue`: Tự động loại bỏ và xóa vĩnh viễn khỏi IndexedDB các bản ghi ngoại tuyến không hợp lệ khi server phản hồi mã lỗi `4xx` (Bad Request / Data error), chấm dứt triệt để vòng lặp gửi request lỗi liên thanh.
- **Khắc Phục Spam Toast "Thác Lũ" & Khóa Re-entrancy Form (`static/js/editor.js`, `static/js/app.js`, `static/css/glass.css`):**
  - **Re-entrancy Lock:** Thêm cờ `isSaving` vào `Editor.save()` ngăn chặn triệt để click đúp hoặc spam tap vào nút "Lưu bài viết" khi đang xử lý.
  - **Ép Commit Bàn Phím Ảo iOS:** Kích hoạt `document.activeElement?.blur()` trước khi đọc `.value` để ép bộ gõ tiếng Việt trên iOS Safari flush dữ liệu vào DOM.
  - **Thuật toán Toast Deduplication & Eviction:** Nâng cấp `showToast()` tự động phát hiện thông báo trùng nội dung (reset thời gian hiển thị, không nhân bản phần tử DOM) và giới hạn tối đa 2 Toast hiển thị đồng thời (tự động thu hồi Toast cũ nhất).
  - **Vị Trí Toast Thông Minh:** Trên mobile (`@media (max-width: 768px)`), đưa `.toast-container` lên phía trên đỉnh màn hình (`top: max(16px, env(safe-area-inset-top))`), không bao giờ che khuất cụm nút bấm ở đáy.
- **Khắc Phục Nút Bấm Dưới Đáy Modal Bị Cắt Xén Trên iPhone (`static/css/layout.css`):**
  - Tái cấu trúc `.editor-dialog` trên mobile: Khóa `overflow: hidden !important;`, `max-height: min(92dvh, calc(100dvh - 32px)) !important;`, loại bỏ double padding đáy.
  - Khóa `.editor-body`: `flex: 1 1 auto !important; overflow-y: auto !important; -webkit-overflow-scrolling: touch !important;`.
  - Khóa `.editor-footer`: `flex-shrink: 0 !important; padding: 14px 16px max(16px, env(safe-area-inset-bottom, 16px)) !important;` giúp cụm nút "Hủy bỏ" và "Lưu nhật ký" luôn nằm thoáng đãng phía trên thanh Home Indicator của iPhone.

## [1.5.0] - 2026-10-12
### Added & Refactored (Go-Live Readiness Release)
- **Hoàn Thiện Nghiệp Vụ Hình Ảnh & Media Lifecycle Đầy Đủ (`static/js/editor.js`, `app/routes/entry_routes.py`, `app/services/media_service.py`):**
  - Tái cấu trúc Data Model trong Editor: Quản lý tách bạch 3 tập dữ liệu `existingPhotos` (ảnh đã lưu từ server), `deletedPhotoIds` (danh sách ID ảnh cần xóa), và `selectedFiles` (ảnh mới chọn).
  - Quy chuẩn component thumbnail `.preview-thumb-box`: Khung vuông cố định `aspect-ratio: 1`, ảnh bên trong `object-fit: cover`, không cho phép bung kích thước container.
  - Bổ sung nút xóa nổi bật `.preview-remove-btn` (hình tròn nổi 28x28px, nền hồng ngọc gradient, viền trắng, icon `✕`) trên góc TẤT CẢ các ảnh thumbnail (cả ảnh cũ lẫn ảnh mới).
  - Backend nhận và parse `deleted_photo_ids` trong transaction nguyên tử: Xóa bản ghi trong bảng `entry_photos` và xóa sạch file vật lý `.webp` cùng `_thumb.webp` trong thư mục `uploads/` trên ổ cứng.
- **Triệt Tiêu Hoàn Toàn Lỗi Tràn Ngang Modal / Bottom Sheet Trên Mobile (`layout.css`, `components.css`):**
  - Thay thế toàn bộ `100vw` bằng `width: 100% !important; max-width: 100% !important; box-sizing: border-box !important;`.
  - Khóa cứng `overflow-x: hidden !important; overscroll-behavior: contain !important; touch-action: pan-y !important; min-width: 0 !important;` trên `.modal-overlay`, `.editor-dialog`, và `.editor-body`.
  - Chuẩn hóa lưới ảnh `.uploaded-previews-grid` với `display: grid; grid-template-columns: repeat(auto-fill, minmax(76px, 1fr)); gap: 10px; width: 100%; max-width: 100%;`.
  - Đảm bảo trên các màn hình Mobile (375x812 và 390x844): Modal đứng im tuyệt đối, không lộ bất kỳ mảng trống nào bên phải (`scrollWidth === innerWidth`).
- **Vá Lỗ Hổng Xác Thực & Cô Lập Dữ Liệu Đa Tài Khoản (`static/js/api.js`, `static/js/app.js`, `static/js/passcode.js`):**
  - Bắt buộc lưu kèm `user_id` vào từng bản ghi của hàng đợi ngoại tuyến `IndexedDB`.
  - Trong `syncOfflineQueue`: Chỉ đồng bộ các bài viết khớp với `currentUser.id`.
  - Khi đổi tài khoản (`onUserChanged`): Làm mới toàn bộ 4 views (Timeline, Calendar, Memories, Profile) và xóa trắng form Editor để không bị rò rỉ dữ liệu hoặc nháp của tài khoản trước.
  - Bảo mật PIN: Khi đang bật khóa PIN, chỉ gọi nạp dữ liệu bài viết vào DOM sau khi người dùng đã nhập đúng mã PIN trong phiên (`isUnlocked === true`).
- **Xử Lý Toàn Diện Ma Trận Edge Cases:**
  - Cho phép đăng bài viết chỉ có ảnh (nội dung chữ để trống nếu có ít nhất 1 ảnh đính kèm). Chỉ báo lỗi 400 khi cả chữ và ảnh đều rỗng.
  - Cho phép xóa sạch toàn bộ ảnh cũ trong bài viết, chuyển bài viết thành nhật ký thuần văn bản hợp lệ.
  - Dọn dẹp tags mồ côi: Tự động xóa các tag trong bảng `tags` không còn bài viết nào tham chiếu đến sau khi xóa/sửa bài.
- **Bộ Kiểm Thử Toàn Diện 100% PASS:**
  - `tests/test_v15_media_lifecycle.py`: 6 kịch bản kiểm thử xóa ảnh vật lý trên ổ đĩa và cập nhật DB pass 100%.
  - `tests/verify_mobile_editor_overflow.py`: Playwright kiểm thử viewport mobile (375x812 & 390x844) xác nhận 0px tràn ngang và nút xóa 28x28px hiển thị hoàn hảo.
  - Toàn bộ test hồi quy (`test_v14_features.py`, `test_auth_isolation.py`, `test_edit_and_ux.py`) đạt 100% PASS.

## [1.4.3] - 2026-10-12
### Fixed & Improved
- **Khắc Phục Triệt Để Bug Nút Profile Header Bị Đơ & Intercept Pointer Events (`components.css`, `layout.css`, `auth.js`, `app.js`):**
  - **Root Cause cốt lõi:** Cụm thanh công cụ phóng to `#lightbox-controls-bar` định vị ở góc trên bên phải (`top: max(16px...), right: max(16px...)`) trước đó được gán `pointer-events: auto !important` ngay cả khi Lightbox đang đóng (`opacity: 0`), dẫn đến việc toàn bộ click vào Profile Pill ("Nguyễn Thành Long") bị phần tử vô hình này nuốt mất sự kiện.
  - Sửa đổi: Đưa `.lightbox-modal` khi không kích hoạt về `display: none !important; visibility: hidden !important; pointer-events: none !important;`, chỉ kích hoạt `pointer-events: auto !important` khi có class `.active`.
  - Triệt tiêu hoàn toàn các listener trực tiếp gây xung đột và `stopPropagation()` cục bộ trong `static/js/auth.js`, chuyển 100% sang Event Delegation duy nhất tại `document` trong `static/js/app.js` (SSoT).
- **Bổ Sung Nút Chế Độ Đêm / Ngày Vào Profile Dropdown Menu (`index.html`, `app.js`):**
  - Tích hợp thêm mục "Chế độ Đêm / Ngày" (`#dropdown-theme-toggle-btn`) vào menu thả xuống, đồng bộ trạng thái icon và badge (Sáng / Tối) theo thời gian thực.
  - Menu chứa đầy đủ 4 nhóm chức năng cốt lõi: Bảo mật mã PIN, Đêm/Ngày, Sao lưu/Khôi phục, Đăng xuất.
- **Tối Ưu Hóa Logic Tách Tên Xưng Hô Friendly Greeting Banner (`app.js`):**
  - Ưu tiên các trường `nickname` / `preferredName` / `preferred_name` nếu có.
  - Tự động lọc bỏ các chú thích trong ngoặc đơn như `(心)`, `(Zen)` và lấy chính xác từ cuối cùng trong chuỗi họ tên (ví dụ: "Nguyễn Thành Long" -> "Chào Long, hôm nay bạn cảm thấy thế nào? 🌸").
- **Kiểm Thử Tự Động Playwright E2E:**
  - Script `tests/verify_profile_dropdown.py` kiểm thử 100% PASS từ click pill, assert menu hiển thị, đầy đủ 4 mục menu, đóng khi click outside, và chụp ảnh bằng chứng `desktop_profile_dropdown_open.png`.
- **Tăng Phiên Bản Hệ Thống Lên `v1.4.3`:**
  - Cập nhật `sw.js` (CACHE_NAME = `kokoro-v1.4.3`), `app/config.py`, và query string chống cache `?v=1.4.3` cho toàn bộ CSS/JS.
- **Header Profile Pill Dropdown Event Delegation (`static/js/app.js` & CSS):**
  - Chuyển toàn bộ cơ chế lắng nghe sự kiện click mở Dropdown sang Event Delegation cấp `document`, triệt tiêu hoàn toàn lỗi mất listener khi render lại user info động.
  - Thiết lập thuộc tính `z-index: 9999 !important; pointer-events: auto !important;` cho `.profile-dropdown-menu`, đảm bảo `.app-header` và `#user-profile-container` có `overflow: visible !important`.
  - Tự động đóng dropdown khi click ra ngoài hoặc khi nhấp vào bất kỳ tùy chọn nào bên trong.
- **Tinh Chỉnh Logic Tách Tên Xưng Hô Thân Mật (`static/js/app.js`):**
  - Tách lấy từ cuối cùng trong chuỗi họ tên (ví dụ: "Nguyễn Thành Long" -> "Chào Long") và loại bỏ phần chú thích trong ngoặc đơn như `(心)`, `(Zen)`.
- **Cố Định Layout Desktop 3 Cột Bất Biến & Ẩn FAB Nổi (`layout.css`, `components.css`):**
  - Khóa cứng bố cục `300px minmax(520px, 1fr) 320px` trên Desktop (`> 1024px`), triệt tiêu hoàn toàn 5 cột trụ dọc và ẩn nút FAB nổi đè bài viết.
  - Tăng phiên bản `CACHE_NAME` lên `kokoro-v1.4.2` và query param `?v=1.4.2` trên toàn bộ assets.

---

## [1.4.1] - 2026-10-12
### Fixed & Improved
- **PWA Service Worker Cache-Busting & Clean Activation (`static/sw.js` & `static/index.html`):**
  - Tăng phiên bản `CACHE_NAME` lên `kokoro-v1.4.1`.
  - Tự động xóa sạch toàn bộ cache cũ trong sự kiện `activate` và gọi `self.skipWaiting()` + `self.clients.claim()`.
  - Gắn query param chống cache `?v=1.4.1` cho toàn bộ thẻ `<script>` (`lightbox.js`, `app.js`, `editor.js`...) và `<link>` CSS (`components.css`, `layout.css`...) trong `index.html`.
  - Bổ sung `reg.update()` trong `pwa.js` để kích hoạt kiểm tra cập nhật Service Worker chủ động ngay khi mở web.
- **Tương Tác Lightbox Cảm Ứng & Phóng To Trực Quan (`lightbox.js`, `components.css`, `layout.css`):**
  - Gắn thuộc tính bắt buộc cho ảnh `#lightbox-img`: `touch-action: none !important`, `user-select: none !important`, `transition: transform 0.1s ease-out`.
  - Đăng ký sự kiện Touch chuẩn Mobile với `{ passive: false }` và gọi `e.preventDefault()` khi phát hiện cử chỉ 2 ngón (Pinch-to-Zoom) hoặc đang kéo ảnh khi phóng to (Pan), ngăn chặn triệt để tình trạng trình duyệt nuốt mất cử chỉ.
  - Nâng cấp cụm nút bấm điều khiển nổi (`#lightbox-controls-bar`): Đảm bảo `z-index: 10000 !important` luôn nổi trên cùng; hỗ trợ các nấc zoom mượt mà theo bậc: `[+]` (1.5x -> 2.0x -> 2.5x -> 3.0x -> 3.5x), `[-]` (thu nhỏ theo bậc), `[↺]` (reset về 1.0x tâm giữa), và `[✕]` (đóng ảnh).
  - Tích hợp chốt chống gán sự kiện lặp (`this.initialized`) trong `Lightbox.init()`.

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
