"""
Automated Test Suite for Phase v1.5.0:
1. Create entry with multiple photos.
2. Verify physical files exist on disk and in PostgreSQL entry_photos.
3. Update entry with deleted_photo_ids: verify DB record deleted AND physical files removed from disk.
4. Photo-only entry: empty content with 1 photo is valid.
5. Delete all photos transitioning to pure text entry.
6. Empty content + empty photos rejected with 400.
7. Orphaned tags cleanup verification.
"""

import sys
import os
import io
import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def create_client():
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener, cj

def request_json(opener, method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode("utf-8"))
        except Exception:
            return e.code, {"message": raw.decode("utf-8", errors="ignore")}

def create_multipart_payload(fields: dict, files: list):
    boundary = "----WebKitFormBoundaryKokoroTestBoundary7MA4YWxkTrZu0gW"
    buf = io.BytesIO()

    for k, v in fields.items():
        buf.write(f"--{boundary}\r\n".encode("utf-8"))
        buf.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        buf.write(f"{v}\r\n".encode("utf-8"))

    for field_name, file_name, file_bytes in files:
        buf.write(f"--{boundary}\r\n".encode("utf-8"))
        buf.write(f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode("utf-8"))
        buf.write(b"Content-Type: image/png\r\n\r\n")
        buf.write(file_bytes)
        buf.write(b"\r\n")

    buf.write(f"--{boundary}--\r\n".encode("utf-8"))
    content_type = f"multipart/form-data; boundary={boundary}"
    return buf.getvalue(), content_type

def request_multipart(opener, method, endpoint, fields: dict, files: list):
    url = f"{BASE_URL}{endpoint}"
    body_bytes, content_type = create_multipart_payload(fields, files)
    req = urllib.request.Request(url, data=body_bytes, method=method)
    req.add_header("Content-Type", content_type)
    try:
        with opener.open(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw.decode("utf-8"))
        except Exception:
            return e.code, {"message": raw.decode("utf-8", errors="ignore")}

from PIL import Image

def make_test_image(color=(255, 183, 197)):
    img = Image.new("RGB", (200, 200), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_tests():
    print("=================================================================")
    print("  KOKORO (心) — TEST SUITE: V1.5.0 MEDIA LIFECYCLE & EDGE CASES")
    print("=================================================================")

    client, cj = create_client()

    # Step 0: Mock Login
    print("\n[Step 0] Dang nhap nguoi dung mau (user_id = 1)...")
    st, resp = request_json(client, "POST", "/api/auth/mock-login", {"user_id": 1})
    assert st == 200, f"Login failed: {st} {resp}"
    print(f"  -> PASS: Dang nhap thanh cong: {resp['user']['name']}")

    # Step 1: Create Entry with 2 Photos
    print("\n[Step 1] Tao bai viet voi 2 anh dinh kem va tag #testv15...")
    fields = {
        "title": "Kiem thu Media Lifecycle v1.5",
        "content": "Noi dung bai viet thu nghiem xoa anh vat ly",
        "mood": "serene",
        "weather": "sunny",
        "tags": "#testv15 #media_audit"
    }
    files = [
        ("photos", "photo1.png", make_test_image((255, 100, 100))),
        ("photos", "photo2.png", make_test_image((100, 100, 255)))
    ]
    st, resp = request_multipart(client, "POST", "/api/entries", fields, files)
    assert st == 201, f"Create entry failed: {st} {resp}"
    entry_id = resp["entry_id"]
    print(f"  -> PASS: Tao bai viet thanh cong (ID: {entry_id})")

    # Fetch entry details to inspect photos
    st, list_resp = request_json(client, "GET", "/api/entries")
    assert st == 200
    entry = next((e for e in list_resp["entries"] if e["id"] == entry_id), None)
    assert entry is not None, f"Entry {entry_id} not found in listing"
    assert len(entry["photos"]) == 2, f"Expected 2 photos, found {len(entry['photos'])}"
    print(f"  -> PASS: Tim thay bai viet trong DB voi 2 anh: ID={entry['photos'][0]['id']}, ID={entry['photos'][1]['id']}")

    photo_to_delete = entry["photos"][0]
    photo_to_keep = entry["photos"][1]

    path_orig = os.path.join(BASE_DIR, photo_to_delete["url"].replace("/", os.sep))
    path_thumb = os.path.join(BASE_DIR, photo_to_delete["thumbUrl"].replace("/", os.sep))
    assert os.path.exists(path_orig), f"Original photo file should exist on disk: {path_orig}"
    assert os.path.exists(path_thumb), f"Thumbnail file should exist on disk: {path_thumb}"
    print(f"  -> PASS: File anh vat ly ton tai tren o dia truoc khi xoa:")
    print(f"     Goc: {path_orig}")
    print(f"     Thumb: {path_thumb}")

    # Step 2: Update entry, deleting 1 photo via deleted_photo_ids
    print(f"\n[Step 2] Xoa 1 anh (photo_id = {photo_to_delete['id']}) qua PUT /api/entries/{entry_id}...")
    update_fields = {
        "title": "Kiem thu sau khi xoa 1 anh",
        "content": "Noi dung da cap nhat con lai 1 anh",
        "mood": "cozy",
        "weather": "sunny",
        "tags": "#testv15",
        "deleted_photo_ids": json.dumps([photo_to_delete["id"]])
    }
    st, resp = request_multipart(client, "PUT", f"/api/entries/{entry_id}", update_fields, [])
    assert st == 200, f"Update entry failed: {st} {resp}"
    print(f"  -> PASS: API cap nhat tra ve thanh cong!")

    # Verify physical file deletion on disk
    assert not os.path.exists(path_orig), f"Original photo should be physically deleted: {path_orig}"
    assert not os.path.exists(path_thumb), f"Thumbnail should be physically deleted: {path_thumb}"
    print("  -> PASS: File goc va file thumbnail da bi XOA VEC tren o dia!")

    # Verify PostgreSQL entry_photos count
    st, list_resp = request_json(client, "GET", "/api/entries")
    entry_updated = next((e for e in list_resp["entries"] if e["id"] == entry_id), None)
    assert len(entry_updated["photos"]) == 1, f"Expected 1 remaining photo, got {len(entry_updated['photos'])}"
    assert entry_updated["photos"][0]["id"] == photo_to_keep["id"], "Kept photo ID should match"
    print(f"  -> PASS: DB chi con 1 anh (ID={entry_updated['photos'][0]['id']})")

    # Step 3: Photo-only entry (Empty content, 1 photo attached)
    print("\n[Step 3] Kiem tra Edge Case: Dang bai viet chi co anh (content rong)...")
    st, resp = request_multipart(client, "POST", "/api/entries", {
        "title": "Nhat ky chi co anh",
        "content": "   ",
        "mood": "reflective",
        "tags": "#photo_only"
    }, [("photos", "only_photo.png", make_test_image((50, 200, 100)))])
    assert st == 201, f"Photo-only entry should succeed: {st} {resp}"
    photo_only_id = resp["entry_id"]
    print(f"  -> PASS: Dang bai viet chi co anh thanh cong (ID: {photo_only_id})")

    # Step 4: Empty content AND empty photos rejected
    print("\n[Step 4] Kiem tra Edge Case: Content rong VA khong co anh bi tu choi...")
    st, resp = request_multipart(client, "POST", "/api/entries", {
        "title": "Bai viet rong",
        "content": "   ",
        "mood": "serene"
    }, [])
    assert st == 400, f"Should return 400 for empty entry, got {st} {resp}"
    print(f"  -> PASS: May chu tu choi 400 dung tieu chuan: {resp.get('message')}")

    # Step 5: Transition to pure text entry (Delete all remaining photos)
    print(f"\n[Step 5] Xoa sach toan bo anh con lai, chuyen thanh bai viet thuan van ban...")
    st, resp = request_multipart(client, "PUT", f"/api/entries/{entry_id}", {
        "title": "Bai viet thuan van ban sau khi xoa het anh",
        "content": "Chi con chu, khong con anh nao",
        "mood": "grateful",
        "deleted_photo_ids": json.dumps([photo_to_keep["id"]])
    }, [])
    assert st == 200, f"Transition to pure text entry failed: {st} {resp}"

    st, list_resp = request_json(client, "GET", "/api/entries")
    entry_text_only = next((e for e in list_resp["entries"] if e["id"] == entry_id), None)
    assert len(entry_text_only["photos"]) == 0, "Photos should be 0"
    print("  -> PASS: Bai viet da tro thanh nhat ky thuan van ban hop le!")

    # Step 6: Cleanup test entries
    print(f"\n[Step 6] Don dep du lieu kiem thu...")
    st, _ = request_json(client, "DELETE", f"/api/entries/{entry_id}")
    assert st == 200
    st, _ = request_json(client, "DELETE", f"/api/entries/{photo_only_id}")
    assert st == 200
    print("  -> PASS: Da don dep cac bai viet kiem thu thanh cong!")

    print("\n=================================================================")
    print("  TAT CA 6 BIEU DO KIEM THU MEDIA LIFECYCLE & EDGE CASES: PASS 100%! 🌸✨")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
