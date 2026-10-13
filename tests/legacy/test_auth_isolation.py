"""
Automated Test Suite for Phase 3:
1. Google Identity Services config & endpoints
2. Mock Login for Multiple Users (Aria Tanaka vs Kenji Sato)
3. Strict Data Isolation: User A cannot see, pin, or delete User B's entries
4. Logout session clearance
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:5050/api"

def create_client():
    """Create a urllib opener with dedicated CookieJar to simulate a browser session."""
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

def run_auth_tests():
    print("=================================================================")
    print("  KOKORO (心) — PHASE 3: AUTHENTICATION & DATA ISOLATION TEST")
    print("=================================================================")

    client_aria, cj_aria = create_client()
    client_kenji, cj_kenji = create_client()
    client_unauth, _ = create_client()

    # 1. Test Auth Config
    print("\n[Step 1] Kiem tra GET /auth/config...")
    status, config = request_json(client_unauth, "GET", "/auth/config")
    assert status == 200, f"Expected 200, got {status}"
    assert config["google_client_id"] != ""
    assert config["mock_auth"] is True
    print(f"  -> Google Client ID: {config['google_client_id']}")
    print(f"  -> Mock Auth Enabled: {config['mock_auth']}")
    print("  [PASS] Auth config endpoint hoat dong tot!")

    # 2. Test Unauthenticated Access
    print("\n[Step 2] Kiem tra truy cap khi chua dang nhap...")
    status, me_unauth = request_json(client_unauth, "GET", "/auth/me")
    assert status == 200 and me_unauth["authenticated"] is False
    print("  -> GET /auth/me unauthenticated: user is None")

    status, entries_unauth = request_json(client_unauth, "GET", "/entries")
    assert status == 401, f"Expected 401 Unauthorized, got {status}"
    print(f"  -> GET /entries returned {status}: {entries_unauth['message']}")
    print("  [PASS] Chan thanh cong truy cap chua xac thuc!")

    # 3. List Mock Users and Login as Aria Tanaka
    print("\n[Step 3] Dang nhap tai khoan Aria Tanaka (User ID = 1)...")
    status, mock_users = request_json(client_aria, "GET", "/auth/mock-users")
    assert status == 200 and len(mock_users["users"]) >= 2
    user1 = mock_users["users"][0]
    user2 = mock_users["users"][1]
    print(f"  -> User 1: ID {user1['id']} - {user1['name']} ({user1['email']})")
    print(f"  -> User 2: ID {user2['id']} - {user2['name']} ({user2['email']})")

    status, login_res1 = request_json(client_aria, "POST", "/auth/mock-login", {"user_id": user1["id"]})
    assert status == 200 and login_res1["status"] == "success"
    print(f"  -> Aria cookie set: {len(cj_aria)} cookies")

    # Verify session with GET /auth/me
    status, me_aria = request_json(client_aria, "GET", "/auth/me")
    assert status == 200 and me_aria["authenticated"] is True
    assert me_aria["user"]["id"] == user1["id"]
    print(f"  -> GET /auth/me verified: {me_aria['user']['name']}")
    print("  [PASS] Aria Tanaka dang nhap thanh cong!")

    # 4. Create Entry for Aria Tanaka
    print("\n[Step 4] Tao bai viet cho Aria Tanaka...")
    boundary = "----AriaBoundary"
    body_aria = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="title"\r\n\r\nNhat ky bi mat cua Aria\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"\r\n\r\nDay la khoanh khac dac biet chi mot minh Aria nhin thay.\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="mood"\r\n\r\nserene\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="tags"\r\n\r\n#aria #secret\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req_create_aria = urllib.request.Request(
        f"{BASE_URL}/entries",
        data=body_aria,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with client_aria.open(req_create_aria) as resp:
        aria_entry_data = json.loads(resp.read().decode("utf-8"))
    aria_entry_id = aria_entry_data["entry_id"]
    print(f"  -> Created Aria Entry ID: {aria_entry_id}")

    # 5. Login as Kenji Sato (User 2)
    print(f"\n[Step 5] Dang nhap tai khoan Kenji Sato (User ID = {user2['id']})...")
    status, login_res2 = request_json(client_kenji, "POST", "/auth/mock-login", {"user_id": user2["id"]})
    assert status == 200 and login_res2["status"] == "success"
    status, me_kenji = request_json(client_kenji, "GET", "/auth/me")
    assert status == 200 and me_kenji["authenticated"] is True
    assert me_kenji["user"]["id"] == user2["id"]
    print(f"  -> Kenji Sato session active: {me_kenji['user']['name']}")
    print("  [PASS] Kenji Sato dang nhap thanh cong!")

    # 6. Verify Kenji Sato CANNOT see Aria's Entry
    print(f"\n[Step 6] Kiem tra tinh co lap: Kenji co nhin thay bai viet {aria_entry_id} cua Aria khong?...")
    status, kenji_entries = request_json(client_kenji, "GET", "/entries")
    assert status == 200
    kenji_entry_ids = [e["id"] for e in kenji_entries["entries"]]
    print(f"  -> Danh sach Entry IDs cua Kenji: {kenji_entry_ids}")
    assert aria_entry_id not in kenji_entry_ids, f"CRITICAL: Kenji Sato is able to see Aria's entry {aria_entry_id}!"
    print("  [PASS] Du lieu duoc co lap tuyet doi! Kenji KHONG the xem bai cua Aria!")

    # 7. Verify Kenji CANNOT delete or pin Aria's Entry
    print(f"\n[Step 7] Kiem tra: Kenji thu xoa hoac ghim bai viet {aria_entry_id} cua Aria...")
    status, delete_attempt = request_json(client_kenji, "DELETE", f"/entries/{aria_entry_id}")
    assert status == 404, f"Expected 404 (or 403), got {status}"
    print(f"  -> Kenji delete attempt blocked with {status}: {delete_attempt['message']}")

    status, pin_attempt = request_json(client_kenji, "PATCH", f"/entries/{aria_entry_id}/pin")
    assert status == 404, f"Expected 404 (or 403), got {status}"
    print(f"  -> Kenji pin attempt blocked with {status}: {pin_attempt['message']}")
    print("  [PASS] Kenji khong co bat ky quyen han nao tren bai viet cua Aria!")

    # 8. Create Entry for Kenji and Verify Aria cannot see Kenji's Entry
    print("\n[Step 8] Tao bai viet rieng cho Kenji Sato...")
    body_kenji = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="title"\r\n\r\nTra dao buoi chieu - Kenji\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"\r\n\r\nMot tach tra xanh nong giup tinh tam sau gio lam.\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="mood"\r\n\r\ncozy\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="tags"\r\n\r\n#matcha #zen\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")
    req_create_kenji = urllib.request.Request(
        f"{BASE_URL}/entries",
        data=body_kenji,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with client_kenji.open(req_create_kenji) as resp:
        kenji_entry_data = json.loads(resp.read().decode("utf-8"))
    kenji_entry_id = kenji_entry_data["entry_id"]
    print(f"  -> Created Kenji Entry ID: {kenji_entry_id}")

    # Check Aria's view
    status, aria_entries = request_json(client_aria, "GET", "/entries")
    aria_ids = [e["id"] for e in aria_entries["entries"]]
    assert kenji_entry_id not in aria_ids
    print(f"  -> Aria's entry list: {aria_ids} (Does NOT contain Kenji's {kenji_entry_id})")
    print("  [PASS] Hai tai khoan hoan toan doc lap, hai chieu deu an toan tuyet doi!")

    # 9. Test Logout
    print("\n[Step 9] Kiem tra chuc nang dang xuat (Logout)...")
    status, logout_res = request_json(client_aria, "POST", "/auth/logout")
    assert status == 200
    status, me_after_logout = request_json(client_aria, "GET", "/auth/me")
    assert me_after_logout["authenticated"] is False
    print("  -> Session cleared successfully! User is now unauthenticated.")
    print("  [PASS] Dang xuat thanh cong!")

    # 10. Test Google Auth Endpoint & upsert_user
    print("\n[Step 10] Kiem tra Google Auth endpoint & upsert_user...")
    status_missing, res_missing = request_json(client_unauth, "POST", "/auth/google", {})
    assert status_missing == 400 and res_missing["status"] == "error"
    print(f"  -> Missing credential returned {status_missing}: {res_missing['message']}")

    status_invalid, res_invalid = request_json(client_unauth, "POST", "/auth/google", {"credential": "invalid_token_xyz"})
    assert status_invalid == 401 and res_invalid["status"] == "error"
    print(f"  -> Invalid credential returned {status_invalid}: {res_invalid['message']}")

    from app.auth import upsert_user
    test_u = upsert_user("g_test_verify", "g_test@kokoro.me", "Google Tester", "https://img.test")
    assert test_u["google_id"] == "g_test_verify"
    assert test_u["email"] == "g_test@kokoro.me"
    print(f"  -> upsert_user succeeded for user id {test_u['id']}: {test_u['name']}")

    # Clean up test user
    from app.database import get_cursor
    with get_cursor() as cur:
        cur.execute("DELETE FROM users WHERE google_id = %s;", ("g_test_verify",))
    print("  [PASS] Google Auth endpoint va upsert_user hoat dong chinh xac 100%!")

    print("\n=================================================================")
    print("  ALL PHASE 3 AUTH & ISOLATION TESTS PASSED 100%! EXCELLENT!")
    print("=================================================================")

if __name__ == "__main__":
    run_auth_tests()
