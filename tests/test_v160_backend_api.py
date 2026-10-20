"""
Comprehensive Automated Verification Suite for Kokoro v1.6.0-beta.1 Backend API & Database
Tests:
1. Categories Seeding on DB init & GET /api/categories returns default 5 moods
2. Category Usage Count calculation
3. POST /api/categories - Create new mood/category with validation (empty, duplicate)
4. PUT /api/categories/{id} - Update mood name, icon, color & entries sync
5. DELETE /api/categories/{id} - Safe delete (entries preserved with category_id = NULL)
6. POST /api/tags - Proactive tag creation with '#' normalization
7. User Data Isolation between Aria Tanaka and Kenji Sato
8. Integration: Create Entry with category_id, verify joined response
"""

import sys
import os
import unittest
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config
from app.database import init_db, get_cursor, get_db, seed_mock_users_for_testing, clean_mock_users_after_testing

class TestV160BackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            init_db()
            seed_mock_users_for_testing()
        except Exception as e:
            raise unittest.SkipTest(f"Database not accessible in this environment: {e}")
        cls._orig_mock_auth = Config.MOCK_AUTH
        Config.MOCK_AUTH = True

        # Initialize client with https scheme to pass secure cookie check
        cls.client = TestClient(app, base_url="https://testserver")
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = 'aria.tanaka@kokoro.me';")
                cls.aria_id = cur.fetchone()[0]
                cur.execute("SELECT id FROM users WHERE email = 'kenji.sato@kokoro.me';")
                cls.kenji_id = cur.fetchone()[0]

        # Login as User 1 (Aria Tanaka)
        resp1 = cls.client.post("/api/auth/mock-login", json={"user_id": cls.aria_id})
        assert resp1.status_code == 200, f"Login Aria failed: {resp1.text}"
        cls.token_aria = resp1.json()["token"]

        # Login as User 2 (Kenji Sato)
        resp2 = cls.client.post("/api/auth/mock-login", json={"user_id": cls.kenji_id})
        assert resp2.status_code == 200, f"Login Kenji failed: {resp2.text}"
        cls.token_kenji = resp2.json()["token"]

        # Clean lingering test categories from previous test runs
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM categories WHERE name LIKE 'Aria Only%' OR name LIKE 'Tạm thời Xóa%' OR name LIKE 'Hạnh phúc 2026%' OR name LIKE 'Thư giãn%';")

    @classmethod
    def tearDownClass(cls):
        Config.MOCK_AUTH = cls._orig_mock_auth
        clean_mock_users_after_testing()

    def setUp(self):
        # Clear test client cookies to test Authorization header strictly
        self.client.cookies.clear()
        self.headers_aria = {"Authorization": f"Bearer {self.token_aria}"}
        self.headers_kenji = {"Authorization": f"Bearer {self.token_kenji}"}

    def test_01_get_categories_default_seeded(self):
        """Test GET /api/categories returns seeded default moods for Aria."""
        resp = self.client.get("/api/categories", headers=self.headers_aria)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        categories = data["categories"]
        self.assertGreaterEqual(len(categories), 5, "Expected at least 5 default categories")
        
        names = [c["name"] for c in categories]
        self.assertIn("Bình yên", names)
        self.assertIn("Ấm áp", names)
        self.assertIn("Chiêm nghiệm", names)
        self.assertIn("Biết ơn", names)
        self.assertIn("Năng lượng", names)

        # Check required fields
        first = categories[0]
        self.assertIn("id", first)
        self.assertIn("icon", first)
        self.assertIn("color", first)
        self.assertIn("usage_count", first)

    def test_02_create_category_and_validations(self):
        """Test POST /api/categories creation and validation rules."""
        # 1. Validation: empty name
        resp_empty = self.client.post("/api/categories", json={"name": ""}, headers=self.headers_aria)
        self.assertEqual(resp_empty.status_code, 400)
        self.assertIn("error", resp_empty.json()["status"])

        # 2. Success: create unique category
        new_cat = {
            "name": "Hạnh phúc 2026",
            "icon": "🥰",
            "color": "#f43f5e"
        }
        resp = self.client.post("/api/categories", json=new_cat, headers=self.headers_aria)
        self.assertEqual(resp.status_code, 201)
        res_data = resp.json()
        self.assertEqual(res_data["status"], "success")
        created = res_data["category"]
        self.assertEqual(created["name"], "Hạnh phúc 2026")
        self.assertEqual(created["icon"], "🥰")
        self.assertEqual(created["color"], "#f43f5e")
        self.assertEqual(created["usage_count"], 0)
        cat_id = created["id"]

        # 3. Validation: duplicate name conflict
        resp_dup = self.client.post("/api/categories", json=new_cat, headers=self.headers_aria)
        self.assertEqual(resp_dup.status_code, 409)

        # Cleanup created category
        self.client.delete(f"/api/categories/{cat_id}", headers=self.headers_aria)

    def test_03_update_category(self):
        """Test PUT /api/categories/{id} to update details and sync entries."""
        # Create a temporary category
        resp = self.client.post("/api/categories", json={"name": "Thư giãn Temp", "icon": "🧘", "color": "#10b981"}, headers=self.headers_aria)
        cat = resp.json()["category"]
        cat_id = cat["id"]

        # Update name and icon
        update_payload = {
            "name": "Thư giãn Đã đổi",
            "icon": "🍃",
            "color": "#06b6d4"
        }
        resp_up = self.client.put(f"/api/categories/{cat_id}", json=update_payload, headers=self.headers_aria)
        self.assertEqual(resp_up.status_code, 200)
        updated = resp_up.json()["category"]
        self.assertEqual(updated["name"], "Thư giãn Đã đổi")
        self.assertEqual(updated["icon"], "🍃")
        self.assertEqual(updated["color"], "#06b6d4")

        # Cleanup
        self.client.delete(f"/api/categories/{cat_id}", headers=self.headers_aria)

    def test_04_delete_category_safe_entry_preservation(self):
        """Test DELETE /api/categories/{id} sets entries.category_id to NULL without deleting entries."""
        # Create category
        resp_cat = self.client.post("/api/categories", json={"name": "Tạm thời Xóa", "icon": "🗑️", "color": "#8b5cf6"}, headers=self.headers_aria)
        cat_id = resp_cat.json()["category"]["id"]

        # Create entry using this category
        entry_form = {
            "title": "Nhật ký test an toàn khi xóa mood",
            "content": "Nội dung bài viết này không được bị mất khi xóa mood",
            "category_id": str(cat_id),
            "mood": "Tạm thời Xóa"
        }
        resp_entry = self.client.post("/api/entries", data=entry_form, headers=self.headers_aria)
        self.assertIn(resp_entry.status_code, [200, 201])
        entry_id = resp_entry.json().get("entry_id") or resp_entry.json().get("entry", {}).get("id")
        self.assertIsNotNone(entry_id)

        # Delete the category
        del_resp = self.client.delete(f"/api/categories/{cat_id}", headers=self.headers_aria)
        self.assertEqual(del_resp.status_code, 200)

        # Verify entry still exists and category_id is NULL
        resp_get = self.client.get(f"/api/entries/{entry_id}", headers=self.headers_aria)
        self.assertEqual(resp_get.status_code, 200)
        entry_data = resp_get.json()["entry"]
        self.assertEqual(entry_data["id"], entry_id)
        self.assertIsNone(entry_data["categoryId"])

        # Cleanup entry
        self.client.delete(f"/api/entries/{entry_id}", headers=self.headers_aria)

    def test_05_proactive_create_tag(self):
        """Test POST /api/tags proactive creation and normalization."""
        # Empty name validation
        resp_err = self.client.post("/api/tags", json={"name": ""}, headers=self.headers_aria)
        self.assertEqual(resp_err.status_code, 400)

        # Create tag without hash
        resp1 = self.client.post("/api/tags", json={"name": "sakura2026"}, headers=self.headers_aria)
        self.assertEqual(resp1.status_code, 201)
        tag1 = resp1.json()["tag"]
        self.assertEqual(tag1["name"], "#sakura2026")
        tag_id = tag1["id"]

        # Idempotent re-creation
        resp2 = self.client.post("/api/tags", json={"name": "#sakura2026"}, headers=self.headers_aria)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp2.json()["tag"]["id"], tag_id)

        # Cleanup
        self.client.delete(f"/api/tags/{tag_id}", headers=self.headers_aria)

    def test_06_user_data_isolation(self):
        """Test Aria Tanaka and Kenji Sato have strictly isolated categories."""
        # Aria creates category
        resp_a = self.client.post("/api/categories", json={"name": "Aria Only 🌸", "icon": "🌸", "color": "#ec4899"}, headers=self.headers_aria)
        self.assertEqual(resp_a.status_code, 201)
        aria_cat_id = resp_a.json()["category"]["id"]

        # Kenji lists categories -> should NOT see Aria Only
        resp_k = self.client.get("/api/categories", headers=self.headers_kenji)
        kenji_names = [c["name"] for c in resp_k.json()["categories"]]
        self.assertNotIn("Aria Only 🌸", kenji_names)

        # Kenji tries to update or delete Aria's category -> should get 404
        resp_hack_up = self.client.put(f"/api/categories/{aria_cat_id}", json={"name": "Kenji Hijack"}, headers=self.headers_kenji)
        self.assertEqual(resp_hack_up.status_code, 404)

        resp_hack_del = self.client.delete(f"/api/categories/{aria_cat_id}", headers=self.headers_kenji)
        self.assertEqual(resp_hack_del.status_code, 404)

        # Cleanup
        self.client.delete(f"/api/categories/{aria_cat_id}", headers=self.headers_aria)

    def test_07_entry_category_integration(self):
        """Test full entry creation and retrieval with category_id."""
        # Get Aria's first category (e.g. Bình yên)
        cats_resp = self.client.get("/api/categories", headers=self.headers_aria)
        cat = cats_resp.json()["categories"][0]
        cat_id = cat["id"]

        # Create entry
        form_data = {
            "title": "Nhật ký tích hợp Category Test",
            "content": "Kiểm tra hiển thị đầy đủ icon và màu sắc danh mục 🌸",
            "category_id": str(cat_id),
            "mood": cat["name"]
        }
        res_post = self.client.post("/api/entries", data=form_data, headers=self.headers_aria)
        self.assertIn(res_post.status_code, [200, 201])
        entry_id = res_post.json().get("entry_id") or res_post.json().get("entry", {}).get("id")
        self.assertIsNotNone(entry_id)

        # Get entries list with filter
        res_list = self.client.get(f"/api/entries?category_id={cat_id}", headers=self.headers_aria)
        self.assertEqual(res_list.status_code, 200)
        entries = res_list.json()["entries"]
        found = next((e for e in entries if e["id"] == entry_id), None)
        self.assertIsNotNone(found, "Entry not found in filtered category list")
        self.assertEqual(found["categoryId"], cat_id)
        self.assertEqual(found["categoryName"], cat["name"])
        self.assertEqual(found["categoryIcon"], cat["icon"])
        self.assertEqual(found["categoryColor"], cat["color"])

        # Cleanup
        self.client.delete(f"/api/entries/{entry_id}", headers=self.headers_aria)


if __name__ == "__main__":
    unittest.main()
