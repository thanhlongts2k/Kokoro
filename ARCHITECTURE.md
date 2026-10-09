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
│  ├─ API Endpoints (/api/auth, /api/entries, /api/media)      │
│  └─ Media Processing Engine (Pillow: WebP/Thumbnail)         │
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

### 4.4. Bảng `tags` & `entry_tags`
- `tags`: `id SERIAL PRIMARY KEY`, `user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE`, `name VARCHAR(100) NOT NULL`, `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`, `UNIQUE (user_id, name)`.
- `entry_tags`: `entry_id INT NOT NULL REFERENCES entries(id) ON DELETE CASCADE`, `tag_id INT NOT NULL REFERENCES tags(id) ON DELETE CASCADE`, `PRIMARY KEY (entry_id, tag_id)`.

---

## 5. ĐẶC TẢ API (REST API SPECIFICATION)

### 5.1. Authentication (`/api/auth`)
- `POST /api/auth/google`: Nhận Google ID Token (`credential`), xác thực qua Google Auth Library, tìm hoặc tạo User, trả về JWT Session Cookie / Bearer Token.
- `GET /api/auth/me`: Lấy thông tin user hiện tại và phiên làm việc.
- `POST /api/auth/logout`: Xóa phiên đăng nhập.

### 5.2. Diary Entries (`/api/entries`)
- `GET /api/entries`: Danh sách bài viết (hỗ trợ phân trang `page`, `limit`, lọc theo `mood`, `tag`, `month`, `search`).
- `POST /api/entries`: Tạo bài viết mới kèm danh sách ảnh và tags.
- `GET /api/entries/{id}`: Xem chi tiết bài viết kèm toàn bộ ảnh.
- `PUT /api/entries/{id}`: Cập nhật nội dung, cảm xúc, ngày viết và danh sách ảnh.
- `DELETE /api/entries/{id}`: Xóa bài viết và giải phóng các file ảnh liên quan.

### 5.3. Media Upload (`/api/media`)
- `POST /api/media/upload`: Tải lên 1 hoặc nhiều ảnh (Multipart Form), nén WebP và tạo thumbnail.
- `GET /uploads/{filename}`: Phục vụ xem ảnh gốc hoặc thumbnail.

### 5.4. Statistics (`/api/stats`)
- `GET /api/stats/summary`: Thống kê tổng số ngày viết, chuỗi liên tiếp (streak), biểu đồ phân bổ tâm trạng (Mood breakdown).

---

## 6. QUY CHUẨN PWA (PROGRESSIVE WEB APP SPECIFICATION)

1. **Manifest File (`manifest.webmanifest`):**
   - `name`: "Kokoro — Nhật Ký Cảm Xúc"
   - `short_name`: "Kokoro"
   - `start_url`: "/"
   - `display`: "standalone"
   - `background_color`: "#080b11"
   - `theme_color`: "#080b11"
   - `icons`: Đầy đủ kích thước 192x192 và 512x512 maskable icon.
2. **Service Worker (`sw.js`):**
   - Cache-First đối với assets tĩnh (HTML, CSS, JS, Fonts, Icons).
   - Network-First đối với API calls, fallback về cache nếu mất mạng.
   - Lưu trữ bản nháp nhật ký offline vào `localStorage` / `IndexedDB` để chống mất dữ liệu khi gián đoạn mạng.
