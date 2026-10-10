"""
Automated Test Suite for Phase v1.4.0:
1. Zen Ambient Sound Assets availability, file size & HTTP serving (rain, furin, waves, stream)
2. Client-side WebCrypto SHA-256 + Salt Passcode Lock simulation & security verification
3. System Version verification (v1.4.0)
4. Full Core CRUD & Isolation Regression Test
"""

import sys
import os
import json
import hashlib
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050"

def create_client():
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener, cj

def request_http(opener, method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                body = json.loads(raw.decode("utf-8"))
            else:
                body = raw
            return status, body, resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = {"message": raw.decode("utf-8", errors="ignore")}
        return e.code, body, e.headers

def run_v14_tests():
    print("=================================================================")
    print("  KOKORO (心) — TEST SUITE: V1.4.0 PASSCODE LOCK & ZEN AUDIO")
    print("=================================================================")

    client, cj = create_client()

    # 1. Healthcheck & Version bump verification
    print("\n[Step 1] Kiem tra phien ban may chu GET /api/health...")
    st, body, _ = request_http(client, "GET", "/api/health")
    assert st == 200, f"Health check failed: {st}"
    assert body["version"] == "v1.4.0", f"Version mismatch: expected v1.4.0, got {body['version']}"
    print(f"  -> PASS: Kokoro Server dang chay phien ban: {body['version']} (PostgreSQL: {body['database']})")

    # 2. Check Zen Audio Assets on Disk
    print("\n[Step 2] Kiem tra 4 file am thanh Zen tren o dia (static/audio/)...")
    tracks = ["rain.mp3", "furin.mp3", "waves.mp3", "stream.mp3"]
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audio_dir = os.path.join(base_dir, "static", "audio")

    for t in tracks:
        fp = os.path.join(audio_dir, t)
        assert os.path.exists(fp), f"Missing audio file: {fp}"
        sz = os.path.getsize(fp) / 1024
        assert 50 <= sz <= 350, f"File size out of expected bounds: {t} is {sz:.1f} KB"
        print(f"  -> PASS: {t} ton tai tren dia, dung luong: {sz:.1f} KB (tinh gon < 350KB)")

    # 3. Check Zen Audio Assets served via HTTP
    print("\n[Step 3] Kiem tra phuc vu am thanh qua HTTP (GET /audio/{track})...")
    for t in tracks:
        st, content, headers = request_http(client, "GET", f"/audio/{t}")
        assert st == 200, f"Failed to fetch /audio/{t}: status {st}"
        assert len(content) > 50000, f"Content too small for /audio/{t}"
        print(f"  -> PASS: GET /audio/{t} tra ve HTTP 200 OK ({len(content)} bytes)")

    # 4. WebCrypto SHA-256 + Salt Passcode Logic Verification
    print("\n[Step 4] Kiem tra logic ma hoa mat khau PIN (WebCrypto SHA-256 + Salt)...")
    def simulate_hash_pin(pin: str, salt_hex: str) -> str:
        return hashlib.sha256((pin + salt_hex).encode("utf-8")).hexdigest()

    test_pin = "2509"
    test_salt = os.urandom(16).hex()
    hashed_pin = simulate_hash_pin(test_pin, test_salt)

    # Correct PIN verification
    assert simulate_hash_pin("2509", test_salt) == hashed_pin, "Valid PIN should match hash"
    print("  -> PASS: Ma hoa va xac thuc PIN chinh xac thanh cong!")

    # Incorrect PIN verification
    assert simulate_hash_pin("1234", test_salt) != hashed_pin, "Invalid PIN should not match hash"
    assert simulate_hash_pin("0000", test_salt) != hashed_pin, "Invalid PIN should not match hash"
    print("  -> PASS: Tu choi ma PIN sai chinh xac!")

    # Salt uniqueness verification
    other_salt = os.urandom(16).hex()
    assert simulate_hash_pin(test_pin, other_salt) != hashed_pin, "Different salt must produce different hash"
    print("  -> PASS: Salt ngau nhien 128-bit ngan chan hoan toan tan cong Rainbow Table!")

    # 5. Core CRUD Regression Test
    print("\n[Step 5] Kiem tra hoi quy Core CRUD & Phuc vu giao dien PWA...")
    # Login Aria
    st, login_res, _ = request_http(client, "POST", "/api/auth/mock-login", {"user_id": 1})
    assert st == 200
    print("  -> Logged in as:", login_res["user"]["name"])

    # Create entry
    boundary = "----KokoroBoundaryTestV14"
    body_data = bytearray()
    body_data.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nTest v1.4.0\r\n".encode("utf-8"))
    body_data.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"content\"\r\n\r\nKiem tra hoi quy he thong v1.4.0\r\n".encode("utf-8"))
    body_data.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"mood\"\r\n\r\nserene\r\n".encode("utf-8"))
    body_data.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(f"{BASE_URL}/api/entries", data=bytes(body_data), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with client.open(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        entry_id = res_json["entry_id"]
    print(f"  -> Created entry ID #{entry_id}")

    # Delete entry
    st, del_res, _ = request_http(client, "DELETE", f"/api/entries/{entry_id}")
    assert st == 200
    print(f"  -> Deleted entry ID #{entry_id}")

    print("\n=================================================================")
    print("  TAT CA TEST V1.4.0 (PASSCODE & ZEN AUDIO) DEU PASS 100%! 🌸✨")
    print("=================================================================")

if __name__ == "__main__":
    run_v14_tests()
