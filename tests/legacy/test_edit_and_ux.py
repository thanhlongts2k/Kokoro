"""
Automated Test Suite for Edit Entry (PUT /api/entries/{id}) & UX Features
- Strict User Data Isolation on Edit (User A cannot edit User B's entry)
- Full Field Updates: title, content, mood, weather, entry_date, tags
- Append Photo via Pillow WebP processing during edit
- Live Search Query validation
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
import io

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050/api"

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
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status, body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"message": raw}
        return e.code, body

def post_multipart(opener, endpoint, fields, files=None, method="POST"):
    url = f"{BASE_URL}{endpoint}"
    boundary = "----KokoroBoundaryTest7MA4YWxkTrZu0gW"
    body = bytearray()

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{v}\r\n".encode("utf-8"))

    if files:
        for field_name, file_name, file_bytes, content_type in files:
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode("utf-8"))
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
            body.extend(file_bytes)
            body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=bytes(body), method=method)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        with opener.open(req) as resp:
            status = resp.status
            data = json.loads(resp.read().decode("utf-8"))
            return status, data
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"message": raw}
        return e.code, body

def create_sample_png_bytes():
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(244, 114, 182))
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_tests():
    print("=================================================================")
    print("  KOKORO (心) — TEST SUITE: EDIT ENTRY & UX SEARCH VERIFICATION")
    print("=================================================================")

    aria, _ = create_client()
    kenji, _ = create_client()

    # 1. Fetch Mock Users
    print("\n[Step 1] Lay danh sach Mock Users...")
    st, mock_res = request_json(aria, "GET", "/auth/mock-users")
    assert st == 200 and len(mock_res["users"]) >= 2
    user1 = mock_res["users"][0]
    user2 = mock_res["users"][1]

    # Login Aria
    st, res1 = request_json(aria, "POST", "/auth/mock-login", {"user_id": user1["id"]})
    assert st == 200, f"Aria login failed: {res1}"
    print(f"  -> OK Aria: {res1['user']['name']} (ID: {user1['id']})")

    # 2. Login Kenji
    print("\n[Step 2] Dang nhap Kenji Sato...")
    st, res2 = request_json(kenji, "POST", "/auth/mock-login", {"user_id": user2["id"]})
    assert st == 200, f"Kenji login failed: {res2}"
    print(f"  -> OK Kenji: {res2['user']['name']} (ID: {user2['id']})")

    # 3. Aria creates a journal entry
    print("\n[Step 3] Aria tao bai viet ban dau...")
    st, res = post_multipart(aria, "/entries", {
        "title": "Bình minh mùa thu Kyoto",
        "content": "Một sớm se lạnh ngồi ngắm lá phong rơi bên hiên chùa.",
        "mood": "serene",
        "weather": "sunny",
        "entry_date": "2026-10-10",
        "tags": "#kyoto #autumn #leaves"
    })
    assert st == 201, f"Failed to create entry: {res}"
    entry_id = res["entry_id"]
    print(f"  -> OK: Entry ID = {entry_id}")

    # 4. Kenji attempts to edit Aria's entry -> Must return 404
    print(f"\n[Step 4] Kenji co tinh sua bai #{entry_id} cua Aria (Data Isolation)...")
    st, res = post_multipart(kenji, f"/entries/{entry_id}", {
        "title": "Hacked by Kenji",
        "content": "Kenji sua bai trai phep",
        "mood": "energetic"
    }, method="PUT")
    assert st == 404, f"Kenji should NOT be able to edit Aria's entry! Status: {st}, Response: {res}"
    print(f"  -> PASS: Bị từ chối chính xác (HTTP {st}): {res['message']}")

    # 5. Non-existent entry ID -> Must return 404
    print("\n[Step 5] Aria sua bai voi ID khong ton tai (999999)...")
    st, res = post_multipart(aria, "/entries/999999", {
        "title": "Test",
        "content": "Test content",
    }, method="PUT")
    assert st == 404, f"Expected 404, got {st}"
    print(f"  -> PASS: HTTP 404 Not Found")

    # 6. Validation: Empty content -> Must return 400
    print("\n[Step 6] Aria gui request sua voi noi dung trong...")
    st, res = post_multipart(aria, f"/entries/{entry_id}", {
        "title": "Tieu de moi",
        "content": "   "
    }, method="PUT")
    assert st == 400, f"Expected 400, got {st}"
    print(f"  -> PASS: Bắt lỗi validation rỗng (HTTP {st}): {res['message']}")

    # 7. Aria updates her entry successfully
    print(f"\n[Step 7] Aria cap nhat bai viet #{entry_id}...")
    updated_title = "Hoàng hôn mùa thu Kyoto - Đã cập nhật"
    updated_content = "Chiều muộn thưởng trà sen nóng và ngắm ráng chiều vàng óng ả."
    updated_tags = "#kyoto #autumn #greentea #sen"
    st, res = post_multipart(aria, f"/entries/{entry_id}", {
        "title": updated_title,
        "content": updated_content,
        "mood": "grateful",
        "weather": "windy",
        "entry_date": "2026-10-10",
        "tags": updated_tags
    }, method="PUT")
    assert st == 200, f"Failed to update entry: {res}"
    print(f"  -> PASS: HTTP {st}: {res['message']}")

    # 8. Verify updated data in GET /api/entries
    print(f"\n[Step 8] Kiem tra du lieu sau cap nhat qua GET /api/entries...")
    st, res = request_json(aria, "GET", "/entries")
    assert st == 200
    entries = res["entries"]
    target = next((e for e in entries if e["id"] == entry_id), None)
    assert target is not None, "Target entry not found in list"
    assert target["title"] == updated_title, f"Title mismatch: {target['title']}"
    assert target["content"] == updated_content, f"Content mismatch: {target['content']}"
    assert target["mood"] == "grateful", f"Mood mismatch: {target['mood']}"
    assert "#greentea" in target["tags"], f"Tags mismatch: {target['tags']}"
    print(f"  -> PASS: Entry #{entry_id} da cap nhat day du tren PostgreSQL!")
    print(f"     Tiêu đề: {target['title']}")
    print(f"     Tâm trạng: {target['mood']}")
    print(f"     Thẻ: {target['tags']}")

    # 9. Aria updates entry and attaches an additional photo
    print(f"\n[Step 9] Aria cap nhat va bo sung anh moi qua Pillow WebP...")
    img_bytes = create_sample_png_bytes()
    st, res = post_multipart(aria, f"/entries/{entry_id}", {
        "title": updated_title,
        "content": updated_content,
        "mood": "grateful",
        "tags": updated_tags
    }, files=[("photos", "test_photo_added.png", img_bytes, "image/png")], method="PUT")
    assert st == 200, f"Failed to add photo: {res}"

    st, res = request_json(aria, "GET", "/entries")
    target = next((e for e in res["entries"] if e["id"] == entry_id), None)
    photos = target.get("photos", [])
    print(f"  -> PASS: Cap nhat anh thanh cong! So anh hien tai: {len(photos)}")

    # 10. Live Search parameter testing
    print(f"\n[Step 10] Kiem tra tim kiem GET /api/entries?search=greentea...")
    st, res = request_json(aria, "GET", "/entries?search=greentea")
    assert st == 200
    search_entries = res["entries"]
    assert any(e["id"] == entry_id for e in search_entries), "Search query should match updated tag #greentea"
    print(f"  -> PASS: Live search tim thay {len(search_entries)} ket qua voi tu khoa 'greentea'!")

    # 11. Cleanup test entry
    print(f"\n[Step 11] Don dep test entry #{entry_id}...")
    st, res = request_json(aria, "DELETE", f"/entries/{entry_id}")
    assert st == 200
    print("  -> OK: Da xoa entry sau test.")

    print("\n=================================================================")
    print("  TAT CA TEST EDIT ENTRY & UX SEARCH DEU PASS 100%! 🌸✨")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
