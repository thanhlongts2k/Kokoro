"""
Comprehensive Automated Verification Suite for Kokoro v1.6.1
Tests:
1. Version Alignment (Config, Auth API, Service Worker, Client HTML)
2. Weather Lifecycle (Create, Read, Update entry with weather)
3. IndexedDB Sync Guard (Defense against "null" string trap & type coercion)
4. Export JSON v1.1 (Includes custom categories and entry category mappings)
5. Import JSON v1.1 with Categories & ON CONFLICT resolution
6. Backward Compatibility (v1.0 legacy JSON without categories table imports flawlessly)
7. Client UI Contract Verification (HTML, CSS tokens, editor.js, app.js)
"""

import sys
import os
import json
import unittest
from datetime import datetime
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config
from app.database import init_db, get_cursor, get_db, seed_mock_users_for_testing, clean_mock_users_after_testing
from app.auth import create_session_token

class TestV161DataIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_mock_users_for_testing()
        cls.client = TestClient(app, base_url="https://testserver")

        # Get test user (Aria Tanaka)
        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            cls.user = cur.fetchone()

        cls.user_id = cls.user["id"]
        cls.token = create_session_token(cls.user_id, cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        clean_mock_users_after_testing()

    def setUp(self):
        self.client.cookies.clear()

    def test_01_version_alignment(self):
        """Verify Config, Auth config API, and Service Worker versions are aligned with v1.6.1 or later"""
        self.assertIn(Config.APP_VERSION, ("v1.6.1", "v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3"))

        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("version"), ("v1.6.1", "v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3"))

        sw_path = Config.BASE_DIR / "static" / "sw.js"
        sw_content = sw_path.read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_content for v in ("kokoro-v1.6.1", "kokoro-v1.6.2", "kokoro-v1.6.3", "kokoro-v1.6.4", "kokoro-v1.6.5", "kokoro-v1.7.0", "kokoro-v1.7.1", "kokoro-v1.7.2", "kokoro-v1.7.3")))
        self.assertTrue(any(v in sw_content for v in ("?v=1.6.1", "?v=1.6.2", "?v=1.6.3", "?v=1.6.4", "?v=1.6.5", "?v=1.7.0", "?v=1.7.1", "?v=1.7.2", "?v=1.7.3")))

        index_path = Config.BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")
        self.assertTrue(any(v in index_content for v in ("tokens.css?v=1.6.1", "tokens.css?v=1.6.2", "tokens.css?v=1.6.3", "tokens.css?v=1.6.4", "tokens.css?v=1.6.5", "tokens.css?v=1.7.0", "tokens.css?v=1.7.1", "tokens.css?v=1.7.2", "tokens.css?v=1.7.3")))
        self.assertTrue(any(v in index_content for v in ("app.js?v=1.6.1", "app.js?v=1.6.2", "app.js?v=1.6.3", "app.js?v=1.6.4", "app.js?v=1.6.5", "app.js?v=1.7.0", "app.js?v=1.7.1", "app.js?v=1.7.2", "app.js?v=1.7.3")))

    def test_02_weather_lifecycle(self):
        """Test creating and updating entries with weather (PUT /api/entries/{id} weather = %s)"""
        # 1. Create entry with weather='rainy'
        create_payload = {
            "title": "Mưa mùa hạ 2026",
            "content": "Một ngày mưa nhẹ nhàng bên ô cửa sổ nhỏ.",
            "mood": "melancholy",
            "weather": "rainy",
            "entry_date": "2026-10-13",
            "tags": "#rain #peaceful"
        }
        res_create = self.client.post("/api/entries", data=create_payload, headers=self.headers)
        self.assertEqual(res_create.status_code, 201, f"Create entry failed: {res_create.text}")
        entry_id = res_create.json().get("entry_id")
        self.assertIsNotNone(entry_id)

        # 2. Retrieve entry and verify weather is 'rainy'
        res_get = self.client.get(f"/api/entries/{entry_id}", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)
        entry_data = res_get.json().get("entry")
        self.assertEqual(entry_data.get("weather"), "rainy")

        # 3. Update entry with weather='snowy'
        update_payload = {
            "title": "Tuyết đầu mùa 2026",
            "content": "Cơn mưa đã chuyển thành những bông tuyết trắng muốt.",
            "mood": "serene",
            "weather": "snowy",
            "entry_date": "2026-10-13",
            "tags": "#snow #cozy"
        }
        res_update = self.client.put(f"/api/entries/{entry_id}", data=update_payload, headers=self.headers)
        self.assertEqual(res_update.status_code, 200, f"Update entry failed: {res_update.text}")

        # 4. Verify entry weather was updated to 'snowy'
        res_get2 = self.client.get(f"/api/entries/{entry_id}", headers=self.headers)
        self.assertEqual(res_get2.status_code, 200)
        entry_data2 = res_get2.json().get("entry")
        self.assertEqual(entry_data2.get("weather"), "snowy")

        # Cleanup
        self.client.delete(f"/api/entries/{entry_id}", headers=self.headers)

    def test_03_indexeddb_sync_null_trap_guard(self):
        """Test backend safety against string 'null' category_id from IndexedDB sync"""
        # Sending string "null" shouldn't trigger ValueError or HTTP 500
        payload_null_str = {
            "title": "Test Null String Guard",
            "content": "Bản ghi từ IndexedDB sync với category_id là chuỗi null.",
            "category_id": "null",
            "mood": "serene",
            "weather": "sunny"
        }
        res = self.client.post("/api/entries", data=payload_null_str, headers=self.headers)
        self.assertEqual(res.status_code, 201, f"Failed with null string: {res.text}")
        entry_id = res.json().get("entry_id")

        # Verify entry has NULL category_id in DB
        with get_cursor() as cur:
            cur.execute("SELECT category_id FROM entries WHERE id = %s;", (entry_id,))
            row = cur.fetchone()
            self.assertIsNone(row["category_id"])

        self.client.delete(f"/api/entries/{entry_id}", headers=self.headers)

    def test_04_export_json_v11(self):
        """Test GET /api/entries/export exports custom categories and entry category mappings"""
        # Create a unique category
        cat_name = f"Du xuân v1.6.1 {datetime.now().microsecond}"
        cat_res = self.client.post("/api/categories", json={
            "name": cat_name,
            "icon": "🌸",
            "color": "#f472b6"
        }, headers=self.headers)
        self.assertEqual(cat_res.status_code, 201)
        cat_id = cat_res.json()["category"]["id"]

        # Create entry under this category
        entry_res = self.client.post("/api/entries", data={
            "title": "Kỷ niệm mùa xuân",
            "content": "Hoa anh đào nở rộ trên con đường xưa.",
            "category_id": str(cat_id),
            "weather": "windy"
        }, headers=self.headers)
        self.assertEqual(entry_res.status_code, 201)
        entry_id = entry_res.json()["entry_id"]

        # Call export endpoint
        export_res = self.client.get("/api/entries/export", headers=self.headers)
        self.assertEqual(export_res.status_code, 200)
        export_data = export_res.json()

        # Assert v1.1 export specs
        self.assertEqual(export_data.get("export_version"), "1.1")
        self.assertIn("categories", export_data)
        self.assertIn("entries", export_data)

        # Check category is exported
        exported_cats = {c["name"]: c for c in export_data["categories"]}
        self.assertIn(cat_name, exported_cats)

        # Check entry has category mapping
        exported_entry = next((e for e in export_data["entries"] if e["id"] == entry_id), None)
        self.assertIsNotNone(exported_entry)
        self.assertEqual(exported_entry.get("category_id"), cat_id)
        self.assertEqual(exported_entry.get("category_name"), cat_name)
        self.assertEqual(exported_entry.get("weather"), "windy")

        # Cleanup
        self.client.delete(f"/api/entries/{entry_id}", headers=self.headers)
        self.client.delete(f"/api/categories/{cat_id}", headers=self.headers)

    def test_05_import_json_v11_with_categories_and_on_conflict(self):
        """Test importing v1.1 backup payload reconciles categories and maps entry category_id"""
        unique_suffix = f"{datetime.now().microsecond}"
        cat_name_1 = f"Học tập {unique_suffix}"
        cat_name_2 = f"Du lịch {unique_suffix}"

        backup_payload = {
            "app": "Kokoro (心)",
            "version": "v1.6.1",
            "export_version": "1.1",
            "categories": [
                {"id": 9991, "name": cat_name_1, "icon": "📚", "color": "#3b82f6", "sort_order": 1},
                {"id": 9992, "name": cat_name_2, "icon": "✈️", "color": "#10b981", "sort_order": 2}
            ],
            "entries": [
                {
                    "title": "Bài viết học tập",
                    "content": "Nghiên cứu kiến trúc PWA.",
                    "category_id": 9991,
                    "category_name": cat_name_1,
                    "mood": "energetic",
                    "weather": "cloudy",
                    "entry_date": "2026-10-10",
                    "created_at": "2026-10-10T14:30:00",
                    "tags": ["#study"]
                },
                {
                    "title": "Bài viết du lịch",
                    "content": "Chuyến đi biển bình yên.",
                    "category_id": 9992,
                    "category_name": cat_name_2,
                    "mood": "serene",
                    "weather": "sunny",
                    "entry_date": "2026-10-11",
                    "tags": ["#travel"]
                }
            ]
        }

        # 1. First import
        res_import = self.client.post("/api/entries/import", json=backup_payload, headers=self.headers)
        self.assertEqual(res_import.status_code, 200, f"Import failed: {res_import.text}")
        data = res_import.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("imported_count"), 2)

        # 2. Check that categories exist and entries are linked to valid category IDs
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories WHERE user_id = %s AND name IN (%s, %s);", (self.user_id, cat_name_1, cat_name_2))
            cat_map = {r["name"]: r["id"] for r in cur.fetchall()}
            self.assertIn(cat_name_1, cat_map)
            self.assertIn(cat_name_2, cat_map)

            cur.execute("""
                SELECT id, title, category_id, weather, created_at 
                FROM entries 
                WHERE user_id = %s AND title IN ('Bài viết học tập', 'Bài viết du lịch')
                ORDER BY title ASC;
            """, (self.user_id,))
            imported_entries = cur.fetchall()
            self.assertEqual(len(imported_entries), 2)

            # Check study entry
            study_entry = next(e for e in imported_entries if e["title"] == "Bài viết học tập")
            self.assertEqual(study_entry["category_id"], cat_map[cat_name_1])
            self.assertEqual(study_entry["weather"], "cloudy")
            # Verify timestamp preservation
            self.assertEqual(study_entry["created_at"].strftime("%Y-%m-%d %H:%M"), "2026-10-10 14:30")

            # Check travel entry
            travel_entry = next(e for e in imported_entries if e["title"] == "Bài viết du lịch")
            self.assertEqual(travel_entry["category_id"], cat_map[cat_name_2])
            self.assertEqual(travel_entry["weather"], "sunny")

        # 3. Test ON CONFLICT resolution by importing again (idempotency test)
        res_reimport = self.client.post("/api/entries/import", json=backup_payload, headers=self.headers)
        self.assertEqual(res_reimport.status_code, 200, f"Re-import with ON CONFLICT failed: {res_reimport.text}")

        # Cleanup test data
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM entries WHERE user_id = %s AND title IN ('Bài viết học tập', 'Bài viết du lịch');", (self.user_id,))
                cur.execute("DELETE FROM categories WHERE user_id = %s AND name IN (%s, %s);", (self.user_id, cat_name_1, cat_name_2))

    def test_06_backward_compatibility_v10_import(self):
        """Test importing legacy v1.0 backup file without categories table or category_id works 100%"""
        legacy_backup = {
            "app": "Kokoro (心)",
            "version": "v1.0.0",
            "export_version": "1.0",
            "entries": [
                {
                    "title": "Nhật ký Kokoro v1.0 Legacy",
                    "content": "Bài viết tạo từ thời điểm hệ thống chưa có bảng categories.",
                    "mood": "serene",
                    "entry_date": "2026-09-01",
                    "tags": ["#legacy", "#memory"]
                }
            ]
        }

        res = self.client.post("/api/entries/import", json=legacy_backup, headers=self.headers)
        self.assertEqual(res.status_code, 200, f"Legacy import failed: {res.text}")
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("imported_count"), 1)

        # Verify entry was created safely with category_id = NULL and default weather
        with get_cursor() as cur:
            cur.execute("SELECT id, category_id, weather FROM entries WHERE user_id = %s AND title = 'Nhật ký Kokoro v1.0 Legacy';", (self.user_id,))
            entry = cur.fetchone()
            self.assertIsNotNone(entry)
            self.assertIsNone(entry["category_id"])
            self.assertEqual(entry["weather"], "sunny")

        # Cleanup
        self.client.delete(f"/api/entries/{entry['id']}", headers=self.headers)

    def test_07_client_ui_contract_verification(self):
        """Verify DOM elements, CSS classes, and JS methods for Weather Selector & Data Integrity"""
        base_dir = Config.BASE_DIR

        # 1. HTML Verification
        index_html = (base_dir / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="editor-weather-picker-list"', index_html)
        self.assertIn('data-weather="sunny"', index_html)
        self.assertIn('data-weather="rainy"', index_html)
        self.assertIn('data-weather="cloudy"', index_html)
        self.assertIn('data-weather="windy"', index_html)
        self.assertIn('data-weather="snowy"', index_html)
        self.assertIn('id="editor-weather-input"', index_html)

        # 2. CSS Verification
        components_css = (base_dir / "static" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn('.weather-picker-list', components_css)
        self.assertIn('.weather-chip', components_css)
        self.assertIn('.weather-chip.active', components_css)
        self.assertIn('.weather-badge-pill', components_css)

        # 3. editor.js Verification
        editor_js = (base_dir / "static" / "js" / "editor.js").read_text(encoding="utf-8")
        self.assertIn("selectedWeather: 'sunny'", editor_js)
        self.assertIn("setWeather(weather = 'sunny')", editor_js)
        self.assertIn("weather: this.selectedWeather", editor_js)
        self.assertIn("formData.append('weather', this.selectedWeather || 'sunny')", editor_js)

        # 4. api.js IndexedDB Safe Sync Verification
        api_js = (base_dir / "static" / "js" / "api.js").read_text(encoding="utf-8")
        self.assertIn("item.category_id !== 'null'", api_js)
        self.assertIn("formData.append('category_id', String(item.category_id))", api_js)

        # 5. app.js Weather Badge Verification
        app_js = (base_dir / "static" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn("weatherBadgeHtml", app_js)
        self.assertIn("weatherIcons", app_js)

if __name__ == "__main__":
    unittest.main()
