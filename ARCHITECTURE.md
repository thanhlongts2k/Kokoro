# ARCHITECTURE.md — Kiến Trúc Hệ Thống Kokoro (心)

> **Single Source of Truth (SSoT)**: Tài liệu đặc tả kỹ thuật kiến trúc, mô hình dữ liệu, phân tầng hệ thống và quy chuẩn thiết kế của ứng dụng **Kokoro — Personal Diary & Photo Journal PWA**.

---

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

- **Tên dự án:** Kokoro (心) — Sổ tay nhật ký cảm xúc & lưu trữ khoảnh khắc cá nhân.
- **Mô hình hoạt động:** Ứng dụng Web PWA Fullstack chạy trực tiếp trên máy chủ cục bộ (Local Server) tại cổng `5050`, phục vụ truy cập qua mạng nội bộ hoặc qua Nginx Reverse Proxy (domain/tunnel).
- **Trọng tâm sản phẩm:**
  1. Ghi chép nhật ký văn bản giàu cảm xúc (hỗ trợ Markdown/Rich text, gắn Mood, Thời tiết, Tags).
  2. Tải và quản lý album ảnh chất lượng cao (nén ảnh WebP thông minh, tạo thumbnail nhanh bằng Pillow).
  3. Trải nghiệm PWA di động mượt mà (cài đặt lên màn hình chính iOS/Android, hỗ trợ offline draft, service worker caching).
  4. Xác thực bảo mật bằng tài khoản Google (Google Identity Services OAuth 2.0 kèm Mock Auth trong dev).
  5. Giao diện thẩm mỹ cao phong cách **Soft Sakura Pastel / Healing Light Frosted Glassmorphism** (Hồng nhẹ êm dịu, phong cách chữa lành Á Đông).

---

## 2. KIẾN TRÚC PHÂN TẦNG (LAYERED ARCHITECTURE)

```
┌──────────────────────────────────────────────────────────────┐
│                    KOKORO CLIENT (PWA)                       │
│  HTML5 + Vanilla CSS Soft Sakura Glass + Modular ES6 JS      │
│  Service Worker (Cache & Offline Drafts) + Manifest          │
└───────────────────────────────┬──────────────────────────────┘
                                │ HTTP / JSON REST API (Port 5050)
┌───────────────────────────────▼──────────────────────────────┐
│                  KOKORO BACKEND (STARLETTE)                  │
│  ASGI Server (Uvicorn) - Port 5050                           │
│  ├─ Auth Middleware (Google Token & Dev Mock Auth)           │
│  ├─ Routers: /api/auth, /api/entries, /api/categories,       │
│  │           /api/tags, /api/stats, /api/maintenance         │
│  ├─ Domain Services: MediaService (Pillow WebP/Thumbnails)   │
│  ├─ Schemas / DTOs: Typed dataclasses (app/schemas/*)        │
│  │   (CategoryDTO, TagDTO, StatsDTO, UserDTO, EntryDTO)      │
│  └─ Repositories: DAO Layer Isolation (app/repositories/*)   │
│      (EntryRepository, UserRepository, CategoryRepository,   │
│       TagRepository, StatsRepository, PhotoRepository)       │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                    DATA & STORAGE LAYER                      │
│  ├─ PostgreSQL 18 (ThreadedConnectionPool, kokoro_db)        │
│  └─ File Storage: /uploads/ (originals & thumbnails)         │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. THIẾT KẾ GIAO DIỆN & HỆ THỐNG TOKENS (UI DESIGN SYSTEM)

### 3.1. Triết lý Thiết kế: Soft Sakura Healing (Phong cách Chữa lành)
Giao diện ứng dụng bám sát phong cách **Soft Sakura Pastel / Light Frosted Glassmorphism**:
- Nền ấm áp, thư thái với sắc hồng phấn dịu nhẹ và ánh ngọc trai (`#fff5f7` đến `#fdf2f4`).
- Các tấm thẻ (Cards) làm từ kính mờ bán trong suốt (`backdrop-filter: blur(16px)`), viền hồng phấn phát quang nhẹ nhàng (`rgba(244, 114, 182, 0.2)`).
- Chữ màu xám than thanh lịch (`#334155`), độ tương phản vừa phải, dịu mắt, hoàn toàn không gây chói hoặc nặng nề.
- Hiệu ứng chuyển động mượt mà (micro-interactions, soft hover lift, sakura petal glow).

### 3.2. Bảng Màu (Color Palette - Soft Sakura Theme)
- **Background Ambient:** `#fff5f7` (Soft Rose Mist) đến `#fdf2f4` (Sakura Petal Tint)
- **Surface Glass:** `rgba(255, 255, 255, 0.78)` (Frosted White Glass, Blur 16px)
- **Glass Border:** `rgba(244, 114, 182, 0.22)` (Subtle Sakura Glow Border)
- **Glass Shadow:** `0 8px 32px rgba(244, 114, 182, 0.08)` (Soft Rosy Ambient Shadow)
- **Accent Primary (Sakura Rose):** `#f472b6` / `#fb7185` (Hồng phấn hoa anh đào)
- **Accent Secondary (Warm Amber):** `#f59e0b` (Ánh nắng hoàng hôn)
- **Accent Serene (Matcha Green):** `#10b981` (Xanh trà thanh tịnh)
- **Accent Lavender:** `#a855f7` (Tím nhạt chiêm nghiệm)
- **Text Primary:** `#1e293b` (Slate Dark dịu mắt)
- **Text Secondary:** `#475569` (Slate Muted)
- **Text Light / Subtle:** `#94a3b8`

### 3.3. Các Màn hình & Thành phần Cốt lõi (Screens & Components)
1. **Header Bar:** Logo Kokoro (心) kèm biểu tượng hoa anh đào Sakura, Bộ lọc theo dòng thời gian, Nút tìm kiếm, Avatar người dùng & Trạng thái kết nối PWA.
2. **Timeline Feed (Dòng thời gian):** Danh sách các thẻ nhật ký được sắp xếp theo ngày/tháng với trục thời gian hồng phấn (Pink timeline line), hiển thị ảnh lưới, mood tags, trích đoạn.
3. **Calendar View (Lịch kỷ niệm):** Lịch trực quan hiển thị các chấm màu hoa anh đào trên từng ngày đã viết nhật ký.
4. **Rich Diary Editor (Trình soạn thảo):**
   - Tiêu đề & Nội dung đa dòng tự co giãn.
   - Bộ chọn cảm xúc nhanh (Mood selector: Serene 🌸, Energetic ⚡, Reflective 🌙, Grateful 🍵, Melancholy 🌧️).
   - Khung kéo thả tải nhiều ảnh, xem trước ảnh tức thì và sắp xếp thứ tự.
   - Thẻ gắn Tag linh hoạt (`#healing`, `#spring`, `#memories`...).
5. **Photo Lightbox Modal:** Trình xem ảnh toàn màn hình với hiệu ứng mờ nền kính Sakura.

---

## 4. MÔ HÌNH DỮ LIỆU (DATABASE SCHEMA - POSTGRESQL)

Cơ sở dữ liệu cục bộ: **`kokoro_db`** (Port `5432`).

### 4.1. Bảng `users`
| Cột | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `id` | SERIAL PRIMARY KEY | Khóa chính |
| `google_id` | VARCHAR(255) UNIQUE NOT NULL | Mã ID duy nhất Google |
| `email` | VARCHAR(255) UNIQUE NOT NULL | Email người dùng |
| `name` | VARCHAR(255) NOT NULL | Tên hiển thị người dùng |
| `avatar_url` | TEXT | Đường dẫn ảnh đại diện |
| `created_at` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian tạo tài khoản |
| `last_login` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian đăng nhập gần nhất |

### 4.2. Bảng `entries`
| Cột | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `id` | SERIAL PRIMARY KEY | Khóa chính |
| `user_id` | INT NOT NULL REFERENCES users(id) ON DELETE CASCADE | Khóa ngoại người dùng |
| `title` | VARCHAR(255) | Tiêu đề bài viết |
| `content` | TEXT NOT NULL | Nội dung nhật ký |
| `mood` | VARCHAR(50) DEFAULT 'serene' | Cảm xúc (serene, energetic, reflective...) |
| `weather` | VARCHAR(50) DEFAULT 'sunny' | Thời tiết (sunny, rainy, cloudy, windy...) |
| `entry_date` | DATE NOT NULL DEFAULT CURRENT_DATE | Ngày ghi nhật ký (YYYY-MM-DD) |
| `is_pinned` | BOOLEAN DEFAULT FALSE | Ghim bài lên đầu dòng thời gian |
| `created_at` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian tạo bản ghi |
| `updated_at` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật sau cùng |

### 4.3. Bảng `entry_photos`
| Cột | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `id` | SERIAL PRIMARY KEY | Khóa chính |
| `entry_id` | INT NOT NULL REFERENCES entries(id) ON DELETE CASCADE | Khóa ngoại bài nhật ký |
| `file_path` | TEXT NOT NULL | Đường dẫn file ảnh gốc |
| `thumb_path` | TEXT NOT NULL | Đường dẫn file ảnh thu nhỏ (WebP) |
| `file_name` | VARCHAR(255) NOT NULL | Tên file hiển thị |
| `file_size` | INT NOT NULL | Dung lượng file (bytes) |
| `width` | INT | Chiều rộng ảnh (px) |
| `height` | INT | Chiều cao ảnh (px) |
| `sort_order` | INT DEFAULT 0 | Thứ tự hiển thị trong album |
| `created_at` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian tải lên |

### 4.5. Bảng `categories` (v1.6.0 — Quản Lý Danh Mục & Moods Động)
| Cột | Kiểu | Mô tả |
| :--- | :--- | :--- |
| `id` | SERIAL PRIMARY KEY | Khóa chính |
| `user_id` | INT NOT NULL REFERENCES users(id) ON DELETE CASCADE | Khóa ngoại người dùng sở hữu |
| `name` | VARCHAR(100) NOT NULL | Tên danh mục/mood (Bình yên, Ấm áp, Hạnh phúc...) |
| `icon` | VARCHAR(50) DEFAULT '📁' | Biểu tượng icon emoji (🌸, ☕, 🌙, 🍵, ⚡, 🥰...) |
| `color` | VARCHAR(50) DEFAULT '#ec4899' | Mã màu sắc pastel nhận diện |
| `sort_order` | INT DEFAULT 0 | Thứ tự sắp xếp hiển thị |
| `created_at` | TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP | Thời gian khởi tạo |
| *Ràng buộc* | `UNIQUE (user_id, name)` | Chống trùng lặp tên danh mục trong cùng tài khoản |

*Khóa ngoại mở rộng:* Bảng `entries` có thêm cột `category_id INT REFERENCES categories(id) ON DELETE SET NULL` (khi xóa danh mục, bài viết tự động chuyển về chưa phân loại, tuyệt đối không bị xóa mất).

---

## 5. ĐẶC TẢ API (REST API SPECIFICATION)

### 5.1. Authentication (`/api/auth`)
- `POST /api/auth/google`: Nhận Google ID Token (`credential`), xác thực qua Google Auth Library, tìm hoặc tạo User, trả về JWT Session Cookie / Bearer Token.
- `GET /api/auth/me`: Lấy thông tin user hiện tại và phiên làm việc.
- `POST /api/auth/logout`: Xóa phiên đăng nhập.
- `GET /api/auth/config`: Cung cấp cấu hình auth công khai (`google_client_id`, `mock_auth`, `version`).
- `GET /api/auth/mock-users` & `POST /api/auth/mock-login`: Chỉ khả dụng khi `MOCK_AUTH=True` cho môi trường dev/testing; được bảo vệ nghiêm ngặt bằng rào chắn Privacy Guard (chỉ truy vấn/cho phép đăng nhập với tài khoản có `google_id LIKE 'mock_%' OR email LIKE '%@kokoro.me'`, trả về `403 Forbidden` khi `MOCK_AUTH=False` và chặn tuyệt đối việc để lộ hoặc đăng nhập vào tài khoản cá nhân thật).

### 5.2. Diary Entries (`/api/entries`)
- `GET /api/entries`: Danh sách bài viết (hỗ trợ lọc theo `category_id`, `mood`, `tag`, `month`, `search`).
- `POST /api/entries`: Tạo bài viết mới kèm `category_id`, `weather`, ảnh và tags (trả về HTTP 201 Created).
- `GET /api/entries/{id}`: Xem chi tiết bài viết kèm toàn bộ ảnh và thông tin danh mục liên kết.
- `PUT /api/entries/{id}`: Cập nhật nội dung, cảm xúc, thời tiết (`weather`), danh mục, ngày viết và ảnh.
- `DELETE /api/entries/{id}`: Xóa bài viết và giải phóng các file ảnh liên quan.
- `GET /api/entries/export`: Xuất tệp sao lưu JSON chuẩn v1.1 bao gồm toàn bộ danh mục tùy chỉnh (`categories`) và bài viết.
- `POST /api/entries/import`: Khôi phục dữ liệu từ tệp sao lưu JSON kèm ánh xạ danh mục, tương thích ngược 100% với tệp v1.0 cũ.

### 5.3. Categories & Dynamic Moods (`/api/categories` - v1.6.0)
- `GET /api/categories`: Lấy danh sách danh mục/moods của user kèm số lượng bài viết (`usage_count`).
- `POST /api/categories`: Tạo danh mục mới (validate tên không rỗng, kiểm tra trùng lặp).
- `PUT /api/categories/{id}`: Cập nhật tên, icon, màu sắc và tự động đồng bộ `entries.mood`.
- `DELETE /api/categories/{id}`: Xóa danh mục an toàn, tự động set `entries.category_id = NULL`.

### 5.4. Tags Management (`/api/tags` - v1.6.0)
- `GET /api/tags`: Lấy danh sách toàn bộ tag của user kèm `usage_count`.
- `POST /api/tags`: Chủ động tạo thẻ mới trước khi viết bài (chuẩn hóa `#tag`).
- `PUT /api/tags/{id}`: Đổi tên thẻ (tự động gộp nếu trùng thẻ đích).
- `DELETE /api/tags/{id}`: Xóa thẻ.
- `DELETE /api/tags/cleanup-orphans`: Dọn dẹp tất cả thẻ có `usage_count = 0`.

### 5.5. Media Upload (`/api/media`)
- `POST /api/media/upload`: Tải lên 1 hoặc nhiều ảnh (Multipart Form), nén WebP và tạo thumbnail.
- `GET /uploads/{filename}`: Phục vụ xem ảnh gốc hoặc thumbnail.

### 5.6. Statistics (`/api/stats`)
- `GET /api/stats/summary`: Thống kê tổng số ngày viết, chuỗi liên tiếp (streak), biểu đồ phân bổ tâm trạng (Mood breakdown).

### 5.7. System Maintenance & Cleanup (`/api/maintenance` - v1.6.4)
- `POST /api/maintenance/cleanup-orphaned-media`: Quét và dọn sạch các tệp ảnh mồ côi trên đĩa (`uploads/originals/`, `uploads/thumbnails/`) không có bản ghi trong bảng `entry_photos`. Hỗ trợ Grace Period an toàn (mặc định 2 giờ) bảo vệ các ảnh bản nháp đang soạn thảo; chuẩn hóa so sánh theo tên file thuần túy chống bẫy đường dẫn Windows.


---

## 6. QUY CHUẨN PWA (PROGRESSIVE WEB APP SPECIFICATION)

1. **Manifest File (`manifest.webmanifest`):**
   - `name`: "Kokoro — Nhật Ký Cảm Xúc"
   - `short_name`: "Kokoro"
   - `start_url`: "/"
   - `display`: "standalone"
   - `background_color`: "#fff5f7"
   - `theme_color`: "#fdf2f4"
   - `icons`: Đầy đủ kích thước 192x192 và 512x512 maskable icon.
2. **Service Worker (`sw.js`):**
   - Cache-First đối với assets tĩnh (HTML, CSS, JS, Fonts, Icons).
   - Network-First đối với API calls, fallback về cache nếu mất mạng.
   - Lưu trữ bản nháp nhật ký offline vào `localStorage` / `IndexedDB` để chống mất dữ liệu khi gián đoạn mạng.

---

## 7. GỢI Ý SUY NGẪM CHÁNH NIỆM MỖI NGÀY (DAILY ZEN PROMPT ENGINE - v1.6.2)

1. **Kho tàng 36 câu hỏi gợi ý chánh niệm (`static/js/zen-prompts.js`):**
   - 100% Offline-First, không phụ thuộc mạng hay máy chủ backend.
   - Phân bổ cân bằng trên 4 trụ cột cảm xúc: Biết ơn & Giản dị (🍵 Gratitude), Buông bỏ & Tự trắc ẩn (🌙 Letting Go), Hiện diện & Chiêm nghiệm (🌸 Presence), Ước vọng & Năng lượng (⚡ Growth).
2. **Thuật toán tạo Seed ngày cục bộ tất định (Deterministic Local Date Seed):**
   - Sử dụng ngày cục bộ máy client (`getLocalDateString()`) tránh triệt để lỗi chuyển ngày sớm do lệch múi giờ UTC.
   - Hàm băm 32-bit `hashDate()` ánh xạ ngày sang chỉ số câu hỏi duy nhất trong ngày, đổi mới lúc 00:00 đêm.
   - Nút xúc xắc 🎲 (`getRandomPrompt()`) hỗ trợ đổi câu hỏi ngẫu nhiên và lưu trạng thái vào `localStorage`.
3. **Quy chuẩn Bảo vệ Bản nháp (Draft Safety Protocol):**
   - Khi chèn câu hỏi vào Editor (`insertZenPrompt`), hệ thống bảo toàn 100% nội dung bản nháp đã có bằng cách chèn trích dẫn Markdown `> 🌸 "${promptText}"\n\n` lên đầu bài viết thay vì ghi đè.
   - Tự động đặt con trỏ chuột (`setSelectionRange`) ngay sau câu trích dẫn để người dùng viết tiếp tự nhiên.
   - Tự động map và kích hoạt danh mục cảm xúc đề xuất (`suggestedMood`).
4. **Bộ nhớ trạng thái & Thu gọn thẻ:**
   - Hỗ trợ đóng/thu gọn thẻ hôm nay với khóa lưu trữ `kokoro_zen_dismissed_${today}`, tự động hiển thị lại khi sang ngày mới.

---

## 8. XUẤT THẺ ẢNH KỶ NIỆM CANVAS (DAILY CARD EXPORT ENGINE - v1.6.3)

1. **Khóa cứng bộ đệm 1080p (Fixed 1080p Canvas Buffer):**
   - Tỷ lệ Vuông (1:1): `1080 × 1080 px` (Instagram/Facebook Feed).
   - Tỷ lệ Dọc (9:16): `1080 × 1920 px` (Instagram/TikTok/Facebook Story).
   - Tuyệt đối không nhân `devicePixelRatio` vào buffer vật lý để phòng ngừa vượt giới hạn 16.7 triệu pixel gây crash Safari trên iOS.
   - Preview trên giao diện điều tiết mượt mà qua CSS responsive (`max-width: 340px`).
2. **Cổng chặn font async & Bẻ dòng thông minh (`wrapAndFitText`):**
   - Đảm bảo `await document.fonts.ready` trước khi kết xuất để chữ tiếng Việt và emoji không bị vỡ layout hay lỗi ô vuông.
   - Thuật toán bẻ dòng tách đoạn văn `\r?\n` trước khi chia từ, bảo toàn nhịp điệu bài viết và ngắt dòng thơ; tự động cắt tỉa và chèn `"..."` an toàn khi vượt quá chiều cao khả dụng.
3. **Bố cục thích ứng (Adaptive Layout):**
   - Thẻ thuần chữ: Bố cục Zen Quote thanh thoát, font lớn, biểu tượng đóa hoa anh đào chìm nghệ thuật.
   - Thẻ có ảnh: Khung ảnh bo tròn tinh tế (hỗ trợ badge `+X ảnh` nếu có nhiều ảnh) kết hợp tiêu đề & trích đoạn hài hòa.
4. **Instant Web Share API & Quản trị Bộ nhớ RAM:**
   - Tiền tạo sẵn Blob/File (`currentExportFile`) ngay sau khi render xong preview để gọi `navigator.share({ files })` ngay trong User Gesture (tránh `NotAllowedError` trên iOS Safari).
   - Thu hồi tài nguyên tức thì `URL.revokeObjectURL(activeBlobUrl)` và reset kích thước canvas khi đóng modal.

---

## 9. KIẾN TRÚC CLEAN ARCHITECTURE & PHÂN TẦNG REPOSITORY (GIAI ĐOẠN 1-3)

1. **Nguyên tắc Phân tầng & Cô lập Tầng Dữ liệu (Layer Isolation):**
   - **Routers / Controllers (`app/routes/*`):** 100% không chứa raw SQL. Chỉ tiếp nhận HTTP request, parse/validate DTO, điều phối gọi Service/Repository, và trả về `JSONResponse`.
   - **Repositories (`app/repositories/*`):** Đóng gói toàn bộ thao tác truy vấn CSDL PostgreSQL (`psycopg2`), quản lý transaction atomicity, chống race condition và map kết quả trả về typed DTO hoặc dict chuẩn.
   - **Schemas / DTOs (`app/schemas/*`):** Định nghĩa cấu trúc dữ liệu tường minh bằng Python typed dataclass, triệt tiêu hoàn toàn `dict[str, Any]` thô không kiểm soát kiểu.
2. **Hệ thống Repositories Độc lập:**
   - `EntryRepository`: Quản lý toàn bộ nghiệp vụ bài viết (lọc theo mood/tag/category/thời gian, chi tiết, thêm mới atomic kèm tags & ảnh, cập nhật kèm dọn ảnh thừa, xóa, ghim, export/import JSON backup).
   - `UserRepository`: Quản lý danh sách người dùng, session token, lấy user đầu tiên và upsert Google ID / mock profile.
   - `CategoryRepository`: Quản lý danh mục bài viết (tạo, cập nhật, xóa an toàn với `ON DELETE SET NULL`).
   - `TagRepository`: Quản lý thẻ hashtag bài viết và auto-complete.
   - `StatsRepository`: Tính toán thống kê cảm xúc, chuỗi ngày viết, và tổng số bài viết.
   - `PhotoRepository`: Quản lý ảnh đính kèm bài viết, truy vấn đường dẫn phục vụ dọn dẹp ảnh mồ côi.
3. **Quy chuẩn Dung lượng Controller (< 300 Lines):**
   - God-file `entry_routes.py` (từng chiếm 1.568 dòng) đã được tái cấu trúc thành công xuống còn **291 dòng code**, đạt chuẩn Single Responsibility và dễ dàng bảo trì mở rộng lâu dài.

---

## 10. KIẾN TRÚC ĐIỀU HƯỚNG & PHÂN TẦNG HIỂN THỊ FRONTEND (v1.7.0 MODULAR ARCHITECTURE)

1. **Bộ Điều Phối Trung Tâm & Điều Hướng (`static/js/app.js` < 400 dòng):**
   - Đóng vai trò Bootstrapper & Routing Orchestrator duy nhất, liên kết các module hiển thị độc lập:
     * `timeline-feed.js`: Timeline Feed, Photo Mosaic, Progressive Pagination (15 items/lần).
     * `calendar-view.js`: Mini & Full Calendar Grid, phép tính ngày `isSameDay`, lọc bài theo ngày.
     * `memories-view.js`: Album ảnh kỷ niệm, Lightbox kết nối, bộ lọc thẻ/cảm xúc.
     * `profile-stats.js`: Trang cá nhân, chuỗi streak liên tục (`calculateStreak`), biểu đồ tâm trạng.
   - **Cơ chế Event Delegation Đa Nền Tảng (Cross-platform Navigation Contract):**
     * Desktop Navigation: Tương thích cả `[data-switch-view]` và `[data-view-target]`.
     * Mobile Navigation: Lắng nghe `.bottom-nav-item[data-tab]`.
     * Profile Dropdown Menu: Lắng nghe `#user-profile-pill` và điều hướng nội bộ từ `#dropdown-profile-view-btn`.
     * View Container: Đồng bộ chuyển đổi trạng thái hiển thị giữa `.c-view` và `.app-view`.
2. **Chiến Lược Bộ Nhớ Đệm & Invalidation (`static/sw.js`):**
   - Service Worker Cache-First đối với static assets, tích hợp cơ chế chủ động kiểm tra cập nhật `reg.update()`.
   - Mỗi lần cập nhật logic giao diện, `sw.js` mang dấu vết phiên bản để ép trình duyệt nạp lại mã nguồn mới nhất mà không gây xung đột cache cục bộ.
3. **Hợp Đồng Phản Hồi API & Vòng Đời Phiên Đăng Nhập (API Response Contracts & Session Lifecycle):**
   - **Quy chuẩn khóa phản hồi REST API (Response Payload Contract):**
     * `GET /api/entries`: Bắt buộc trả về `{ "status": "success", "entries": [...] }`.
     * `GET /api/categories`: Bắt buộc trả về `{ "status": "success", "categories": [...] }`.
     * `GET /api/stats/summary`: Trả về phẳng `{ "status": "success", "totalEntries": N, ... }`.
     * **Client Invariant:** Mã nguồn `static/js/app.js` luôn sử dụng biểu thức fallback an toàn `res.entries || res.data` và `res.categories || res.data`, triệt tiêu hoàn toàn rủi ro gán nhầm mảng rỗng (`[]`) làm ẩn bài viết của người dùng.
   - **Vòng đời chuyển đổi tài khoản (`onUserChanged`):**
     * Khi người dùng đăng nhập Google hoặc chọn tài khoản, `auth.js` kích hoạt sự kiện `window.KokoroApp.onUserChanged(user)`.
     * Ứng dụng tự động kích hoạt nạp lại song song 4 luồng dữ liệu (`loadCategories`, `loadEntries`, `loadStats`, `loadPopularTags`) phân tách theo `user_id`, bảo đảm dữ liệu cá nhân hóa hiển thị tức thì và cô lập 100%.


