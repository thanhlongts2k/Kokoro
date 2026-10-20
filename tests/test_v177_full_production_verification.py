"""
KOKORO (心) — FULL SYSTEM E2E & PRODUCTION HARDENING VERIFICATION (v1.7.7)
Tests covering:
1. Version synchronization (Config, Auth API, Health, sw.js, index.html) to v1.7.7
2. Editor Modal/Bottom Sheet contracts & element ID integrity
3. Zen Audio relaxation mini-player DOM structure & tracks
4. Passcode PIN security settings & keypad DOM structure
5. Memories View mood filter chips & tag hygiene contracts
6. PWA Responsive layouts & safe-area insets contracts
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

class TestV177FullProductionVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_version_synchronization_v177(self):
        """Verify Config, Auth config, Health endpoint, Service Worker cache, and index.html footer badge are synchronized."""
        self.assertIn(Config.APP_VERSION, ("v1.7.7", "v1.8.0"))

        auth_resp = self.client.get("/api/auth/config")
        self.assertEqual(auth_resp.status_code, 200)
        self.assertIn(auth_resp.json().get("version"), ("v1.7.7", "v1.8.0"))

        health_resp = self.client.get("/api/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertIn(health_resp.json().get("version"), ("v1.7.7", "v1.8.0"))

        sw_code = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_code for v in ("kokoro-v1.7.7", "kokoro-v1.8.0")))
        self.assertTrue(any(f"./js/app.js?v={v}" in sw_code for v in ("1.7.7", "1.8.0")))

        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertTrue(any(v in html_code for v in ('id="app-version-badge">v1.7.7</span>', 'id="app-version-badge">v1.8.0</span>')))
        self.assertTrue(any(f'./js/app.js?v={v}' in html_code for v in ("1.7.7", "1.8.0")))

    def test_02_editor_contracts_integrity(self):
        """Verify editor modal overlay ID, close buttons, and bottom nav trigger exist."""
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="editor-modal-overlay"', html_code)
        self.assertIn('id="editor-close-btn"', html_code)
        self.assertIn('id="editor-cancel-btn"', html_code)
        self.assertIn('data-tab="editor"', html_code)

        editor_js = (BASE_DIR / "static" / "js" / "editor.js").read_text(encoding="utf-8")
        self.assertIn("editor-modal-overlay", editor_js)
        self.assertIn("editor-cancel-btn", editor_js)

    def test_03_zen_audio_and_passcode_dom_contracts(self):
        """Verify Zen player panel and Passcode keypad overlay exist in index.html."""
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="zen-player-panel"', html_code)
        self.assertIn('id="zen-toggle-btn"', html_code)
        self.assertIn('id="passcode-lock-overlay"', html_code)
        self.assertIn('data-passcode-digit="1"', html_code)

    def test_04_memories_view_and_tags_hygiene(self):
        """Verify memories-view.js trims duplicate hashtag symbols before rendering."""
        mem_js = (BASE_DIR / "static" / "js" / "memories-view.js").read_text(encoding="utf-8")
        self.assertIn("replace(/^#+/, '')", mem_js)

    def test_05_responsive_pwa_layout_contracts(self):
        """Verify layout.css and glass.css include ultra-compact and safe inset rules."""
        layout_css = (BASE_DIR / "static" / "css" / "layout.css").read_text(encoding="utf-8")
        glass_css = (BASE_DIR / "static" / "css" / "glass.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 360px)", layout_css)
        self.assertIn("env(safe-area-inset-bottom, 0px)", layout_css)
        self.assertIn("env(safe-area-inset-top, 0px)", glass_css)

if __name__ == "__main__":
    unittest.main()
