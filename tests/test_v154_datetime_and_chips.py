import sys
import requests
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5050"

def test_v154_datetime_and_chips():
    print("==================================================================")
    print("TEST SUITE: v1.5.4 Custom DateTimePicker & Mood Counts Verification")
    print("==================================================================")

    # 1. Login user
    session = requests.Session()
    r_login = session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 38})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    user = r_login.json()["user"]
    print(f"✓ User 38 logged in: {user['name']} (ID: {user['id']})")

    # 2. Get initial stats
    r_stats_init = session.get(f"{BASE_URL}/api/stats/summary")
    assert r_stats_init.status_code == 200
    init_stats = r_stats_init.json()
    init_total = init_stats["totalEntries"]
    init_mood_counts = init_stats.get("moodCounts", {})
    init_cozy_count = init_mood_counts.get("cozy", 0)
    print(f"✓ Initial stats: total={init_total}, cozy_count={init_cozy_count}")

    # 3. Create entry with custom created_at & entry_date
    custom_dt = "2026-05-15T09:45:00"
    custom_entry_date = "2026-05-15"

    create_data = {
        "title": "Nhật ký thử nghiệm DateTime Picker v1.5.4",
        "content": "Bài viết này được tạo vào thời gian tùy chỉnh quá khứ.",
        "mood": "cozy",
        "weather": "sunny",
        "entry_date": custom_entry_date,
        "created_at": custom_dt,
        "tags": "#healing #v154"
    }

    r_create = session.post(f"{BASE_URL}/api/entries", data=create_data)
    assert r_create.status_code == 201, f"Create entry failed: {r_create.text}"
    entry_id = r_create.json()["entry_id"]
    print(f"✓ Created test entry ID {entry_id} with custom created_at '{custom_dt}'")

    # 4. Fetch entry and verify created_at
    r_get = session.get(f"{BASE_URL}/api/entries/{entry_id}")
    assert r_get.status_code == 200, f"Get entry failed: {r_get.text}"
    entry_data = r_get.json()["entry"]
    assert entry_data["entry_date"] == custom_entry_date or entry_data.get("entryDate") == custom_entry_date
    # Compare ISO datetime
    created_at_val = entry_data.get("created_at") or entry_data.get("createdAt")
    assert "2026-05-15" in created_at_val and "09:45" in created_at_val, f"created_at mismatch: {created_at_val}"
    print(f"✓ Verified created_at persisted correctly: {created_at_val}")

    # 5. Verify stats updated cozy count
    r_stats_after = session.get(f"{BASE_URL}/api/stats/summary")
    assert r_stats_after.status_code == 200
    after_stats = r_stats_after.json()
    assert after_stats["totalEntries"] == init_total + 1
    assert after_stats["moodCounts"].get("cozy", 0) == init_cozy_count + 1
    print(f"✓ Stats updated: total={after_stats['totalEntries']}, cozy_count={after_stats['moodCounts'].get('cozy')}")

    # 6. Update entry with a new custom created_at and different mood
    updated_dt = "2026-06-20T18:30:00"
    updated_entry_date = "2026-06-20"

    update_data = {
        "title": "Nhật ký đã cập nhật thời gian v1.5.4",
        "content": "Nội dung cập nhật với thời gian mới.",
        "mood": "reflective",
        "weather": "rainy",
        "entry_date": updated_entry_date,
        "created_at": updated_dt,
        "tags": "#updated #v154"
    }

    r_update = session.put(f"{BASE_URL}/api/entries/{entry_id}", data=update_data)
    assert r_update.status_code == 200, f"Update entry failed: {r_update.text}"
    print(f"✓ Updated test entry ID {entry_id} with new custom created_at '{updated_dt}'")

    # 7. Fetch updated entry and verify created_at
    r_get_updated = session.get(f"{BASE_URL}/api/entries/{entry_id}")
    assert r_get_updated.status_code == 200
    updated_entry = r_get_updated.json()["entry"]
    up_created_at = updated_entry.get("created_at") or updated_entry.get("createdAt")
    assert "2026-06-20" in up_created_at and "18:30" in up_created_at, f"Updated created_at mismatch: {up_created_at}"
    print(f"✓ Verified updated created_at persisted correctly: {up_created_at}")

    # 8. Clean up test entry
    r_del = session.delete(f"{BASE_URL}/api/entries/{entry_id}")
    assert r_del.status_code == 200, f"Delete failed: {r_del.text}"
    print(f"✓ Deleted test entry ID {entry_id}")

    # 9. Verify stats rolled back cleanly
    r_stats_final = session.get(f"{BASE_URL}/api/stats/summary")
    assert r_stats_final.status_code == 200
    final_stats = r_stats_final.json()
    assert final_stats["totalEntries"] == init_total
    print(f"✓ Final stats restored to initial total: {final_stats['totalEntries']}")

    print("\n==================================================================")
    print(">>> ALL v1.5.4 BACKEND INTEGRATION CHECKS PASSED (100% SUCCESS) <<<")
    print("==================================================================")

if __name__ == "__main__":
    test_v154_datetime_and_chips()
