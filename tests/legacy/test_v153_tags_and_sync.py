import sys
import requests
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5050"

def test_tags_and_sync():
    print("==================================================================")
    print("TEST SUITE: v1.5.3 Tag Management & Dynamic Synchronization")
    print("==================================================================")

    # 1. Unauthenticated request to /api/tags must return 401
    r_unauth = requests.get(f"{BASE_URL}/api/tags")
    assert r_unauth.status_code == 401, f"Expected 401, got {r_unauth.status_code}"
    print("✓ Unauthenticated GET /api/tags returns 401 Unauthorized")

    # 2. Login User 38
    session = requests.Session()
    r_login = session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 38})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    user = r_login.json()["user"]
    print(f"✓ User 38 logged in: {user['name']} (ID: {user['id']})")

    # 3. GET /api/tags for User 38
    r_tags = session.get(f"{BASE_URL}/api/tags")
    assert r_tags.status_code == 200, f"GET /api/tags failed: {r_tags.text}"
    assert r_tags.headers.get("cache-control") == "no-cache, no-store, must-revalidate, max-age=0"
    data = r_tags.json()
    assert data["status"] == "success"
    assert "tags" in data
    tags = data["tags"]
    print(f"✓ GET /api/tags returned {len(tags)} tags with no-cache headers")

    for t in tags[:5]:
        print(f"   - Tag: {t['name']} | Usage count: {t['usage_count']}")
        assert "id" in t and "name" in t and "usage_count" in t

    # 4. Check sorting: usage_count DESC
    usage_counts = [t["usage_count"] for t in tags]
    assert usage_counts == sorted(usage_counts, reverse=True), "Tags are not ordered by usage_count DESC!"
    print("✓ Tags are strictly ordered by usage_count DESC")

    # 5. GET /api/stats/summary for User 38
    r_stats = session.get(f"{BASE_URL}/api/stats/summary")
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert "totalEntries" in stats
    assert "moodCounts" in stats
    assert "moodBreakdown" in stats
    print(f"✓ GET /api/stats/summary returned totalEntries: {stats['totalEntries']}, moodCounts: {stats['moodCounts']}")

    # 6. Create a test entry with a unique tag and verify tag count increments
    unique_tag = f"#tagtest_{int(hash('test') % 10000)}"
    entry_payload = {
        "title": "Nhật ký kiểm thử tag v1.5.3",
        "content": "Kiểm tra tăng usage_count của tag và đồng bộ danh mục.",
        "mood": "serene",
        "weather": "sunny",
        "entry_date": "2026-10-12",
        "tags": f"{unique_tag} #healing"
    }
    r_create = session.post(f"{BASE_URL}/api/entries", data=entry_payload)
    assert r_create.status_code in (200, 201), f"Create entry failed: {r_create.text}"
    created_id = r_create.json().get("entry_id")
    print(f"✓ Created test entry ID: {created_id} with tag {unique_tag}")

    # 7. Verify unique_tag appears in /api/tags with usage_count >= 1
    r_tags_after = session.get(f"{BASE_URL}/api/tags")
    assert r_tags_after.status_code == 200
    tags_after = r_tags_after.json()["tags"]
    found_tag = next((t for t in tags_after if t["name"] == unique_tag or t["name"] == unique_tag.lstrip('#')), None)
    assert found_tag is not None, f"Tag {unique_tag} was not found in tags list!"
    assert found_tag["usage_count"] >= 1
    print(f"✓ Verified tag '{found_tag['name']}' usage_count: {found_tag['usage_count']}")

    # 8. Clean up test entry
    r_del = session.delete(f"{BASE_URL}/api/entries/{created_id}")
    assert r_del.status_code == 200
    print(f"✓ Cleaned up test entry ID: {created_id}")

    # 9. Verify isolation: Login User 1 and ensure User 38's custom tag is NOT in User 1's tags
    session_u1 = requests.Session()
    r_login_u1 = session_u1.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 1})
    assert r_login_u1.status_code == 200
    r_tags_u1 = session_u1.get(f"{BASE_URL}/api/tags")
    assert r_tags_u1.status_code == 200
    tags_u1 = r_tags_u1.json()["tags"]
    found_in_u1 = next((t for t in tags_u1 if t["name"] == unique_tag), None)
    assert found_in_u1 is None, f"Data leakage! Tag {unique_tag} appeared in User 1's tags list."
    print("✓ Multi-account isolation verified: User 1 cannot see User 38 tags")

    print("\n==================================================================")
    print("ALL v1.5.3 TAG & SYNC TESTS PASSED 100%! ✨")
    print("==================================================================")

if __name__ == "__main__":
    test_tags_and_sync()
