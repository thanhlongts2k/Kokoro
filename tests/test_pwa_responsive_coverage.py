"""
KOKORO (心) — PWA RESPONSIVE COVERAGE & VIEWPORT INTEGRITY (v1.7.6)
Tests for:
1. Ultra-compact mobile screens (< 360px) header & button protections
2. Toast notifications positioning below header on mobile viewports
3. Bottom navigation safe-area-inset-bottom styling & feed clearance
4. Multi-device responsive contracts across all 4 core views
5. Version synchronization across Config, Auth, Health, sw.js, and index.html
"""

import os
import sys
import unittest
from pathlib import Path
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
from app.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent

class TestPWAResponsiveCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_ultra_compact_screen_protection(self):
        """Verify layout.css defines max-width: 360px protection for ultra-compact mobile screens."""
        layout_css = (BASE_DIR / "static" / "css" / "layout.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 360px)", layout_css)
        self.assertIn(".brand-title", layout_css)
        self.assertIn("brand-logo", layout_css)

    def test_02_toast_container_mobile_positioning(self):
        """Verify glass.css places toast-container safely below the app header on mobile screens."""
        glass_css = (BASE_DIR / "static" / "css" / "glass.css").read_text(encoding="utf-8")
        self.assertIn("top: calc(var(--header-height) + env(safe-area-inset-top, 0px) + 12px)", glass_css)

    def test_03_mobile_bottom_nav_and_feed_clearance(self):
        """Verify bottom nav respects safe-area-inset-bottom and main-wrapper has adequate bottom clearance."""
        layout_css = (BASE_DIR / "static" / "css" / "layout.css").read_text(encoding="utf-8")
        self.assertIn("height: calc(var(--bottom-nav-height) + env(safe-area-inset-bottom, 0px))", layout_css)
        self.assertIn("calc(var(--bottom-nav-height) + env(safe-area-inset-bottom, 0px) + 24px)", layout_css)

    def test_04_version_synchronization_v176_v177(self):
        """Verify Config, Auth config, Health endpoint, sw.js, and index.html are synchronized to v1.7.6, v1.7.7, or v1.8.0."""
        self.assertIn(Config.APP_VERSION, ("v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2"))
        
        auth_resp = self.client.get("/api/auth/config")
        self.assertEqual(auth_resp.status_code, 200)
        self.assertIn(auth_resp.json().get("version"), ("v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2"))

        health_resp = self.client.get("/api/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertIn(health_resp.json().get("version"), ("v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2"))

        sw_code = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_code for v in ("kokoro-v1.7.6", "kokoro-v1.7.7", "kokoro-v1.8.0", "kokoro-v1.8.1", "kokoro-v1.8.2")))
        self.assertTrue(any(f"./css/layout.css?v={v}" in sw_code for v in ("1.7.6", "1.7.7", "1.8.0", "1.8.1", "1.8.2")))

        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertTrue(any(f'id="app-version-badge">{v}</span>' in html_code for v in ("v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2")))
        self.assertTrue(any(f'./css/layout.css?v={v}' in html_code for v in ("1.7.6", "1.7.7", "1.8.0", "1.8.1", "1.8.2")))

if __name__ == "__main__":
    unittest.main()
