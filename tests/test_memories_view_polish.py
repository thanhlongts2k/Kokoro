"""
KOKORO (心) — MEMORIES VIEW & HASHTAG POLISH VERIFICATION SUITE (v1.7.5)
Tests for:
1. Hashtag double hash prevention in memories-view.js
2. CSS pill styling & flex-shrink protection in components.css
3. Mobile touch overlay accessibility in components.css
4. Integration verification of memories view component contracts
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

class TestMemoriesViewPolish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_hashtag_double_hash_prevention(self):
        """Verify memories-view.js strips leading hash before rendering #${safeTag} and empty state."""
        memories_js = (BASE_DIR / "static" / "js" / "memories-view.js").read_text(encoding="utf-8")
        self.assertIn("cleanTagName = tag.replace(/^#+/, '')", memories_js, "Must clean tag before rendering")
        self.assertIn("<span>#${safeTag}</span>", memories_js, "Must render single leading hash")
        self.assertIn("cleanEmptyTag = memoriesState.tag ? memoriesState.tag.replace(/^#+/, '') : ''", memories_js, "Must clean empty state tag")

    def test_02_css_memory_mood_pill_contract(self):
        """Verify components.css defines memory-mood-pill with flex-shrink: 0 and white-space: nowrap."""
        comp_css = (BASE_DIR / "static" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn(".memories-mood-scroll .memory-mood-pill", comp_css, "Must define .memory-mood-pill styles")
        self.assertIn("flex-shrink: 0 !important", comp_css, "Must prevent mood pill squeezing")
        self.assertIn("white-space: nowrap !important", comp_css, "Must prevent mood pill label wrapping")
        self.assertIn("border-radius: 20px !important", comp_css, "Must keep pill shape")

    def test_03_mobile_touch_overlay_accessibility(self):
        """Verify mobile touch devices display c-memory-overlay gracefully without hover requirement."""
        comp_css = (BASE_DIR / "static" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn("@media (hover: none) and (pointer: coarse)", comp_css)
        self.assertIn(".c-memory-overlay", comp_css)

    def test_04_version_synchronization_v175(self):
        """Verify Config, Auth config, Health endpoint, sw.js, and index.html are synchronized to v1.7.5 or v1.7.6."""
        self.assertIn(Config.APP_VERSION, ("v1.7.5", "v1.7.6"))
        
        auth_resp = self.client.get("/api/auth/config")
        self.assertEqual(auth_resp.status_code, 200)
        self.assertIn(auth_resp.json().get("version"), ("v1.7.5", "v1.7.6"))

        health_resp = self.client.get("/api/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertIn(health_resp.json().get("version"), ("v1.7.5", "v1.7.6"))

        sw_code = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_code for v in ("kokoro-v1.7.5", "kokoro-v1.7.6")))
        self.assertTrue(any(f"./js/memories-view.js?v={v}" in sw_code for v in ("1.7.5", "1.7.6")))

        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertTrue(any(f'id="app-version-badge">{v}</span>' in html_code for v in ("v1.7.5", "v1.7.6")))
        self.assertTrue(any(f"./js/memories-view.js?v={v}" in html_code for v in ("1.7.5", "1.7.6")))

if __name__ == "__main__":
    unittest.main()
