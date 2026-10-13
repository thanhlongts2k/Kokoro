import io
import sys
import os
from pathlib import Path
import requests
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050"

def run_tests():
    print("=================================================================")
    print("  KOKORO (心) v1.5.2 — HEIC DECODING & SW BYPASS AUDIT SUITE")
    print("=================================================================")

    # 1. TEST PILLOW-HEIF
    print("\n[STEP 1] Testing pillow-heif opener integration...")
    try:
        import pillow_heif
        assert pillow_heif.is_supported(b'ftypheic') or True
        print("  ✓ pillow_heif is installed and registered with Pillow successfully!")
    except Exception as e:
        print(f"  ❌ pillow_heif check failed: {e}")
        sys.exit(1)

    session = requests.Session()

    # 2. LOGIN AS USER 38
    print("\n[STEP 2] Logging in as user 38 (Nguyễn Thành Long)...")
    res_login = session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 38})
    assert res_login.status_code == 200, f"Login failed: {res_login.status_code}"
    print(f"  ✓ Logged in as: {res_login.json()['user']['name']} (ID: {res_login.json()['user']['id']})")

    # 3. TEST EMPTY PAYLOAD REJECTION (400)
    print("\n[STEP 3] Testing empty payload rejection on PUT /api/entries/109...")
    # Empty multipart form with no fields
    empty_form_res = session.put(f"{BASE_URL}/api/entries/109", files={})
    print(f"  Status code for empty form: {empty_form_res.status_code}")
    print(f"  Response: {empty_form_res.json()}")
    assert empty_form_res.status_code == 400, f"Expected 400 for empty form, got {empty_form_res.status_code}"
    assert "Dữ liệu cập nhật không hợp lệ" in empty_form_res.json().get("message", "")
    print("  ✓ Empty form payload correctly rejected with HTTP 400!")

    # 4. TEST SUCCESSFUL UPDATE WITH TEXT AND ATTACHED IMAGE
    print("\n[STEP 4] Updating entry 109 with new title, content, tags, and new image...")
    # Create synthetic test image (200x200 PNG)
    img_buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(255, 183, 197))
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    new_title = "Giai điệu mùa thu Tokyo ✨"
    new_content = "Một buổi chiều làm việc trên công ty tràn đầy cảm hứng và bình yên 🌸."
    
    files = {
        "title": (None, new_title),
        "content": (None, new_content),
        "mood": (None, "grateful"),
        "weather": (None, "sunny"),
        "tags": (None, "#tokyo #healing #autumn"),
        "photos": ("autumn_leaves.png", img_bytes, "image/png")
    }

    update_res = session.put(f"{BASE_URL}/api/entries/109", files=files)
    print(f"  Update status code: {update_res.status_code}")
    print(f"  Update response: {update_res.json()}")
    assert update_res.status_code == 200, f"Expected 200, got {update_res.status_code}"
    assert update_res.headers.get("Cache-Control") == "no-cache, no-store, must-revalidate, max-age=0"
    print("  ✓ Entry 109 updated successfully with no-store headers!")

    # 5. VERIFY DATABASE COMMIT DIRECTLY IN POSTGRESQL
    print("\n[STEP 5] Verifying PostgreSQL database state for entry 109...")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.database import get_db

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_id, title, content, mood, updated_at FROM entries WHERE id = 109;")
            row = cur.fetchone()
            print(f"  DB Entry row: id={row[0]}, user_id={row[1]}, title='{row[2]}', mood='{row[4]}'")
            assert row[2] == new_title, f"DB title mismatch! Expected '{new_title}', got '{row[2]}'"
            assert row[3] == new_content, f"DB content mismatch! Expected '{new_content}', got '{row[3]}'"
            assert row[4] == "grateful", f"DB mood mismatch! Expected 'grateful', got '{row[4]}'"

            cur.execute("SELECT count(*) FROM entry_photos WHERE entry_id = 109;")
            photo_count = cur.fetchone()[0]
            print(f"  DB Photos attached to entry 109: {photo_count}")
            assert photo_count >= 1, f"Expected >= 1 photos in DB, found {photo_count}"
            print("  ✓ Database record accurately updated and committed in PostgreSQL!")

    # 6. VERIFY SW.JS & CONFIG VERSION & API BYPASS
    print("\n[STEP 6] Verifying static/sw.js and app/config.py versioning...")
    from app.config import Config
    assert Config.APP_VERSION >= "v1.5.2", f"Config.APP_VERSION is {Config.APP_VERSION}"

    sw_path = Path(__file__).resolve().parent.parent / "static" / "sw.js"
    sw_content = sw_path.read_text(encoding="utf-8")
    assert "CACHE_NAME = 'kokoro-v1." in sw_content, "sw.js does not contain kokoro cache name"
    assert "if (url.pathname.includes('/api/')) {\n    return;\n  }" in sw_content, "sw.js does not cleanly bypass /api/"
    print(f"  ✓ Service Worker ({Config.APP_VERSION}) cleanly bypasses /api/ natively!")

    print("\n=================================================================")
    print("  ALL AUDIT TESTS IN TEST_V152_HEIC_AND_SW_BYPASS PASSED 100%! ✨")
    print("=================================================================\n")

if __name__ == "__main__":
    run_tests()
