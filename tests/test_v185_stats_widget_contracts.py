"""
Kokoro (心) Test Suite: Emotion Journey Widget Contracts & Server Stats SSoT
Covers:
1. Backend Vietnamese <-> English mood mapping in StatsRepository.MOOD_MAP
2. Backend mood normalization and aggregation for stats summary
3. REST Endpoint GET /api/stats/summary schema contract (totalEntries, totalPhotos, streakDays, moodBreakdown)
4. Client-side ProfileStats.renderStats behavioral execution in Node.js (SSoT DOM updates, fallback, empty states)
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import unittest

from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config
from app.database import init_db, get_cursor, seed_mock_users_for_testing
from app.repositories.stats_repository import StatsRepository
from app.schemas.stats import StatsSummaryDTO

BASE_DIR = Path(__file__).resolve().parent.parent


class TestStatsWidgetContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_mock_users_for_testing()
        cls._orig_mock_auth = Config.MOCK_AUTH
        Config.MOCK_AUTH = True

        cls.client = TestClient(app, base_url="https://testserver")

        with get_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            row = cur.fetchone()
            cls.user_id = row["id"] if row else 1

        resp = cls.client.post("/api/auth/mock-login", json={"user_id": cls.user_id})
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        cls.token = resp.json()["token"]
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        Config.MOCK_AUTH = cls._orig_mock_auth

    def test_01_backend_mood_mapping_and_normalization(self):
        """Verify StatsRepository.MOOD_MAP maps Vietnamese mood names to standard slugs."""
        # 1. MOOD_MAP contract
        mood_map = StatsRepository.MOOD_MAP
        self.assertIsInstance(mood_map, dict)
        self.assertEqual(mood_map.get("bình yên"), "serene")
        self.assertEqual(mood_map.get("ấm áp"), "cozy")
        self.assertEqual(mood_map.get("chiêm nghiệm"), "reflective")
        self.assertEqual(mood_map.get("biết ơn"), "grateful")
        self.assertEqual(mood_map.get("năng lượng"), "energetic")
        self.assertEqual(mood_map.get("serene"), "serene")
        self.assertEqual(mood_map.get("cozy"), "cozy")

        # 2. Test streak calculation with realistic date sequence
        today = datetime.now().date()
        consecutive_dates = [today, today - timedelta(days=1), today - timedelta(days=2)]
        streak = StatsRepository.calculate_streak_days(consecutive_dates)
        self.assertEqual(streak, 3)

        fragmented_dates = [today, today - timedelta(days=7), today - timedelta(days=8)]
        streak_frag = StatsRepository.calculate_streak_days(fragmented_dates)
        self.assertEqual(streak_frag, 1)

        empty_streak = StatsRepository.calculate_streak_days([])
        self.assertEqual(empty_streak, 0)

    def test_02_backend_stats_summary_endpoint_contract(self):
        """Verify GET /api/stats/summary returns required SSoT fields and 401 unauth."""
        # Unauthenticated request with fresh client must return 401
        unauth_client = TestClient(app, base_url="https://testserver")
        unauth_resp = unauth_client.get("/api/stats/summary")
        self.assertEqual(unauth_resp.status_code, 401)
        unauth_data = unauth_resp.json()
        self.assertEqual(unauth_data["status"], "error")

        # Authenticated request
        resp = self.client.get("/api/stats/summary", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data.get("status"), "success")
        self.assertIn("totalEntries", data)
        self.assertIn("totalPhotos", data)
        self.assertIn("streakDays", data)
        self.assertIn("moodBreakdown", data)
        self.assertIn("moodCounts", data)

        self.assertIsInstance(data["totalEntries"], int)
        self.assertIsInstance(data["totalPhotos"], int)
        self.assertIsInstance(data["streakDays"], int)
        self.assertIsInstance(data["moodBreakdown"], dict)

        for mood in ["serene", "cozy", "reflective", "grateful", "energetic"]:
            self.assertIn(mood, data["moodBreakdown"])
            self.assertIn("count", data["moodBreakdown"][mood])
            self.assertIn("percent", data["moodBreakdown"][mood])

    def test_03_frontend_stats_widget_ssot_binding_in_node(self):
        """Verify ProfileStats.renderStats DOM binding and fallbacks via Node.js runtime."""
        node_script = """
        const fs = require('fs');
        const path = require('path');

        // Mock Browser DOM with string-coercing textContent like real DOM
        const elements = {};
        global.document = {
          getElementById(id) {
            if (!elements[id]) {
              elements[id] = {
                id,
                innerHTML: '',
                _text: '',
                get textContent() { return String(this._text); },
                set textContent(v) { this._text = String(v); },
                style: {},
                classList: {
                  add: function(c) { this[c] = true; },
                  remove: function(c) { delete this[c]; }
                }
              };
            }
            return elements[id];
          },
          querySelectorAll() { return []; }
        };
        global.window = {};

        // Load profile-stats.js
        const code = fs.readFileSync(path.join(process.cwd(), 'static', 'js', 'profile-stats.js'), 'utf8');
        eval(code);
        const ProfileStats = global.ProfileStats || global.window.ProfileStats;
        if (!ProfileStats) {
          console.error('ProfileStats object not found!');
          process.exit(1);
        }

        // =========================================================================
        // SCENARIO 1: Server Stats SSoT Binding (Normal Online Mode)
        // =========================================================================
        const mockStats = {
          totalEntries: 6,
          totalPhotos: 2,
          streakDays: 1,
          moodBreakdown: {
            serene: { count: 3, percent: 50.0 },
            cozy: { count: 0, percent: 0.0 },
            reflective: { count: 2, percent: 33.3 },
            grateful: { count: 0, percent: 0.0 },
            energetic: { count: 0, percent: 0.0 }
          }
        };

        ProfileStats.renderStats({ entries: [], stats: mockStats });

        const totalEl = global.document.getElementById('stat-total-entries');
        const streakEl = global.document.getElementById('stat-writing-streak');
        const photosEl = global.document.getElementById('stat-photos-count');
        const multiBar = global.document.getElementById('stat-mood-multibar');
        const legSerene = global.document.getElementById('leg-serene');
        const legReflective = global.document.getElementById('leg-reflective');
        const legCozy = global.document.getElementById('leg-cozy');

        if (totalEl.textContent !== '6') {
          console.error('Expected totalEntries 6, got: ' + totalEl.textContent);
          process.exit(1);
        }
        if (streakEl.textContent !== '1 ngày') {
          console.error('Expected streak "1 ngày", got: ' + streakEl.textContent);
          process.exit(1);
        }
        if (!photosEl.innerHTML.includes('2 ảnh')) {
          console.error('Expected photos count "2 ảnh", got: ' + photosEl.innerHTML);
          process.exit(1);
        }
        if (legSerene.textContent !== '50%') {
          console.error('Expected legSerene "50%", got: ' + legSerene.textContent);
          process.exit(1);
        }
        if (legReflective.textContent !== '33%') {
          console.error('Expected legReflective "33%", got: ' + legReflective.textContent);
          process.exit(1);
        }
        if (legCozy.textContent !== '0%') {
          console.error('Expected legCozy "0%", got: ' + legCozy.textContent);
          process.exit(1);
        }
        if (!multiBar.innerHTML.includes('segment-serene') || !multiBar.innerHTML.includes('segment-reflective')) {
          console.error('Expected multiBar to contain serene and reflective segments, got: ' + multiBar.innerHTML);
          process.exit(1);
        }

        // =========================================================================
        // SCENARIO 2: Offline / Fallback Mode (No Server Stats, Local Vietnamese Entries)
        // =========================================================================
        const localEntries = [
          { mood: 'Bình yên', photos: [{ id: 1 }, { id: 2 }], entryDate: '2026-10-21' },
          { mood: 'Bình yên', photos: [], entryDate: '2026-10-21' },
          { mood: 'Chiêm nghiệm', photos: [{ id: 3 }], entryDate: '2026-10-20' },
          { mood: 'Công việc', photos: [], entryDate: '2026-10-19' }
        ];

        ProfileStats.renderStats({ entries: localEntries, stats: null });

        if (totalEl.textContent !== '4') {
          console.error('Fallback total should be 4, got: ' + totalEl.textContent);
          process.exit(1);
        }
        if (!photosEl.innerHTML.includes('3 ảnh')) {
          console.error('Fallback photos should count 3 photos, got: ' + photosEl.innerHTML);
          process.exit(1);
        }
        // Serene was mapped from 'Bình yên' (2 / 4 = 50%)
        if (legSerene.textContent !== '50%') {
          console.error('Fallback legSerene should be 50%, got: ' + legSerene.textContent);
          process.exit(1);
        }
        // Reflective was mapped from 'Chiêm nghiệm' (1 / 4 = 25%)
        if (legReflective.textContent !== '25%') {
          console.error('Fallback legReflective should be 25%, got: ' + legReflective.textContent);
          process.exit(1);
        }

        // =========================================================================
        // SCENARIO 3: Empty State (0 entries, null stats)
        // =========================================================================
        ProfileStats.renderStats({ entries: [], stats: null });
        if (totalEl.textContent !== '0') {
          console.error('Empty total should be 0, got: ' + totalEl.textContent);
          process.exit(1);
        }
        if (streakEl.textContent !== '0 ngày') {
          console.error('Empty streak should be "0 ngày", got: ' + streakEl.textContent);
          process.exit(1);
        }
        if (!photosEl.innerHTML.includes('0 ảnh')) {
          console.error('Empty photos should be "0 ảnh", got: ' + photosEl.innerHTML);
          process.exit(1);
        }
        if (!multiBar.innerHTML.includes('Chưa có dữ liệu')) {
          console.error('Empty multibar should show "Chưa có dữ liệu", got: ' + multiBar.innerHTML);
          process.exit(1);
        }

        console.log('NODE_STATS_WIDGET_PASS');
        """
        proc = subprocess.run(["node", "-e", node_script], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, f"Node stats widget test failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
        self.assertIn("NODE_STATS_WIDGET_PASS", proc.stdout)


if __name__ == '__main__':
    unittest.main()
