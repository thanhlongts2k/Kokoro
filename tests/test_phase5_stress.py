import os
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import io
import time
import json
import requests
from PIL import Image, ImageDraw

BASE_URL = "http://127.0.0.1:5050"

def create_high_res_exif_image(width=4000, height=3000, orientation=6):
    """
    Generate an uncompressed high-resolution test image with EXIF orientation.
    orientation=6 corresponds to 90 degrees CCW / rotated (width & height should transpose).
    """
    img = Image.new("RGB", (width, height), color=(255, 235, 238))
    draw = ImageDraw.Draw(img)
    # Draw some rich shapes to simulate real photo content
    for i in range(0, min(width, height) // 2 - 20, 100):
        draw.rectangle([i, i, width - i, height - i], outline=(244, 114, 182), width=5)
    draw.text((100, 100), "KOKORO EXIF STRESS TEST 2026", fill=(219, 39, 119))

    # Add EXIF tag for orientation
    exif = img.getexif()
    exif[0x0112] = orientation  # 0x0112 is Orientation tag

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95, exif=exif)
    val = buffer.getvalue()
    return val

def test_cache_and_proxy_headers():
    print("\n[Step 1] Kiem tra Cache-Control va Proxy Headers...")
    session = requests.Session()

    # 1. HTML no-cache header
    resp = session.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    cache_ctrl = resp.headers.get("Cache-Control", "")
    print(f"  -> GET / Cache-Control: {cache_ctrl}")
    assert "no-cache" in cache_ctrl, f"Expected no-cache for index.html, got: {cache_ctrl}"

    # 2. CORS Preflight OPTIONS & Actual Request Expose-Headers
    options_resp = session.options(
        f"{BASE_URL}/api/entries",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )
    print(f"  -> OPTIONS /api/entries Status: {options_resp.status_code}")
    print(f"  -> Access-Control-Allow-Methods: {options_resp.headers.get('Access-Control-Allow-Methods')}")
    assert options_resp.status_code == 200

    # Actual request with Origin to verify Access-Control-Expose-Headers
    get_resp = session.get(
        f"{BASE_URL}/api/health",
        headers={"Origin": "http://localhost:3000"}
    )
    expose_hdr = get_resp.headers.get("Access-Control-Expose-Headers", "")
    print(f"  -> GET /api/health Access-Control-Expose-Headers: {expose_hdr}")
    assert "Content-Disposition" in expose_hdr, f"Expected Content-Disposition in expose headers, got: {expose_hdr}"

    # 3. Proxy headers handling (X-Forwarded-Proto, X-Forwarded-Prefix)
    health_resp = session.get(
        f"{BASE_URL}/api/health",
        headers={
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Prefix": "/kokoro"
        }
    )
    assert health_resp.status_code == 200
    print(f"  -> Healthcheck with Proxy Headers: {health_resp.json().get('status')}")
    print("  [PASS] Cache-Control, CORS va Proxy headers hoat dong hoan hao!")

def test_high_res_exif_stress():
    print("\n[Step 2] Kiem tra Tai Anh Lon & Xu ly EXIF Orientation (Stress Test)...")
    session = requests.Session()
    # Login as Aria Tanaka
    login_resp = session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 1})
    assert login_resp.status_code == 200

    # Generate 4 high-res photos (4000x3000, orientation=6)
    print("  -> Dang tao 4 anh do phan giai cao (4000x3000) voi EXIF Orientation tag=6...")
    photos_data = []
    total_raw_bytes = 0
    for i in range(4):
        raw_bytes = create_high_res_exif_image(width=4000, height=3000, orientation=6)
        photos_data.append((f"highres_stress_{i+1}.jpg", raw_bytes))
        total_raw_bytes += len(raw_bytes)

    print(f"  -> Tong dung luong 4 anh tho: {total_raw_bytes / (1024 * 1024):.2f} MB")

    files = [
        ("photos", (name, data, "image/jpeg"))
        for name, data in photos_data
    ]
    data = {
        "title": "Stress Test: 4 anh 4000x3000 kem EXIF xoay chieu",
        "content": "Kiem thu tai anh lon va kiem tra thuat toan Pillow nen WebP duoi ap luc cao.",
        "mood": "energetic",
        "weather": "sunny",
        "entry_date": "2026-10-10",
        "tags": "#stress #performance #exif"
    }

    start_time = time.time()
    resp = session.post(f"{BASE_URL}/api/entries", data=data, files=files)
    elapsed = time.time() - start_time
    print(f"  -> Thoi gian xu ly va luu 4 anh lon vao PostgreSQL: {elapsed:.2f} giay")
    assert resp.status_code == 201, f"Failed create entry: {resp.text}"
    entry_id = resp.json()["entry_id"]
    print(f"  -> Tao thanh cong Entry ID: {entry_id}")

    # Verify photos in DB and check EXIF orientation transpose
    from app.database import get_cursor
    with get_cursor() as cur:
        cur.execute("SELECT file_path, thumb_path, width, height, file_size FROM entry_photos WHERE entry_id = %s;", (entry_id,))
        saved_photos = cur.fetchall()

    assert len(saved_photos) == 4
    total_webp_bytes = sum(p["file_size"] for p in saved_photos)
    print(f"  -> Tong dung luong sau khi nen WebP: {total_webp_bytes / (1024 * 1024):.2f} MB")
    print(f"  -> Ty le giam dung luong: {((1 - total_webp_bytes / total_raw_bytes) * 100):.1f}%")

    for i, p in enumerate(saved_photos):
        w, h = p["width"], p["height"]
        print(f"  -> Photo {i+1}: Dimensions = {w}x{h}, File Size = {p['file_size']}B, Path = {p['file_path']}")
        # Because orientation was 6 (90 deg rotation), 4000x3000 became 3000x4000, then scaled to max 1600: 1200x1600
        assert max(w, h) <= 1600, f"Max dimension exceeded: {w}x{h}"
        assert h > w, f"EXIF Orientation failed! Expected portrait (h > w) due to tag 6, got {w}x{h}"

    # Verify Cache-Control header on uploaded WebP file
    sample_path = saved_photos[0]["thumb_path"]
    upload_resp = session.get(f"{BASE_URL}/{sample_path}")
    assert upload_resp.status_code == 200
    cache_val = upload_resp.headers.get("Cache-Control", "")
    print(f"  -> GET /{sample_path} Cache-Control: {cache_val}")
    assert "immutable" in cache_val and "31536000" in cache_val, f"Cache-Control not immutable: {cache_val}"

    print("  [PASS] Pillow xu ly EXIF xoay chieu chuan xac, nen WebP sieu nho va Cache-Control immutable 100%!")
    return entry_id

def test_import_backup():
    print("\n[Step 3] Kiem tra Chuc nang Khoi phuc Du lieu (Import Backup JSON)...")
    session = requests.Session()
    # Login as Kenji Sato (User ID 12)
    session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 12})

    test_backup = {
        "app": "Kokoro Test Backup",
        "version": "v1.1.0",
        "entries": [
            {
                "title": "Import Test: Ky niem hoa anh dao ruc ro",
                "content": "Noi dung duoc khoi phuc tu ban sao luu JSON ngoai tuyen.",
                "mood": "grateful",
                "weather": "sunny",
                "entry_date": "2026-10-08",
                "is_pinned": True,
                "tags": ["#imported", "#backup", "#sakura"]
            },
            {
                "title": "Import Test: Tach tra chieu an yen",
                "content": "Moi thu da tro ve nguyen ven sau khi khoi phuc.",
                "mood": "cozy",
                "weather": "cloudy",
                "entry_date": "2026-10-09",
                "is_pinned": False,
                "tags": ["#tea", "#zen"]
            }
        ]
    }

    backup_json_bytes = json.dumps(test_backup).encode("utf-8")
    files = {
        "backup_file": ("test_backup.json", backup_json_bytes, "application/json")
    }

    import_resp = session.post(f"{BASE_URL}/api/entries/import", files=files)
    assert import_resp.status_code == 200, f"Import failed: {import_resp.text}"
    result = import_resp.json()
    print(f"  -> Import result: {result}")
    assert result["imported_count"] == 2

    # Verify imported entries belong to Kenji Sato
    entries_resp = session.get(f"{BASE_URL}/api/entries?tag=imported")
    assert entries_resp.status_code == 200
    items = entries_resp.json()["entries"]
    assert len(items) >= 1
    assert items[0]["title"] == "Import Test: Ky niem hoa anh dao ruc ro"
    print(f"  -> Tim thay bai viet vua import cua Kenji: {items[0]['title']} (Tags: {items[0]['tags']})")

    # Verify unauthenticated import is rejected
    unauth_session = requests.Session()
    unauth_resp = unauth_session.post(f"{BASE_URL}/api/entries/import", files=files)
    assert unauth_resp.status_code == 401
    print("  -> Chặn thành công unauthenticated import: 401 Unauthorized")

    print("  [PASS] Chuc nang Khoi phuc Du lieu (Import Backup) hoan toan chinh xac va an toan!")

if __name__ == "__main__":
    print("=================================================================")
    print("  KOKORO (心) — PHASE 5: STRESS, CACHE & IMPORT TESTS")
    print("=================================================================")
    test_cache_and_proxy_headers()
    stress_entry_id = test_high_res_exif_stress()
    test_import_backup()
    print("\n=================================================================")
    print("  ALL PHASE 5 TESTS PASSED 100%! GIAI DOAN 5 HOAN TAT XUAT SAC!")
    print("=================================================================")
