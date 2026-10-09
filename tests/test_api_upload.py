"""
Automated Integration Test: API Upload & PostgreSQL Verification
Tests:
1. Pillow in-memory image generation (JPEG & PNG)
2. Multipart POST to /api/entries
3. PostgreSQL transaction verification (entries, entry_photos, tags, entry_tags)
4. Disk verification of converted .webp and _thumb.webp files
5. GET /api/entries filtering & response structure
6. PATCH /api/entries/{id}/pin toggle
"""

import io
import sys
import os
import json
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import Config
from app.database import get_cursor

def create_sample_image(width: int, height: int, color1: tuple, color2: tuple, fmt: str) -> bytes:
    """Create a sample image in memory with a gradient/pattern."""
    img = Image.new("RGB", (width, height), color=color1)
    draw = ImageDraw.Draw(img)
    # Draw simple shapes to test Pillow Lanczos resizing
    for i in range(0, min(width, height) // 2 - 10, 30):
        draw.ellipse([i, i, width - i, height - i], outline=color2, width=3)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def build_multipart_body(fields: dict, files: list) -> tuple[bytes, str]:
    """Encode fields and files as multipart/form-data."""
    boundary = "----KokoroTestBoundary" + os.urandom(8).hex()
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))

    for field_name, filename, file_bytes, content_type in files:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    content_type_header = f"multipart/form-data; boundary={boundary}"
    return bytes(body), content_type_header

def run_tests():
    print("=================================================================")
    print("  KOKORO (心) — INTEGRATION TEST SUITE (PHASE 2: API & POSTGRES)")
    print("=================================================================")

    # 1. Create two sample images (one large 1920x1080 to test downscaling, one 600x600)
    print("\n[Step 1] Tao 2 file anh test (JPEG 1920x1080 & PNG 600x600)...")
    img1_bytes = create_sample_image(1920, 1080, (253, 242, 248), (244, 114, 182), "JPEG")
    img2_bytes = create_sample_image(600, 600, (240, 253, 244), (74, 222, 128), "PNG")
    print(f"  -> Anh 1 (JPEG): {len(img1_bytes)} bytes")
    print(f"  -> Anh 2 (PNG):  {len(img2_bytes)} bytes")

    from app.auth import create_session_token
    token = create_session_token(1, "aria.tanaka@kokoro.me", "Aria Tanaka (心)")
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Send multipart request to POST /api/entries
    print("\n[Step 2] Gui request POST /api/entries qua multipart/form-data...")
    fields = {
        "title": "Khoảnh khắc hoa anh đào nở sớm",
        "content": "Hôm nay những cánh hoa đầu mùa đã bắt đầu hé nở, cảm giác không gian tràn ngập sự bình yên và dịu dàng.",
        "mood": "serene",
        "weather": "sunny",
        "entry_date": "2026-10-09",
        "tags": "#sakura #healing #spring"
    }
    files = [
        ("photos", "sakura_highres.jpg", img1_bytes, "image/jpeg"),
        ("photos", "matcha_tea.png", img2_bytes, "image/png"),
    ]

    body_bytes, ct_header = build_multipart_body(fields, files)

    req = urllib.request.Request(
        "http://localhost:5050/api/entries",
        data=body_bytes,
        headers={"Content-Type": ct_header, "Authorization": f"Bearer {token}"},
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        status_code = resp.status
        resp_data = json.loads(resp.read().decode("utf-8"))

    print(f"  -> Response Status: {status_code}")
    print(f"  -> Response Body:   {resp_data}")
    assert status_code == 201, f"Expected 201, got {status_code}"
    assert resp_data["status"] == "success"
    entry_id = resp_data["entry_id"]
    print(f"  [PASS] Tao bai viet thanh cong voi Entry ID = {entry_id}")

    # 3. Verify PostgreSQL Database Records
    print(f"\n[Step 3] Kiem tra CSDL PostgreSQL (kokoro_db) cho Entry ID {entry_id}...")
    with get_cursor() as cur:
        # Check entries table
        cur.execute("SELECT id, title, content, mood, weather, entry_date, is_pinned FROM entries WHERE id = %s;", (entry_id,))
        entry_row = cur.fetchone()
        assert entry_row is not None, "Entry not found in DB!"
        print(f"  -> DB Entry: title='{entry_row['title']}', mood='{entry_row['mood']}', date={entry_row['entry_date']}")

        # Check entry_photos table
        cur.execute("SELECT id, file_path, thumb_path, file_size, width, height FROM entry_photos WHERE entry_id = %s ORDER BY sort_order;", (entry_id,))
        photo_rows = cur.fetchall()
        assert len(photo_rows) == 2, f"Expected 2 photos, got {len(photo_rows)}"
        for idx, pr in enumerate(photo_rows):
            print(f"  -> Photo {idx + 1}: path={pr['file_path']}, thumb={pr['thumb_path']}, dim={pr['width']}x{pr['height']}, size={pr['file_size']}B")
            # Verify downscale (1920x1080 scaled down to <= 1600)
            assert max(pr['width'], pr['height']) <= 1600, "Dimension exceeds 1600px!"

        # Check tags
        cur.execute("""
            SELECT t.name FROM tags t 
            JOIN entry_tags et ON t.id = et.tag_id 
            WHERE et.entry_id = %s;
        """, (entry_id,))
        tag_rows = [r["name"] for r in cur.fetchall()]
        print(f"  -> Linked Tags: {tag_rows}")
        assert "#sakura" in tag_rows and "#healing" in tag_rows and "#spring" in tag_rows

    print("  [PASS] Du lieu CSDL PostgreSQL hoan toan chinh xac!")

    # 4. Verify Disk Storage (WebP and Thumbnails)
    print("\n[Step 4] Kiem tra file vat ly tren o dia (uploads/)...")
    for pr in photo_rows:
        orig_file = Config.BASE_DIR / pr["file_path"]
        thumb_file = Config.BASE_DIR / pr["thumb_path"]

        assert orig_file.exists(), f"Original file does not exist: {orig_file}"
        assert thumb_file.exists(), f"Thumbnail file does not exist: {thumb_file}"
        assert orig_file.suffix == ".webp", "Original not WebP"
        assert thumb_file.suffix == ".webp", "Thumb not WebP"

        # Verify Pillow can open them
        with Image.open(orig_file) as im:
            assert im.format == "WEBP"
        with Image.open(thumb_file) as im_thumb:
            assert im_thumb.format == "WEBP"
            assert max(im_thumb.size) <= 400, "Thumb dimension exceeds 400px"

        print(f"  -> Verified on disk: {orig_file.name} (Original) & {thumb_file.name} (Thumb <= 400px)")

    print("  [PASS] File WebP va Thumbnail duoc tao hop le tren o dia!")

    # 5. Verify GET /api/entries
    print("\n[Step 5] Kiem tra endpoint GET /api/entries...")
    get_req = urllib.request.Request("http://localhost:5050/api/entries", headers=auth_header)
    with urllib.request.urlopen(get_req) as resp:
        get_data = json.loads(resp.read().decode("utf-8"))

    assert get_data["status"] == "success"
    assert get_data["count"] >= 1
    target_entry = next((e for e in get_data["entries"] if e["id"] == entry_id), None)
    assert target_entry is not None, "Created entry not found in GET /api/entries list"
    assert len(target_entry["photos"]) == 2
    assert len(target_entry["tags"]) == 3
    print(f"  -> GET entries thanh cong: Tim thay Entry ID {entry_id} voi {len(target_entry['photos'])} anh va tags {target_entry['tags']}")
    print("  [PASS] GET /api/entries hoat dong chuan xac!")

    # 6. Test PATCH /api/entries/{id}/pin
    print(f"\n[Step 6] Test PATCH /api/entries/{entry_id}/pin...")
    pin_req = urllib.request.Request(f"http://localhost:5050/api/entries/{entry_id}/pin", headers=auth_header, method="PATCH")
    with urllib.request.urlopen(pin_req) as resp:
        pin_data = json.loads(resp.read().decode("utf-8"))
    assert pin_data["status"] == "success"
    assert pin_data["is_pinned"] is True
    print(f"  -> Entry ID {entry_id} pinned: {pin_data['is_pinned']}")
    print("  [PASS] PATCH pin hoat dong chuan xac!")

    # 7. Test GET /api/stats/summary
    print("\n[Step 7] Test GET /api/stats/summary...")
    stats_req = urllib.request.Request("http://localhost:5050/api/stats/summary", headers=auth_header)
    with urllib.request.urlopen(stats_req) as resp:
        stats_data = json.loads(resp.read().decode("utf-8"))
    assert stats_data["status"] == "success"
    assert stats_data["totalEntries"] >= 1
    print(f"  -> Stats summary: {stats_data}")
    print("  [PASS] GET /api/stats/summary tra ve so lieu thuc te tu PostgreSQL!")

    print("\n=================================================================")
    print("  ALL TESTS PASSED! GIAI DOAN 2 HOAN TAT 100% THANH CONG!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
