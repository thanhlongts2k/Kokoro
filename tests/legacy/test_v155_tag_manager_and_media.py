import os
import sys
import requests
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:5050"

def test_v155_tag_manager_and_endpoints():
    print("==================================================================")
    print("TEST SUITE: v1.5.5 Tag Manager CRUD & Orphan Cleanup Verification")
    print("==================================================================")

    # 1. Login user 38
    session = requests.Session()
    r_login = session.post(f"{BASE_URL}/api/auth/mock-login", json={"user_id": 38})
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    user = r_login.json()["user"]
    print(f"✓ User 38 logged in: {user['name']} (ID: {user['id']})")

    # 2. Create test entry with tags #v155alpha and #v155beta
    create_data = {
        "title": "Thử nghiệm Tag Manager v1.5.5",
        "content": "Kiểm thử các API đổi tên, merge và dọn dẹp thẻ mồ côi.",
        "mood": "serene",
        "weather": "sunny",
        "entry_date": "2026-10-12",
        "tags": "#v155alpha #v155beta"
    }

    r_create = session.post(f"{BASE_URL}/api/entries", data=create_data)
    assert r_create.status_code == 201, f"Create entry failed: {r_create.text}"
    entry_id = r_create.json()["entry_id"]
    print(f"✓ Created test entry ID {entry_id} with tags '#v155alpha' and '#v155beta'")

    # 3. Verify tags in GET /api/tags
    r_tags = session.get(f"{BASE_URL}/api/tags")
    assert r_tags.status_code == 200, f"Get tags failed: {r_tags.text}"
    tags_list = r_tags.json()["tags"]
    tag_alpha = next((t for t in tags_list if t["name"] == "#v155alpha"), None)
    tag_beta = next((t for t in tags_list if t["name"] == "#v155beta"), None)
    assert tag_alpha is not None, "Tag #v155alpha not found in /api/tags"
    assert tag_beta is not None, "Tag #v155beta not found in /api/tags"
    print(f"✓ Verified tags exist: Alpha ID={tag_alpha['id']}, Beta ID={tag_beta['id']}")

    # 4. Test Rename Tag: PUT /api/tags/{alpha_id} -> #v155renamed
    r_rename = session.put(f"{BASE_URL}/api/tags/{tag_alpha['id']}", json={"name": "#v155renamed"})
    assert r_rename.status_code == 200, f"Rename tag failed: {r_rename.text}"
    renamed_tag_info = r_rename.json()["tag"]
    assert renamed_tag_info["name"] == "#v155renamed"
    print(f"✓ Renamed tag ID {tag_alpha['id']} to '#v155renamed'")

    # Verify entry reflected the new tag
    r_get_entry = session.get(f"{BASE_URL}/api/entries/{entry_id}")
    assert r_get_entry.status_code == 200
    entry_tags = r_get_entry.json()["entry"]["tags"]
    assert "#v155renamed" in entry_tags, f"Expected #v155renamed in entry tags, got: {entry_tags}"
    print(f"✓ Entry tags verified: {entry_tags}")

    # 5. Test Merge Tag: Rename #v155beta to #v155renamed (target already exists)
    r_merge = session.put(f"{BASE_URL}/api/tags/{tag_beta['id']}", json={"name": "v155renamed"}) # Test auto-prefix #
    assert r_merge.status_code == 200, f"Merge tag failed: {r_merge.text}"
    print(f"✓ Successfully merged #v155beta into #v155renamed")

    # Verify #v155beta no longer exists as separate tag
    r_tags_after_merge = session.get(f"{BASE_URL}/api/tags")
    assert r_tags_after_merge.status_code == 200
    tags_after = r_tags_after_merge.json()["tags"]
    assert not any(t["name"] == "#v155beta" for t in tags_after), "Old tag #v155beta should be deleted after merge"
    print("✓ Old merged tag #v155beta cleanly removed from tags table")

    # 6. Test Direct Delete Tag: PUT a temporary tag and DELETE it
    temp_tag_entry_data = {
        "title": "Temp Entry for Direct Delete",
        "content": "Testing direct tag deletion.",
        "mood": "cozy",
        "weather": "sunny",
        "entry_date": "2026-10-12",
        "tags": "#v155tobedeleted"
    }
    r_temp_create = session.post(f"{BASE_URL}/api/entries", data=temp_tag_entry_data)
    temp_entry_id = r_temp_create.json()["entry_id"]
    r_tags_temp = session.get(f"{BASE_URL}/api/tags")
    del_tag_obj = next((t for t in r_tags_temp.json()["tags"] if t["name"] == "#v155tobedeleted"), None)
    assert del_tag_obj is not None

    r_del_tag = session.delete(f"{BASE_URL}/api/tags/{del_tag_obj['id']}")
    assert r_del_tag.status_code == 200, f"Delete tag failed: {r_del_tag.text}"
    print(f"✓ Successfully deleted tag ID {del_tag_obj['id']} via DELETE /api/tags/{{id}}")

    session.delete(f"{BASE_URL}/api/entries/{temp_entry_id}")

    # 7. Delete main test entry
    r_del_entry = session.delete(f"{BASE_URL}/api/entries/{entry_id}")
    assert r_del_entry.status_code == 200
    print(f"✓ Deleted test entry ID {entry_id}")

    # 8. Test Cleanup Orphan Tags: DELETE /api/tags/cleanup-orphans
    # Insert an explicit orphan tag into DB to test cleanup-orphans endpoint
    from app.database import get_db
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tags (user_id, name) VALUES (38, '#v155explicit_orphan') ON CONFLICT DO NOTHING;")

    r_tags_before_cleanup = session.get(f"{BASE_URL}/api/tags")
    assert any(t["name"] == "#v155explicit_orphan" for t in r_tags_before_cleanup.json()["tags"])

    r_cleanup = session.delete(f"{BASE_URL}/api/tags/cleanup-orphans")
    assert r_cleanup.status_code == 200, f"Cleanup orphans failed: {r_cleanup.text}"
    deleted_count = r_cleanup.json().get("deleted_count", 0)
    assert deleted_count >= 1, f"Expected at least 1 orphan deleted, got {deleted_count}"
    print(f"✓ Cleanup orphans succeeded: deleted {deleted_count} unused tags")

    # Verify no orphans remain for test tags
    r_tags_final = session.get(f"{BASE_URL}/api/tags")
    assert r_tags_final.status_code == 200
    final_tags = [t["name"] for t in r_tags_final.json()["tags"]]
    assert "#v155explicit_orphan" not in final_tags, "Orphaned #v155explicit_orphan tag should have been cleaned up"
    print("✓ All test tags cleaned up cleanly. PASS 100%!")

if __name__ == "__main__":
    test_v155_tag_manager_and_endpoints()
