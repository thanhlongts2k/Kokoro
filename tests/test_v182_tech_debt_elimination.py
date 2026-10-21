"""
Test Suite: Tech Debt Sprint v1.8.2 Verification
Verifies:
1. PWA Service Worker & Manifest No-Cache Headers (fix HTTP 304).
2. pwa.js registration options (updateViaCache: 'none') & anti-loop guard.
3. Media Cleanup UI contracts: Storage Optimization Card, button & cleanup result modal with 4 metrics.
4. Maintenance endpoint rate-limiting (429 Too Many Requests on rapid calls).
5. Safe Server-Side Pagination (GET /api/entries?limit=15&offset=0 with pagination metadata).
6. Ultra-lightweight Calendar Summary (GET /api/entries/calendar-summary).
7. Hard bounds verification: entry_routes.py < 300 lines, app.js < 400 lines.
"""

import os
import sys
import unittest
from pathlib import Path
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server import app
from app.database import init_db, get_cursor, seed_mock_users_for_testing
from app.auth import create_session_token


class TestTechDebtEliminationV182(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_mock_users_for_testing()
        cls.client = TestClient(app, base_url="https://testserver")
        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            cls.user = cur.fetchone()
        cls.user_id = cls.user["id"]
        cls.token = create_session_token(cls.user_id, cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_sw_and_manifest_no_cache_headers(self):
        """Verify sw.js and manifest.webmanifest are served with strict no-cache, no-store headers."""
        # 1. sw.js
        resp_sw = self.client.get("/sw.js")
        self.assertEqual(resp_sw.status_code, 200)
        cache_ctrl = resp_sw.headers.get("Cache-Control", "")
        self.assertIn("no-cache", cache_ctrl)
        self.assertIn("no-store", cache_ctrl)
        self.assertIn("must-revalidate", cache_ctrl)
        self.assertIn("max-age=0", cache_ctrl)

        # 2. manifest.webmanifest
        resp_manifest = self.client.get("/manifest.webmanifest")
        self.assertEqual(resp_manifest.status_code, 200)
        manifest_cache = resp_manifest.headers.get("Cache-Control", "")
        self.assertIn("no-cache", manifest_cache)
        self.assertIn("no-store", manifest_cache)

    def test_02_pwa_js_registration_and_anti_loop_guard(self):
        """Verify pwa.js passes updateViaCache: 'none' and uses sessionStorage anti-loop guard."""
        pwa_code = (BASE_DIR / "static" / "js" / "pwa.js").read_text(encoding="utf-8")
        self.assertIn("updateViaCache: 'none'", pwa_code)
        self.assertIn("sessionStorage.getItem('pwa_controller_refresh_timestamp')", pwa_code)
        self.assertIn("sessionStorage.setItem('pwa_controller_refresh_timestamp'", pwa_code)

    def test_03_cleanup_ui_contracts_in_index_html(self):
        """Verify index.html contains Storage Optimization Card and Cleanup Result Modal."""
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="profile-storage-card"', html_code)
        self.assertIn('id="profile-card-cleanup-media-btn"', html_code)
        self.assertIn('id="cleanup-result-modal"', html_code)
        self.assertIn('id="cleanup-res-scanned"', html_code)
        self.assertIn('id="cleanup-res-deleted"', html_code)
        self.assertIn('id="cleanup-res-freed"', html_code)
        self.assertIn('id="cleanup-res-duration"', html_code)

    def test_04_cleanup_rate_limiting(self):
        """Verify POST /api/maintenance/cleanup-orphaned-media enforces 60s rate-limiting."""
        # First call succeeds
        resp1 = self.client.post(
            "/api/maintenance/cleanup-orphaned-media",
            headers=self.headers,
            json={"grace_period_hours": 2.0}
        )
        self.assertIn(resp1.status_code, (200, 429))

        # Second rapid call without bypass header must return 429 Too Many Requests
        resp2 = self.client.post(
            "/api/maintenance/cleanup-orphaned-media",
            headers=self.headers,
            json={"grace_period_hours": 2.0}
        )
        self.assertEqual(resp2.status_code, 429)
        self.assertIn("Vui lòng đợi", resp2.json().get("message", ""))

        # Call with bypass header succeeds
        bypass_headers = dict(self.headers)
        bypass_headers["X-Bypass-Rate-Limit"] = "true"
        resp3 = self.client.post(
            "/api/maintenance/cleanup-orphaned-media",
            headers=bypass_headers,
            json={"grace_period_hours": 2.0}
        )
        self.assertEqual(resp3.status_code, 200)

    def test_05_server_side_pagination_envelope(self):
        """Verify GET /api/entries returns pagination metadata with limit and offset."""
        resp = self.client.get("/api/entries?limit=5&offset=0", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("entries", data)
        self.assertIn("pagination", data)
        pagination = data["pagination"]
        self.assertIn("total", pagination)
        self.assertEqual(pagination["limit"], 5)
        self.assertEqual(pagination["offset"], 0)
        self.assertIn("has_more", pagination)

    def test_06_calendar_summary_endpoint(self):
        """Verify GET /api/entries/calendar-summary returns ultra-lightweight entry summary."""
        resp = self.client.get("/api/entries/calendar-summary", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("entries", data)
        if data["entries"]:
            item = data["entries"][0]
            self.assertIn("id", item)
            self.assertIn("entry_date", item)
            self.assertIn("mood", item)
            # Ensure heavy fields are NOT leaked in calendar-summary
            self.assertNotIn("content", item)
            self.assertNotIn("photos", item)

    def test_07_quantitative_file_bounds_enforcement(self):
        """Enforce strict AGENTS.md bounds: app.js < 400 lines, entry_routes.py < 300 lines."""
        app_js_lines = len((BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8").splitlines())
        entry_routes_lines = len((BASE_DIR / "app" / "routes" / "entry_routes.py").read_text(encoding="utf-8").splitlines())

        self.assertLess(app_js_lines, 400, f"static/js/app.js ({app_js_lines} lines) exceeds 400 lines threshold!")
        self.assertLess(entry_routes_lines, 300, f"app/routes/entry_routes.py ({entry_routes_lines} lines) exceeds 300 lines threshold!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
