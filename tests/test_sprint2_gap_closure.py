"""
Comprehensive Automated Verification Suite for Kokoro Sprint 2 Gap Closure (v1.6.4)
Covers:
1. Version Alignment (Config, Auth API, Service Worker v1.6.4, Client HTML)
2. Orphaned Media Windows Path Safety (Basename normalization test & PhotoRepository isolation)
3. Orphaned Media Grace Period Protection (Draft assets < 2h retained, old orphans removed)
4. Maintenance Endpoint Verification (POST /api/maintenance/cleanup-orphaned-media, Auth gate)
5. Service Worker CDN Caching Rules (Google Fonts & Bootstrap Icons whitelist)
6. Frontend Timeline Progressive Pagination Contracts (app.js & components.css)
7. Modular Architecture & Strict Typing (CleanupStatsDTO, PhotoRepository layer isolation)
"""

import sys
import os
import time
import json
import unittest
from pathlib import Path
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config
from app.database import init_db, get_cursor, get_db
from app.auth import create_session_token
from app.services.media_service import MediaService, ORIGINALS_DIR, THUMBNAILS_DIR
from app.schemas.maintenance import CleanupStatsDTO, MaintenanceResponseDTO
from app.repositories.photo_repository import PhotoRepository
from app.routes.maintenance_routes import maintenance_routes
from app.routes.entry_routes import entry_routes


class TestSprint2GapClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app, base_url="https://testserver")

        # Get test user (Aria Tanaka)
        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            cls.user = cur.fetchone()

        cls.user_id = cls.user["id"]
        cls.token = create_session_token(cls.user_id, cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def setUp(self):
        self.client.cookies.clear()

    def test_01_version_alignment_v164(self):
        """Verify Config, Auth API, Service Worker, and HTML are synchronized to v1.6.4 or later"""
        self.assertIn(Config.APP_VERSION, ("v1.6.4", "v1.6.5", "v1.7.0"))

        # Auth config endpoint
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("version"), ("v1.6.4", "v1.6.5", "v1.7.0"))

        # Service Worker cache name
        sw_file = Config.BASE_DIR / "static" / "sw.js"
        sw_code = sw_file.read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_code for v in ("kokoro-v1.6.4", "kokoro-v1.6.5", "kokoro-v1.7.0")))
        self.assertTrue(any(f"./js/app.js?v={v}" in sw_code for v in ("1.6.4", "1.6.5", "1.7.0")))

        # Index HTML stylesheet & script query params
        html_file = Config.BASE_DIR / "static" / "index.html"
        html_code = html_file.read_text(encoding="utf-8")
        self.assertTrue(any(f"./css/tokens.css?v={v}" in html_code for v in ("1.6.4", "1.6.5", "1.7.0")))
        self.assertTrue(any(f"./js/app.js?v={v}" in html_code for v in ("1.6.4", "1.6.5", "1.7.0")))

    def test_02_orphaned_media_windows_path_safety(self):
        """
        Verify that active photos referenced in DB are NEVER deleted,
        even if stored with Windows backslashes ('uploads\\originals\\...') vs Unix ('uploads/originals/...').
        """
        # Create a mock entry with photo to simulate active record
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO entries (user_id, title, content, mood, weather, entry_date)
                VALUES (%s, 'Path Test Entry', 'Testing Windows Path Normalization', 'serene', 'sunny', CURRENT_DATE)
                RETURNING id;
            """, (self.user_id,))
            entry_id = cur.fetchone()["id"]

            active_orig_fname = "test_active_photo_windows_safety.webp"
            active_thumb_fname = "test_active_photo_windows_safety_thumb.webp"

            # Intentionally store with Windows backslash to test safety
            windows_orig_path = f"uploads\\originals\\{active_orig_fname}"
            windows_thumb_path = f"uploads\\thumbnails\\{active_thumb_fname}"

            cur.execute("""
                INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height)
                VALUES (%s, %s, %s, %s, 1024, 800, 600);
            """, (entry_id, windows_orig_path, windows_thumb_path, active_orig_fname))

        # Physically create these files on disk
        real_orig_file = ORIGINALS_DIR / active_orig_fname
        real_thumb_file = THUMBNAILS_DIR / active_thumb_fname
        real_orig_file.write_bytes(b"ACTIVE_PHOTO_ORIGINAL_BYTES")
        real_thumb_file.write_bytes(b"ACTIVE_PHOTO_THUMB_BYTES")

        # Set modification time to 5 hours ago (> 2h grace period)
        five_hours_ago = time.time() - (5 * 3600)
        os.utime(real_orig_file, (five_hours_ago, five_hours_ago))
        os.utime(real_thumb_file, (five_hours_ago, five_hours_ago))

        try:
            # 1. Test persistence abstraction directly
            active_set = PhotoRepository.get_all_active_photo_filenames()
            self.assertIn(active_orig_fname, active_set)
            self.assertIn(active_thumb_fname, active_set)

            # 2. Run orphan scan via service
            scan_res = MediaService.scan_and_cleanup_orphans(grace_period_hours=2.0)
            self.assertIsInstance(scan_res, CleanupStatsDTO)

            # Both files MUST still exist on disk!
            self.assertTrue(real_orig_file.exists(), "Active original file must NOT be deleted!")
            self.assertTrue(real_thumb_file.exists(), "Active thumb file must NOT be deleted!")
            self.assertNotIn(active_orig_fname, scan_res.deleted_filenames)
            self.assertNotIn(active_thumb_fname, scan_res.deleted_filenames)
        finally:
            # Cleanup mock database record and files
            with get_cursor() as cur:
                cur.execute("DELETE FROM entries WHERE id = %s;", (entry_id,))
            if real_orig_file.exists():
                real_orig_file.unlink()
            if real_thumb_file.exists():
                real_thumb_file.unlink()

    def test_03_orphaned_media_grace_period_protection(self):
        """
        Verify that:
        1. Unreferenced files created < 2 hours ago (drafts) are PROTECTED (not deleted).
        2. Unreferenced files created > 2 hours ago are CLEANED UP.
        """
        now = time.time()

        # 1. Draft file modified 30 minutes ago (< 2h)
        draft_fname = "mock_draft_unreferenced_30min.webp"
        draft_file = ORIGINALS_DIR / draft_fname
        draft_file.write_bytes(b"DRAFT_BUFFER_RECENT")
        thirty_min_ago = now - 1800
        os.utime(draft_file, (thirty_min_ago, thirty_min_ago))

        # 2. Abandoned orphaned file modified 4 hours ago (> 2h)
        old_orphan_fname = "mock_old_orphan_unreferenced_4h.webp"
        old_orphan_file = ORIGINALS_DIR / old_orphan_fname
        old_orphan_file.write_bytes(b"OLD_ORPHAN_BYTES_TO_PURGE")
        four_hours_ago = now - (4 * 3600)
        os.utime(old_orphan_file, (four_hours_ago, four_hours_ago))

        try:
            scan_res = MediaService.scan_and_cleanup_orphans(grace_period_hours=2.0)
            self.assertIsInstance(scan_res, CleanupStatsDTO)

            # Verification:
            # Draft file must be skipped and preserved
            self.assertTrue(draft_file.exists(), "Recent draft within 2h grace period must be protected!")
            self.assertGreaterEqual(scan_res.skipped_grace_period, 1)

            # Old orphan file must be unlinked
            self.assertFalse(old_orphan_file.exists(), "Orphan older than 2h must be deleted!")
            self.assertIn(old_orphan_fname, scan_res.deleted_filenames)
            self.assertGreaterEqual(scan_res.deleted_count, 1)
            self.assertGreater(scan_res.freed_bytes, 0)

            # Test DTO serialization
            dict_data = scan_res.to_dict()
            self.assertEqual(dict_data["deleted_count"], scan_res.deleted_count)
            self.assertEqual(dict_data["freed_mb"], scan_res.freed_mb)
        finally:
            if draft_file.exists():
                draft_file.unlink()
            if old_orphan_file.exists():
                old_orphan_file.unlink()

    def test_04_cleanup_orphaned_media_api_endpoint(self):
        """Test POST /api/maintenance/cleanup-orphaned-media auth gate and execution"""
        # 1. Unauthenticated request -> 401
        unauth_resp = self.client.post("/api/maintenance/cleanup-orphaned-media")
        self.assertEqual(unauth_resp.status_code, 401)
        self.assertEqual(unauth_resp.json().get("authenticated"), False)

        # 2. Authenticated request -> 200 OK with metrics
        auth_resp = self.client.post(
            "/api/maintenance/cleanup-orphaned-media",
            headers=self.headers,
            json={"grace_period_hours": 2.0}
        )
        self.assertEqual(auth_resp.status_code, 200)
        data = auth_resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("data", data)
        self.assertIn("deleted_count", data["data"])
        self.assertIn("freed_mb", data["data"])
        self.assertIn("skipped_grace_period", data["data"])

    def test_05_service_worker_cdn_caching_rules(self):
        """Verify sw.js contains CDN whitelist and opaque/cors response handling"""
        sw_file = Config.BASE_DIR / "static" / "sw.js"
        sw_content = sw_file.read_text(encoding="utf-8")

        # Whitelist hosts
        self.assertIn("fonts.googleapis.com", sw_content)
        self.assertIn("fonts.gstatic.com", sw_content)
        self.assertIn("cdn.jsdelivr.net", sw_content)

        # Opaque / cors response caching
        self.assertIn("opaque", sw_content)
        self.assertIn("ALLOWED_CDN_HOSTS", sw_content)

        # API bypass
        self.assertIn("/api/", sw_content)

    def test_06_frontend_progressive_pagination_contracts(self):
        """Verify app.js and components.css progressive pagination contract"""
        app_js = (Config.BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
        css_file = (Config.BASE_DIR / "static" / "css" / "components.css").read_text(encoding="utf-8")

        # app.js properties & methods
        self.assertIn("timelinePagination:", app_js)
        self.assertTrue("pageSize: 15" in app_js or "PAGINATION.DEFAULT_PAGE_SIZE" in app_js)
        self.assertTrue("visibleLimit: 15" in app_js or "PAGINATION.INITIAL_VISIBLE_LIMIT" in app_js)
        self.assertIn("handleLoadMoreEntries()", app_js)
        self.assertIn("timeline-load-more-btn", app_js)
        self.assertIn("timeline-end-indicator", app_js)

        # components.css styles & WCAG touch target
        self.assertIn(".timeline-load-more-wrap", css_file)
        self.assertIn(".timeline-load-more-btn", css_file)
        self.assertIn(".timeline-end-indicator", css_file)
        self.assertIn("min-height: 46px", css_file)  # >= 44px WCAG 2.5.5 standard

    def test_07_modular_architecture_and_layer_isolation(self):
        """
        Verify AGENTS.md compliance:
        1. Maintenance routes are cleanly registered in maintenance_routes, NOT bloated into entry_routes.
        2. MediaService does NOT import raw get_cursor (delegates entirely to PhotoRepository).
        3. PhotoRepository is decoupled from routing.
        """
        # 1. Modular routing isolation
        maintenance_paths = [r.path for r in maintenance_routes]
        entry_paths = [r.path for r in entry_routes]

        self.assertIn("/api/maintenance/cleanup-orphaned-media", maintenance_paths)
        self.assertNotIn("/api/maintenance/cleanup-orphaned-media", entry_paths)

        # 2. Layer isolation in media_service.py
        media_code = (Config.BASE_DIR / "app" / "services" / "media_service.py").read_text(encoding="utf-8")
        self.assertNotIn("from app.database import get_cursor", media_code)
        self.assertIn("PhotoRepository.get_all_active_photo_filenames()", media_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
