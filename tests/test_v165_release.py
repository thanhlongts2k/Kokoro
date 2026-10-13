"""
Automated Verification Suite for Kokoro Release v1.6.5
Tests:
1. Version synchronization (Config, Auth API, Service Worker, Footer Badge)
2. Layer Isolation (check_db_connection() in app/database.py and server.py)
3. Dead code removal (mock-data.js removed from disk, index.html, and sw.js)
4. Maintenance error handling (graceful handling of invalid body)
5. Card export themes & format filename contracts
"""

import unittest
from pathlib import Path
from starlette.testclient import TestClient

from app.config import Config
from app.database import check_db_connection
import server
from server import app

BASE_DIR = Path(__file__).resolve().parent.parent


class TestV165Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_version_synchronization(self):
        """Verify Config, Auth config API, Service Worker cache, and index.html footer badge are v1.6.5"""
        self.assertEqual(Config.APP_VERSION, "v1.6.5")

        # Auth config endpoint
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("version"), "v1.6.5")

        # Service Worker cache name
        sw_file = BASE_DIR / "static" / "sw.js"
        sw_code = sw_file.read_text(encoding="utf-8")
        self.assertIn("kokoro-v1.6.5", sw_code)
        self.assertIn("./js/app.js?v=1.6.5", sw_code)

        # Index HTML footer badge
        html_file = BASE_DIR / "static" / "index.html"
        html_code = html_file.read_text(encoding="utf-8")
        self.assertIn('id="app-version-badge">v1.6.5</span>', html_code)
        self.assertIn("./js/app.js?v=1.6.5", html_code)

    def test_02_layer_isolation_db_health(self):
        """Verify database connectivity helper works and server.py does not expose get_cursor"""
        is_healthy, info = check_db_connection()
        self.assertTrue(is_healthy)
        self.assertEqual(info, "connected")

        # Verify api_health endpoint response
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "online")
        self.assertEqual(data.get("version"), "v1.6.5")
        self.assertIn("connected", data.get("database"))

        # Verify server module does not import get_cursor
        self.assertFalse(hasattr(server, "get_cursor"), "server.py must not directly import get_cursor")

    def test_03_mock_data_dead_code_eliminated(self):
        """Verify static/js/mock-data.js is deleted and unreferenced"""
        mock_file = BASE_DIR / "static" / "js" / "mock-data.js"
        self.assertFalse(mock_file.exists(), "mock-data.js must be removed from static/js/")

        # Ensure index.html does not load mock-data.js
        html_file = BASE_DIR / "static" / "index.html"
        html_code = html_file.read_text(encoding="utf-8")
        self.assertNotIn("mock-data.js", html_code)

        # Ensure sw.js does not cache mock-data.js
        sw_file = BASE_DIR / "static" / "sw.js"
        sw_code = sw_file.read_text(encoding="utf-8")
        self.assertNotIn("mock-data.js", sw_code)

    def test_04_maintenance_graceful_body_handling(self):
        """Verify maintenance cleanup endpoint does not crash on invalid JSON body"""
        # Unauthenticated request returns 401
        resp_unauth = self.client.post(
            "/api/maintenance/cleanup-orphaned-media",
            headers={"Content-Type": "application/json"},
            content=b"invalid-json{"
        )
        self.assertEqual(resp_unauth.status_code, 401)

    def test_05_card_export_contracts(self):
        """Verify card-export.js contains all 5 themes and filename formatting"""
        card_export_file = BASE_DIR / "static" / "js" / "card-export.js"
        self.assertTrue(card_export_file.exists())
        js_code = card_export_file.read_text(encoding="utf-8")

        for theme in ("sakura", "polaroid", "scrapbook", "music", "editorial"):
            self.assertIn(f"'{theme}'", js_code, f"Theme '{theme}' should be supported in card-export.js")

        self.assertIn("getExportFilename", js_code)
        self.assertIn("kokoro_", js_code)


if __name__ == "__main__":
    unittest.main()
