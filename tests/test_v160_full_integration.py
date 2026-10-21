"""
Integration Test Suite for Kokoro v1.6.0 Release
Verifies:
1. Version synchronization (Config, SW cache, Client script tags)
2. Client DOM & JS unification (Editor, App, TagManager)
3. End-to-end Dynamic Mood/Category Lifecycle:
   - Create category
   - Create entry with category_id
   - Fetch entries with category metadata (categoryId, categoryName, categoryIcon, categoryColor)
   - Filter entries by category_id
   - Delete category -> ON DELETE SET NULL verifies entry preservation!
"""

import sys
import os
import unittest
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from starlette.testclient import TestClient
from server import app
from app.config import Config
from app.auth import create_session_token
from app.database import get_cursor, init_db

BASE_DIR = Path(__file__).resolve().parent.parent

class TestKokoroV160FullIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            init_db()
        except Exception as e:
            raise unittest.SkipTest(f"Database not accessible in this environment: {e}")
        cls.client = TestClient(app, base_url="https://testserver")
        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users ORDER BY id ASC LIMIT 1;")
            user = cur.fetchone()
            if not user:
                cur.execute(
                    "INSERT INTO users (google_id, email, name, avatar_url) VALUES (%s, %s, %s, %s) RETURNING id, email, name;",
                    ("test_v160_full_gid", "test_v160_full@kokoro.me", "Aria Tanaka", "avatar.jpg")
                )
                user = cur.fetchone()
            cls.user = dict(user)
        cls.token = create_session_token(cls.user["id"], cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def setUp(self):
        with get_cursor() as cur:
            cur.execute("DELETE FROM categories WHERE name LIKE 'Kỷ niệm 2026%';")

    def test_01_version_alignment(self):
        """Verify Config, Auth config API, and Service Worker versions match."""
        self.assertIn(Config.APP_VERSION, ("v1.6.0", "v1.6.1", "v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2", "v1.8.5"))

        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("version"), Config.APP_VERSION)

        sw_path = BASE_DIR / "static" / "sw.js"
        sw_content = sw_path.read_text(encoding="utf-8")
        self.assertIn(f"kokoro-{Config.APP_VERSION}", sw_content)
        self.assertIn(f"?v={Config.APP_VERSION[1:]}", sw_content)

    def test_02_client_markup_and_js_integration(self):
        """Verify unified mood/category containers in HTML, editor.js, and app.js"""
        html_path = BASE_DIR / "static" / "index.html"
        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn('id="editor-mood-picker-list"', html_content)
        self.assertIn('id="editor-manage-categories-link"', html_content)
        self.assertIn('id="sidebar-mood-filters"', html_content)
        self.assertIn('id="mobile-mood-chips"', html_content)
        self.assertIn('id="memories-mood-filters"', html_content)

        editor_path = BASE_DIR / "static" / "js" / "editor.js"
        editor_content = editor_path.read_text(encoding="utf-8")
        self.assertIn("loadCategories", editor_content)
        self.assertIn("renderCategoryChips", editor_content)
        self.assertIn("selectedCategoryId", editor_content)

        app_path = BASE_DIR / "static" / "js" / "app.js"
        app_content = app_path.read_text(encoding="utf-8")
        self.assertIn("loadCategories", app_content)
        self.assertIn("renderMoodFilterChips", app_content)
        self.assertIn("renderMemoriesMoodFilterChips", app_content)
        self.assertIn("category-badge-pill", app_content)

    def test_03_end_to_end_category_lifecycle_and_data_safety(self):
        """Test full category creation, entry assignment, filtering, and deletion safety"""
        cat_name = "Kỷ niệm 2026 ✈️"
        # 1. Create custom category
        create_cat_resp = self.client.post(
            "/api/categories",
            json={"name": cat_name, "icon": "✈️", "color": "#38bdf8"},
            headers=self.headers
        )
        self.assertEqual(create_cat_resp.status_code, 201)
        cat_id = create_cat_resp.json()["category"]["id"]
        self.assertIsNotNone(cat_id)

        # 2. Create entry assigned to this category
        entry_payload = {
            "title": "Chuyến đi Mùa Thu 2026",
            "content": "Một buổi chiều ngắm lá vàng rơi tuyệt đẹp tại Kyoto.",
            "mood": "serene",
            "category_id": str(cat_id),
            "entry_date": "2026-10-12"
        }
        create_entry_resp = self.client.post(
            "/api/entries",
            data=entry_payload,
            headers=self.headers
        )
        self.assertEqual(create_entry_resp.status_code, 201)
        entry_id = create_entry_resp.json()["entry_id"]

        try:
            # 3. Fetch single entry and verify category metadata joined
            single_resp = self.client.get(f"/api/entries/{entry_id}", headers=self.headers)
            self.assertEqual(single_resp.status_code, 200)
            entry_data = single_resp.json()["entry"]
            self.assertEqual(entry_data["categoryId"], cat_id)
            self.assertEqual(entry_data["categoryName"], cat_name)
            self.assertEqual(entry_data["categoryIcon"], "✈️")
            self.assertEqual(entry_data["categoryColor"], "#38bdf8")

            # 4. Filter entries by category_id
            filter_resp = self.client.get(f"/api/entries?category_id={cat_id}", headers=self.headers)
            self.assertEqual(filter_resp.status_code, 200)
            filtered_entries = filter_resp.json()["entries"]
            self.assertTrue(any(e["id"] == entry_id for e in filtered_entries))

            # 5. Check category usage count in /api/categories
            cats_resp = self.client.get("/api/categories", headers=self.headers)
            self.assertEqual(cats_resp.status_code, 200)
            matched_cat = next((c for c in cats_resp.json()["categories"] if c["id"] == cat_id), None)
            self.assertIsNotNone(matched_cat)
            self.assertGreaterEqual(matched_cat["usage_count"], 1)

            # 6. INVARIANT CHECK: Delete category -> Entry MUST NOT be deleted (ON DELETE SET NULL)
            del_cat_resp = self.client.delete(f"/api/categories/{cat_id}", headers=self.headers)
            self.assertEqual(del_cat_resp.status_code, 200)

            # Verify entry still exists!
            after_del_resp = self.client.get(f"/api/entries/{entry_id}", headers=self.headers)
            self.assertEqual(after_del_resp.status_code, 200)
            entry_after = after_del_resp.json()["entry"]
            self.assertIsNone(entry_after["categoryId"])
            self.assertIsNone(entry_after["categoryName"])
            self.assertEqual(entry_after["title"], "Chuyến đi Mùa Thu 2026")

        finally:
            # Clean up entry
            self.client.delete(f"/api/entries/{entry_id}", headers=self.headers)

if __name__ == "__main__":
    unittest.main()
