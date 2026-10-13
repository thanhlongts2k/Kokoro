"""
Automated Test Suite for Phase 4:
1. Data Export (/api/entries/export): JSON format, Content-Disposition, and Strict User Isolation
2. Rich Stats Breakdown (/api/stats/summary): 5 Moods distribution, total photos, and streak calculation
3. Streak Calculation Logic verification
"""

import sys
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from http.cookiejar import CookieJar

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.routes.entry_routes import calculate_streak_days

BASE_URL = "http://127.0.0.1:5050/api"

def create_client():
    """Create an opener with dedicated cookie jar."""
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
            return status, body, resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"message": raw}
        return e.code, body, e.headers

def run_phase4_tests():
    print("=================================================================")
    print("  KOKORO (心) — PHASE 4: OFFLINE PWA, RICH STATS & EXPORT TESTS")
    print("=================================================================")

    client_unauth, _ = create_client()
    client_aria, _ = create_client()
    client_kenji, _ = create_client()

    # 1. Test Unauthenticated Export
    print("\n[Step 1] Kiem tra chan xuat du lieu khi chua dang nhap...")
    status, err_body, _ = request_json(client_unauth, "GET", "/entries/export")
    assert status == 401, f"Expected 401, got {status}"
    print(f"  [PASS] Chan thanh cong unauthenticated export: {err_body['message']}")

    # 2. Login as Aria Tanaka (User ID = 1)
    print("\n[Step 2] Dang nhap tai khoan Aria Tanaka (User ID = 1)...")
    status, login_aria, _ = request_json(client_aria, "POST", "/auth/mock-login", {"user_id": 1})
    assert status == 200 and login_aria["status"] == "success"
    print(f"  -> Aria logged in: {login_aria['user']['name']}")

    # 3. Export Entries for Aria Tanaka
    print("\n[Step 3] Xuat file backup JSON cho Aria Tanaka...")
    req_export_aria = urllib.request.Request(f"{BASE_URL}/entries/export", method="GET")
    with client_aria.open(req_export_aria) as resp:
        assert resp.status == 200
        cd_header = resp.headers.get("Content-Disposition", "")
        ct_header = resp.headers.get("Content-Type", "")
        print(f"  -> Content-Disposition: {cd_header}")
        print(f"  -> Content-Type: {ct_header}")
        assert "attachment" in cd_header and "kokoro_backup_" in cd_header
        assert "application/json" in ct_header

        aria_export_data = json.loads(resp.read().decode("utf-8"))

    assert aria_export_data["app"].startswith("Kokoro")
    assert aria_export_data["user"]["id"] == 1
    assert aria_export_data["user"]["email"] == "aria.tanaka@kokoro.me"
    aria_entry_ids = [e["id"] for e in aria_export_data["entries"]]
    print(f"  -> Total exported entries for Aria: {aria_export_data['total_entries']}")
    print(f"  -> Aria Entry IDs: {aria_entry_ids}")
    assert len(aria_entry_ids) > 0
    print("  [PASS] File JSON backup cua Aria day du metadata va chuan form!")

    # 4. Login as Kenji Sato and Export
    print("\n[Step 4] Dang nhap tai khoan Kenji Sato (User ID = 12) va kiem tra tinh co lap...")
    status, login_kenji, _ = request_json(client_kenji, "POST", "/auth/mock-login", {"user_id": 12})
    assert status == 200

    req_export_kenji = urllib.request.Request(f"{BASE_URL}/entries/export", method="GET")
    with client_kenji.open(req_export_kenji) as resp:
        assert resp.status == 200
        kenji_export_data = json.loads(resp.read().decode("utf-8"))

    assert kenji_export_data["user"]["id"] == 12
    kenji_entry_ids = [e["id"] for e in kenji_export_data["entries"]]
    print(f"  -> Kenji Entry IDs in Export: {kenji_entry_ids}")

    # Critical Isolation Assertion: No overlap between Aria and Kenji exports
    overlap = set(aria_entry_ids).intersection(set(kenji_entry_ids))
    assert len(overlap) == 0, f"CRITICAL LEAK: Overlap found between user backups: {overlap}"
    print(f"  [PASS] Co lap du lieu 100%: Ban backup cua Kenji khong chua bat ky bai viet nao cua Aria!")

    # 5. Test Rich Stats Summary (/api/stats/summary)
    print("\n[Step 5] Kiem tra endpoint Rich Stats Summary (/api/stats/summary)...")
    status, stats_data, _ = request_json(client_aria, "GET", "/stats/summary")
    assert status == 200 and stats_data["status"] == "success"
    print(f"  -> Total Entries: {stats_data['totalEntries']}")
    print(f"  -> Total Photos:  {stats_data['totalPhotos']}")
    print(f"  -> Streak Days:   {stats_data['streakDays']}")
    print(f"  -> Serene Pct:    {stats_data['serenePercent']}%")
    print(f"  -> Mood Breakdown: {json.dumps(stats_data['moodBreakdown'], indent=4)}")

    assert "totalPhotos" in stats_data
    assert "streakDays" in stats_data
    assert "moodBreakdown" in stats_data
    for m in ["serene", "cozy", "reflective", "grateful", "energetic"]:
        assert m in stats_data["moodBreakdown"]
        assert "count" in stats_data["moodBreakdown"][m]
        assert "percent" in stats_data["moodBreakdown"][m]
    print("  [PASS] Rich Stats Summary tra ve day du 5 loai cam xuc va chi so chuoi ngay!")

    # 6. Unit Test Streak Days Calculation Algorithm
    print("\n[Step 6] Kiem tra thuat toan tinh Streak Days lien tiep...")
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    old_day = today - timedelta(days=10)

    # Case A: Empty
    assert calculate_streak_days([]) == 0
    # Case B: Only today
    assert calculate_streak_days([today]) == 1
    # Case C: Today, yesterday, and day before (consecutive 3)
    assert calculate_streak_days([today, yesterday, day_before]) == 3
    # Case D: Not today, but yesterday and day before (streak is alive at 2)
    assert calculate_streak_days([yesterday, day_before]) == 2
    # Case E: Only 10 days ago (broken streak)
    assert calculate_streak_days([old_day]) == 0
    print("  [PASS] Thuat toan tinh Streak Days hoat dong chuan xac tuyet doi!")

    print("\n=================================================================")
    print("  ALL PHASE 4 TESTS PASSED 100%! GIAI DOAN 4 HOAN TAT XUAT SAC!")
    print("=================================================================")

if __name__ == "__main__":
    run_phase4_tests()
