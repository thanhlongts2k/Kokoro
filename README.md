# 🌸 Kokoro (心) — Japanese-inspired Aesthetic Diary & Photo Journal PWA

[![Version](https://img.shields.io/badge/version-v1.2.0-ffb7c5.svg?style=flat-square)](https://github.com/thanhlongts2k/Kokoro)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Backend](https://img.shields.io/badge/Starlette-ASGI-4F46E5?style=flat-square)](https://www.starlette.io/)
[![Database](https://img.shields.io/badge/PostgreSQL-18-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![PWA](https://img.shields.io/badge/PWA-Ready-f472b6?style=flat-square&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/license-MIT-pink?style=flat-square)](LICENSE)

> *"Hạnh phúc không phải là đích đến rực rỡ, mà là sự bình an trong từng nhịp thở bình dị mỗi sớm mai."*  
> **Kokoro (心)** là ứng dụng Progressive Web App (PWA) nhật ký cá nhân và lưu giữ khoảnh khắc hình ảnh theo triết lý chữa lành (Zen & Healing) với ngôn ngữ thiết kế **Soft Sakura Pastel** kết hợp hiệu ứng kính mờ thanh khiết (**Light Frosted Glassmorphism**).

---

## ✨ Điểm Nổi Bật & Tính Năng Cốt Lõi (Key Highlights)

### 🎨 1. Trải Nghiệm Giao Diện Soft Sakura & Thiết Kế Thích Ứng (Responsive UI/UX)
- **Hệ thống Design Tokens tinh tế:** Tông màu hồng phấn hoa anh đào dịu nhẹ, đổ bóng đổ mờ pastel, chống chói và thư giãn thị giác.
- **Light Frosted Glassmorphism:** Hiệu ứng kính mờ bán trong suốt thanh lịch trên nền cánh hoa rơi nhẹ nhàng.
- **Thích ứng đa kích thước:** Tối ưu hóa trải nghiệm trên Mobile (Bottom Navigation, Touch Thumb-zone), Tablet và Desktop (3-column layout).
- **Bộ lọc cảm xúc 5 sắc thái:** *Serene 🌸 (Bình yên)*, *Cozy ☕ (Ấm áp)*, *Reflective 🌙 (Chiêm nghiệm)*, *Grateful 🍵 (Biết ơn)*, *Energetic ⚡ (Năng lượng)*.
- **Thanh tiến trình cảm xúc đa phân đoạn (Multi-segment Progress Bar):** Trực quan hóa phân bổ tâm trạng và tính toán chuỗi ngày viết liên tiếp (**Streak Days**) thực tế.

### 💾 2. Ngoại Tuyến Toàn Diện & Tự Động Lưu (Offline First & Auto-save)
- **Tự động lưu bản nháp (Editor Drafts):** Tự động lưu nội dung đang gõ vào `localStorage` phân tách theo `user_id` với debounce 1 giây, tự khôi phục kèm nút "Xóa bản nháp".
- **Hàng đợi ngoại tuyến an toàn qua IndexedDB:** Khi mất kết nối mạng, các bài viết và file ảnh nhị phân (Blob/File) được giữ trọn vẹn trong `IndexedDB` (`kokoro_offline_db`), triệt tiêu 100% rủi ro tràn hạn mức 5MB của `localStorage`.
- **Đồng bộ tự động khi có mạng (Auto-sync on Online):** Lắng nghe sự kiện `window.addEventListener('online')`, tự động duyệt hàng đợi gửi lên máy chủ và hiển thị Toast thông báo dịu dàng.

### 🖼️ 3. Media Processing Engine Siêu Nén (Pillow WebP)
- **Chuyển đổi & Nén tự động:** Toàn bộ ảnh JPEG, PNG tải lên được chuyển đổi sang chuẩn `.webp` (chất lượng 82%), tự động co tỷ lệ tối đa 1600px và tạo thumbnail 400px.
- **Tự động xoay ảnh theo EXIF (Orientation Auto-transpose):** Khắc phục lỗi ảnh chụp điện thoại bị lộn ngược hoặc nghiêng chiều.
- **Hiệu quả nén ấn tượng:** Giảm đến **98.4% dung lượng** lưu trữ trong khi vẫn giữ độ sắc nét tự nhiên.
- **Cache-Control bất biến:** Header `Cache-Control: public, max-age=31536000, immutable` cho toàn bộ media tải lên.

### 🔐 4. Xác Thực Linh Hoạt & Cô Lập Dữ Liệu Tuyệt Đối (Hybrid Auth & Isolation)
- **Google Identity Services (GIS):** Đăng nhập an toàn qua Google One Tap và Google Sign-In button container.
- **Hybrid Dev Account Switcher:** Chuyển đổi 1-click giữa các tài khoản Mock Dev (`Aria Tanaka`, `Kenji Sato`) trong môi trường phát triển.
- **Phiên làm việc an toàn:** Quản lý qua JWT Bearer Token và HttpOnly Session Cookie (`kokoro_session`).
- **Cô lập dữ liệu 100%:** Toàn bộ bài viết, ảnh, tags, số liệu thống kê được phân quyền độc lập theo `user_id`.

### 📦 5. Sao Lưu & Khôi Phục Dữ Liệu 1-Click (Backup Export & Import)
- **Xuất file JSON sao lưu:** Tải toàn bộ nhật ký của tài khoản hiện tại về máy tính đính kèm metadata, danh sách tags và đường dẫn ảnh.
- **Khôi phục dữ liệu nguyên tử:** Nhập lại file `kokoro_backup_*.json` vào tài khoản một cách an toàn trong một database transaction duy nhất.

---

## 🏛️ Kiến Trúc Hệ Thống (System Architecture)

```
d:\Sources\Kokoro\
├── app/                      # Backend Modules
│   ├── config.py             # Cấu hình môi trường (.env, port, upload paths, version)
│   ├── database.py           # PostgreSQL ThreadedConnectionPool & Schema DDL
│   ├── auth.py               # Google OAuth verification & JWT Session Engine
│   ├── routes/               # Starlette REST API Handlers
│   │   ├── auth_routes.py    # /api/auth/* endpoints (login, logout, me, google)
│   │   └── entry_routes.py   # /api/entries/* (CRUD, pin, export, import, stats)
│   └── services/             # Business Domain Services
│       └── media_service.py  # Pillow WebP Converter, EXIF transpose & Thumbnailer
├── static/                   # Progressive Web App Client
│   ├── index.html            # Single Page Application HTML5
│   ├── manifest.webmanifest  # PWA Manifest (Standalone installation)
│   ├── sw.js                 # Service Worker (Cache-First & Network-First)
│   ├── css/                  # CSS Design System (Tokens, Glassmorphism, Layout)
│   └── js/                   # Vanilla ES Modules (api, auth, app, editor, lightbox)
├── tests/                    # Automated Test Suites
│   ├── test_api_upload.py    # Test nén ảnh WebP & PostgreSQL transactions
│   ├── test_auth_isolation.py# Test phân quyền bảo mật & cô lập dữ liệu 2 chiều
│   ├── test_phase4_features.py # Test export JSON, rich stats & streak days
│   └── test_phase5_stress.py # Stress test tải 4 ảnh 4000x3000, EXIF & import JSON
├── uploads/                  # Local Media Storage (Git-ignored)
│   ├── originals/            # Ảnh gốc chuẩn WebP (max 1600px)
│   └── thumbnails/           # Ảnh thu nhỏ chuẩn WebP (max 400px)
├── server.py                 # Starlette ASGI Application Entrypoint (Uvicorn)
├── AGENTS.md                 # Single Source of Truth quy chuẩn vận hành
├── ROADMAP.md                # Lộ trình 5 giai đoạn phát triển (100% Complete)
└── CHANGELOG.md              # Lịch sử phiên bản SemVer (Keep a Changelog)
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy (Quickstart)

### 1. Yêu cầu hệ thống (Prerequisites)
- **Python**: 3.12+ (khuyến nghị Python 3.14).
- **PostgreSQL**: 16+ (đã kiểm thử và tối ưu trên PostgreSQL 18 cổng `5432`).
- **Trình duyệt**: Hỗ trợ hiện đại (Google Chrome, Edge, Safari iOS, Android Chrome).

### 2. Cài đặt thư viện phụ thuộc
```bash
pip install starlette uvicorn psycopg2-binary pillow python-dotenv requests google-auth pyjwt
```

### 3. Cấu hình tệp môi trường (`.env`)
Tạo hoặc chỉnh sửa tệp `.env` tại thư mục gốc của dự án:
```env
# Server
PORT=5050
HOST=0.0.0.0
DEBUG=True

# Database PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kokoro_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Security & Authentication
SECRET_KEY=kokoro_sakura_healing_pastel_secret_key_2026
MOCK_AUTH=True
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com

# Media Storage
UPLOAD_DIR=uploads
```

### 4. Khởi chạy máy chủ
```bash
python server.py
```

Ứng dụng sẽ tự động khởi tạo cơ sở dữ liệu nếu chưa có và lắng nghe tại:
- **Local Access:** `http://localhost:5050/`
- **Nginx Reverse Proxy:** Tương thích hoàn toàn khi triển khai tại sub-path `/kokoro/`.

---

## 🧪 Kiểm Thử Tự Động (Automated Testing)

Kokoro đi kèm 4 bộ test suite toàn diện kiểm tra từ đơn vị đến tích hợp đầu cuối:

```bash
# 1. Kiểm tra REST API & Xử lý ảnh Pillow
python tests/test_api_upload.py

# 2. Kiểm tra Phân quyền tài khoản & Cô lập dữ liệu
python tests/test_auth_isolation.py

# 3. Kiểm tra Export JSON, Rich Stats & Thuật toán Streak Days
python tests/test_phase4_features.py

# 4. Stress Test tải ảnh độ phân giải cao 4000x3000 & Khôi phục Import JSON
python tests/test_phase5_stress.py
```
> **Kết quả:** Cả 4 bộ test suite đều đạt **100% PASS** với 0 lỗi tiềm ẩn.

---

## 📜 Tài Liệu Chuẩn SSoT (Documentation)

- [ARCHITECTURE.md](ARCHITECTURE.md) — Kiến trúc hệ thống chi tiết và thiết kế cơ sở dữ liệu.
- [ROADMAP.md](ROADMAP.md) — Bảng theo dõi tiến độ hoàn thành 5/5 giai đoạn phát triển.
- [CHANGELOG.md](CHANGELOG.md) — Nhật ký phát hành các phiên bản `v1.0.0` đến `v1.2.0`.
- [AGENTS.md](AGENTS.md) — Bộ quy chuẩn kỹ thuật và nguyên tắc vận hành an toàn.

---

## 🌸 Bản Quyền & Giấy Phép (License)
Dự án được phát triển và duy trì bởi **Thanh Long (thanhlongts2k)**.  
Được phát hành theo giấy phép [MIT License](LICENSE).
