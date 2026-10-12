import sys
import requests
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5050"

def test_full_verification():
    print("==================================================================")
    print("VERIFICATION SUITE: iOS PWA Hardening & Anti-Silent-Pass Test")
    print("==================================================================")

    # 1. Login user 38
    session38 = requests.Session()
    r = session38.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 38})
    assert r.status_code == 200, f"Login user 38 failed: {r.text}"
    user38 = r.json()["user"]
    print(f"✓ User 38 logged in: {user38['name']} ({user38['email']})")

    # 2. Check no-cache headers on GET /api/entries, GET /api/stats/summary, GET /api/entries/95
    r_entries = session38.get(f"{BASE_URL}/api/entries")
    assert r_entries.headers.get("cache-control") == "no-cache, no-store, must-revalidate, max-age=0"
    assert r_entries.headers.get("pragma") == "no-cache"
    print("✓ GET /api/entries has strict no-cache headers")

    r_stats = session38.get(f"{BASE_URL}/api/stats/summary")
    assert r_stats.headers.get("cache-control") == "no-cache, no-store, must-revalidate, max-age=0"
    print("✓ GET /api/stats/summary has strict no-cache headers")

    r_single = session38.get(f"{BASE_URL}/api/entries/95")
    assert r_single.headers.get("cache-control") == "no-cache, no-store, must-revalidate, max-age=0"
    print("✓ GET /api/entries/95 has strict no-cache headers")

    # 3. Check rowcount verification on PUT /api/entries/9999999 (non-existent)
    r_nonexistent = session38.put(f"{BASE_URL}/api/entries/9999999", data={"title": "Test", "content": "Test"})
    assert r_nonexistent.status_code == 404, f"Expected 404, got {r_nonexistent.status_code}"
    print("✓ PUT /api/entries/9999999 strictly returns 404 Not Found")

    # 4. Check cross-user modification protection (Zero silent pass)
    session1 = requests.Session()
    r_u1 = session1.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 1})
    assert r_u1.status_code == 200
    r_cross = session1.put(f"{BASE_URL}/api/entries/95", data={"title": "Hacked", "content": "Hacked"})
    assert r_cross.status_code == 404, f"Expected 404 for cross-user update, got {r_cross.status_code}"
    print("✓ Cross-user update on Entry 95 strictly returns 404 Not Found")

    # 5. Check normal update succeeds with 200 and commits to DB
    update_data = {
        "title": "Nóng nực vô cùng (Đã xác nhận)",
        "content": "Làm trên cty mà cúp điênn - Đã cập nhật thành công!",
        "mood": "serene",
        "weather": "sunny",
        "entry_date": "2026-10-12",
        "tags": "#cupdien #verified"
    }
    r_update = session38.put(f"{BASE_URL}/api/entries/95", data=update_data)
    assert r_update.status_code == 200, f"Update failed: {r_update.text}"
    assert r_update.headers.get("cache-control") == "no-cache, no-store, must-revalidate, max-age=0"
    
    # Verify in DB
    r_verify = session38.get(f"{BASE_URL}/api/entries/95")
    entry_verified = r_verify.json()["entry"]
    assert entry_verified["title"] == update_data["title"]
    assert entry_verified["content"] == update_data["content"]
    assert "#cupdien" in entry_verified["tags"]
    print("✓ PUT /api/entries/95 commits new title, content and tags directly to PostgreSQL")

    print("\nALL BACKEND AUDIT CRITERIA PASSED 100%! ✨\n")

if __name__ == '__main__':
    test_full_verification()
