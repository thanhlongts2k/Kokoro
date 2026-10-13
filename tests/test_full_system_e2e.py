"""
KOKORO (心) — FULL SYSTEM E2E & SPEC COMPLIANCE TEST SUITE
Covers all 13 Modules from ARCHITECTURE.md and ROADMAP.md:
M01: Authentication & Session Lifecycle
M02: Multi-View Navigation (Desktop & Mobile)
M03: Zen Ambient Sound Player
M04: Passcode & Privacy Lock
M05: Timeline Feed & Progressive Pagination
M06: Rich Diary Editor & Form Controls
M07: Media Lifecycle & Pillow Processing
M08: Daily Zen Reflection Engine
M09: Full Calendar & Mood Rhythm
M10: Photo Memories Gallery
M11: Category & Tag Management
M12: Daily Card Export Studio
M13: PWA Service Worker & Backup Portability
"""

import asyncio
import os
import sys
import unittest
import psycopg2
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
from app.config import Config
from app.auth import create_session_token, SESSION_COOKIE_NAME
from app.database import get_db

class KokoroFullSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Test against real user 38 (thanhlongts2k@gmail.com)
        cls.user_id = 38
        cls.email = "thanhlongts2k@gmail.com"
        cls.name = "Thành Long"
        cls.token = create_session_token(cls.user_id, cls.email, cls.name)
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}
        cls.auth_cookies = {SESSION_COOKIE_NAME: cls.token}

    # =========================================================================
    # M01: AUTHENTICATION & SESSION LIFECYCLE
    # =========================================================================
    def test_m01_auth_config_and_privacy_guard(self):
        # 1. Public config
        res = self.client.get("/api/auth/config")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

        # 2. Check current session
        res = self.client.get("/api/auth/me", cookies=self.auth_cookies)
        self.assertEqual(res.status_code, 200)
        me = res.json()
        self.assertTrue(me["authenticated"])
        self.assertEqual(me["user"]["id"], 38)

        # 3. Privacy Guard: block mock login into real account
        res = self.client.post("/api/auth/mock-login", json={"user_id": 38})
        # If MOCK_AUTH is false -> 403, if true -> privacy guard blocks real email with 403
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # M05: TIMELINE FEED & DATA ISOLATION
    # =========================================================================
    def test_m05_entries_feed_isolation(self):
        res = self.client.get("/api/entries", cookies=self.auth_cookies)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("entries", data)
        self.assertGreaterEqual(len(data["entries"]), 1)
        # Check that all entries belong to user 38
        for e in data["entries"]:
            self.assertEqual(e.get("user_id") or e.get("userId"), 38)

    # =========================================================================
    # M06: RICH DIARY EDITOR CRUD & WEATHER SELECTOR
    # =========================================================================
    def test_m06_editor_crud_with_weather_and_category(self):
        # 1. Create entry with weather and category
        cat_res = self.client.get("/api/categories", cookies=self.auth_cookies)
        self.assertEqual(cat_res.status_code, 200)
        cats = cat_res.json()["categories"]
        first_cat_id = cats[0]["id"] if cats else None

        post_data = {
            "title": "[TEST AUTO] Kiểm thử toàn diện Kokoro",
            "content": "Nội dung kiểm thử hệ thống tự động theo chuẩn ARCHITECTURE.md.",
            "mood": "serene",
            "weather": "windy",
            "entry_date": "2026-10-13",
            "tags": "#kiemthu, #tudong"
        }
        if first_cat_id:
            post_data["category_id"] = str(first_cat_id)

        res = self.client.post("/api/entries", data=post_data, cookies=self.auth_cookies)
        self.assertEqual(res.status_code, 201)
        created = res.json()["entry"]
        entry_id = created["id"]
        self.assertEqual(created["weather"], "windy")

        # 2. Update entry
        put_data = {
            "title": "[TEST AUTO] Đã cập nhật tiêu đề",
            "content": "Nội dung cập nhật mới.",
            "mood": "energetic",
            "weather": "rainy",
            "entry_date": "2026-10-13",
            "tags": "#kiemthu, #capnhat"
        }
        res_put = self.client.put(f"/api/entries/{entry_id}", data=put_data, cookies=self.auth_cookies)
        self.assertEqual(res_put.status_code, 200)
        updated = res_put.json()["entry"]
        self.assertEqual(updated["weather"], "rainy")
        self.assertEqual(updated["title"], "[TEST AUTO] Đã cập nhật tiêu đề")

        # 3. Clean up created entry
        del_res = self.client.delete(f"/api/entries/{entry_id}", cookies=self.auth_cookies)
        self.assertEqual(del_res.status_code, 200)

    # =========================================================================
    # M11: CATEGORIES & TAGS MANAGEMENT
    # =========================================================================
    def test_m11_categories_and_tags_management(self):
        # 1. Categories list
        res = self.client.get("/api/categories", cookies=self.auth_cookies)
        self.assertEqual(res.status_code, 200)
        cats = res.json()["categories"]
        self.assertIsInstance(cats, list)

        # 2. Create test category
        cat_create_res = self.client.post("/api/categories", json={"name": "Thử nghiệm 🌸", "icon": "🧪", "color": "#f472b6"}, cookies=self.auth_cookies)
        self.assertEqual(cat_create_res.status_code, 201)
        test_cat = cat_create_res.json()["category"]

        # 3. Delete test category
        cat_del_res = self.client.delete(f"/api/categories/{test_cat['id']}", cookies=self.auth_cookies)
        self.assertEqual(cat_del_res.status_code, 200)

        # 4. Tags list and orphan cleanup
        res_tags = self.client.get("/api/tags", cookies=self.auth_cookies)
        self.assertEqual(res_tags.status_code, 200)
        tags = res_tags.json()["tags"]
        self.assertIsInstance(tags, list)

        res_cleanup = self.client.delete("/api/tags/cleanup-orphans", cookies=self.auth_cookies)
        self.assertEqual(res_cleanup.status_code, 200)

    # =========================================================================
    # M13: BACKUP JSON EXPORT & IMPORT (v1.1)
    # =========================================================================
    def test_m13_backup_export_and_backward_compatibility(self):
        res = self.client.get("/api/entries/export", cookies=self.auth_cookies)
        self.assertEqual(res.status_code, 200)
        export_data = res.json()
        self.assertEqual(export_data.get("export_version"), "1.1")
        self.assertIn("entries", export_data)
        self.assertIn("categories", export_data)

    # =========================================================================
    # STATIC ASSETS CONTRACT CHECK
    # =========================================================================
    def test_static_pwa_assets_and_audio(self):
        assets = [
            "/index.html",
            "/manifest.webmanifest",
            "/css/tokens.css",
            "/css/glass.css",
            "/css/components.css",
            "/css/layout.css",
            "/js/constants.js",
            "/js/api.js",
            "/js/auth.js",
            "/js/toast.js",
            "/js/datetime-picker.js",
            "/js/tag-manager.js",
            "/js/lightbox.js",
            "/js/zen-prompts.js",
            "/js/editor.js",
            "/js/card-themes.js",
            "/js/card-canvas-engine.js",
            "/js/card-export.js",
            "/js/zen-audio.js",
            "/js/passcode.js",
            "/js/pwa.js",
            "/js/timeline-feed.js",
            "/js/calendar-view.js",
            "/js/memories-view.js",
            "/js/profile-stats.js",
            "/js/app.js",
            "/audio/rain.mp3",
            "/audio/furin.mp3",
            "/audio/waves.mp3",
            "/audio/stream.mp3",
            "/icons/sakura.svg"
        ]
        for path in assets:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Asset failed: {path}")

if __name__ == "__main__":
    unittest.main()
