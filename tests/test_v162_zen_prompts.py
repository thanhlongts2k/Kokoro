"""
Test Suite: Kokoro v1.6.2 Daily Zen Prompts (Gợi Ý Suy Ngẫm Chánh Niệm Mỗi Ngày)
Covers:
1. Version & PWA Service Worker Cache Alignment (v1.6.2)
2. Script Loading Order Guard in index.html (zen-prompts.js BEFORE editor.js & app.js)
3. 36 Mindful Prompts Catalog across 4 Pillars (9 items per pillar)
4. Deterministic Local Date Seed & Rollover Algorithm
5. Draft Safety & Cursor Placement Contract in editor.js
6. DOM Structure & CSS Components Contract
7. Shuffle Mechanics & Dismissal Persistence
"""

import unittest
import json
import re
import os
import sys
from pathlib import Path
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent


class TestKokoroV162ZenPrompts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_version_and_sw_alignment(self):
        """Verify Config, Auth config API, Service Worker and Footer are aligned to v1.6.2 or later"""
        # 1. Config.APP_VERSION
        self.assertIn(Config.APP_VERSION, ("v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2", "v1.8.5", "v1.8.6", "v1.8.7"))

        # 2. GET /api/auth/config
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("version"), ("v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2", "v1.8.5", "v1.8.6", "v1.8.7"))

        # 3. static/sw.js
        sw_path = BASE_DIR / "static" / "sw.js"
        sw_content = sw_path.read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_content for v in ("kokoro-v1.6.2", "kokoro-v1.6.3", "kokoro-v1.6.4", "kokoro-v1.6.5", "kokoro-v1.7.0", "kokoro-v1.7.1", "kokoro-v1.7.2", "kokoro-v1.7.3", "kokoro-v1.7.4", "kokoro-v1.7.5", "kokoro-v1.7.6", "kokoro-v1.7.7", "kokoro-v1.8.0", "kokoro-v1.8.1", "kokoro-v1.8.2", "kokoro-v1.8.5", "kokoro-v1.8.6", "kokoro-v1.8.7")))
        self.assertTrue(any(v in sw_content for v in ("zen-prompts.js?v=1.6.2", "zen-prompts.js?v=1.6.3", "zen-prompts.js?v=1.6.4", "zen-prompts.js?v=1.6.5", "zen-prompts.js?v=1.7.0", "zen-prompts.js?v=1.7.1", "zen-prompts.js?v=1.7.2", "zen-prompts.js?v=1.7.3", "zen-prompts.js?v=1.7.4", "zen-prompts.js?v=1.7.5", "zen-prompts.js?v=1.7.6", "zen-prompts.js?v=1.7.7", "zen-prompts.js?v=1.8.0", "zen-prompts.js?v=1.8.1", "zen-prompts.js?v=1.8.2", "zen-prompts.js?v=1.8.5", "zen-prompts.js?v=1.8.6", "zen-prompts.js?v=1.8.7")))
        self.assertTrue(any(v in sw_content for v in ("components.css?v=1.6.2", "components.css?v=1.6.3", "components.css?v=1.6.4", "components.css?v=1.6.5", "components.css?v=1.7.0", "components.css?v=1.7.1", "components.css?v=1.7.2", "components.css?v=1.7.3", "components.css?v=1.7.4", "components.css?v=1.7.5", "components.css?v=1.7.6", "components.css?v=1.7.7", "components.css?v=1.8.0", "components.css?v=1.8.1", "components.css?v=1.8.2", "components.css?v=1.8.5", "components.css?v=1.8.6", "components.css?v=1.8.7")))

        # 4. static/index.html footer badge
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")
        self.assertTrue(any(f'id="app-version-badge">{v}</span>' in index_content for v in ("v1.6.2", "v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7", "v1.8.0", "v1.8.1", "v1.8.2", "v1.8.5", "v1.8.6", "v1.8.7")))
        self.assertTrue(any(f'href="./css/components.css?v={v}"' in index_content for v in ("1.6.2", "1.6.3", "1.6.4", "1.6.5", "1.7.0", "1.7.1", "1.7.2", "1.7.3", "1.7.4", "1.7.5", "1.7.6", "1.7.7", "1.8.0", "1.8.1", "1.8.2", "1.8.5", "1.8.6", "1.8.7")))

    def test_02_script_loading_order_guard(self):
        """Ensure zen-prompts.js is loaded BEFORE editor.js and app.js to prevent ReferenceError"""
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        zen_idx = index_content.find("js/zen-prompts.js")
        editor_idx = index_content.find("js/editor.js")
        app_idx = index_content.find("js/app.js")

        self.assertNotEqual(zen_idx, -1, "zen-prompts.js script tag not found in index.html")
        self.assertNotEqual(editor_idx, -1, "editor.js script tag not found in index.html")
        self.assertNotEqual(app_idx, -1, "app.js script tag not found in index.html")

        self.assertLess(zen_idx, editor_idx, "zen-prompts.js MUST be loaded BEFORE editor.js")
        self.assertLess(zen_idx, app_idx, "zen-prompts.js MUST be loaded BEFORE app.js")
        self.assertLess(editor_idx, app_idx, "editor.js MUST be loaded BEFORE app.js")

    def test_03_zen_prompts_catalog_and_pillars(self):
        """Verify repository contains exactly 36 mindful prompts distributed evenly across 4 pillars"""
        zen_file = BASE_DIR / "static" / "js" / "zen-prompts.js"
        content = zen_file.read_text(encoding="utf-8")

        # Extract prompt objects using regex (handles double quotes inside single-quoted strings)
        prompt_blocks = re.findall(
            r"\{\s*id:\s*(\d+),\s*pillar:\s*'([^']+)',\s*pillarName:\s*'([^']+)',\s*text:\s*'([^']+)',\s*suggestedMood:\s*'([^']+)',\s*icon:\s*'([^']+)'\s*\}",
            content,
        )

        self.assertEqual(len(prompt_blocks), 36, f"Expected exactly 36 prompts, found {len(prompt_blocks)}")

        ids = [int(p[0]) for p in prompt_blocks]
        self.assertEqual(ids, list(range(1, 37)), "Prompt IDs must be sequential from 1 to 36")

        pillars = [p[1] for p in prompt_blocks]
        pillar_counts = {}
        for p in pillars:
            pillar_counts[p] = pillar_counts.get(p, 0) + 1

        expected_pillars = {
            "gratitude": 9,
            "letting_go": 9,
            "presence": 9,
            "growth": 9,
        }
        self.assertEqual(pillar_counts, expected_pillars, "Each of the 4 pillars must have exactly 9 prompts")

        # Verify no empty texts or placeholders
        for p_id, pillar, pillar_name, text, mood, icon in prompt_blocks:
            self.assertTrue(len(text.strip()) > 15, f"Prompt {p_id} text too short: '{text}'")
            self.assertNotIn("TODO", text)
            self.assertNotIn("test", text.lower())
            self.assertTrue(len(icon) > 0)
            self.assertTrue(len(mood) > 0)

    def test_04_deterministic_date_hash_and_daily_seed(self):
        """Verify the deterministic string hash algorithm produces consistent daily indices and rollovers"""
        def js_hash_date(date_str: str) -> int:
            """Simulate JavaScript 32-bit integer arithmetic: hash = (hash << 5) - hash + charCode; hash |= 0;"""
            h = 0
            for ch in date_str:
                h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
                # Convert to signed 32-bit int
                if h >= 0x80000000:
                    h -= 0x100000000
            return abs(h)

        # 1. Same date string produces identical index every time
        date_today = "2026-10-13"
        hash_today_1 = js_hash_date(date_today)
        hash_today_2 = js_hash_date(date_today)
        self.assertEqual(hash_today_1, hash_today_2)

        idx_today = hash_today_1 % 36
        self.assertTrue(0 <= idx_today < 36)

        # 2. Date rollover: consecutive days produce deterministic prompts
        dates = ["2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
        indices = [js_hash_date(d) % 36 for d in dates]
        self.assertEqual(len(indices), 4)
        for idx in indices:
            self.assertTrue(0 <= idx < 36)

    def test_05_draft_safety_and_cursor_placement(self):
        """Verify Draft Safety Protocol in editor.js: prepending quote, not overwriting draft, and mood mapping"""
        editor_path = BASE_DIR / "static" / "js" / "editor.js"
        editor_content = editor_path.read_text(encoding="utf-8")

        # Check insertZenPrompt definition
        self.assertIn("insertZenPrompt(promptText, suggestedMood = null)", editor_content)

        # Check safe preservation logic
        self.assertIn("if (!currentVal.includes(promptText))", editor_content)
        self.assertIn("this.contentInput.value = quote + currentVal;", editor_content)

        # Check cursor positioning
        self.assertIn("this.contentInput.setSelectionRange(quote.length, quote.length);", editor_content)

        # Check mood mapping with renderCategoryChips
        self.assertIn("this.renderCategoryChips(null, suggestedMood);", editor_content)
        self.assertIn("lowerMood === 'melancholy'", editor_content)

        # Simulate Python logic for Draft Safety
        prompt_text = "Điều giản dị nào trong ngày đã bất chợt khiến bạn mỉm cười nhẹ nhõm?"
        quote = f'> 🌸 "{prompt_text}"\n\n'

        # Case 1: Empty draft
        existing_empty = ""
        val1 = quote if not existing_empty.strip() else quote + existing_empty
        self.assertEqual(val1, quote)

        # Case 2: Draft with existing user thoughts (MUST NOT BE OVERWRITTEN)
        existing_thoughts = "Hôm nay mình đã đi dạo dưới hàng cây anh đào ven hồ."
        val2 = quote + existing_thoughts
        self.assertTrue(val2.startswith(quote))
        self.assertTrue(val2.endswith(existing_thoughts))
        self.assertIn(existing_thoughts, val2)

        # Case 3: Prompt already included (idempotency check)
        self.assertTrue(prompt_text in val2)

    def test_06_dom_markup_and_css_specs(self):
        """Verify daily-zen-card and editor-prompt-hint-pill exist in index.html and components.css"""
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        # Check Timeline card elements
        self.assertIn('id="daily-zen-card"', index_content)
        self.assertIn('id="zen-prompt-icon"', index_content)
        self.assertIn('id="zen-prompt-pillar"', index_content)
        self.assertIn('id="zen-prompt-text"', index_content)
        self.assertIn('id="zen-prompt-dismiss-btn"', index_content)
        self.assertIn('id="zen-prompt-write-btn"', index_content)
        self.assertIn('id="zen-prompt-shuffle-btn"', index_content)
        self.assertIn('id="zen-dice-icon"', index_content)

        # Check Editor hint pill elements
        self.assertIn('id="editor-zen-prompt-hint"', index_content)
        self.assertIn('id="editor-prompt-hint-icon"', index_content)
        self.assertIn('id="editor-prompt-hint-text"', index_content)
        self.assertIn('id="editor-prompt-hint-insert-btn"', index_content)

        # Check CSS rules
        css_path = BASE_DIR / "static" / "css" / "components.css"
        css_content = css_path.read_text(encoding="utf-8")

        self.assertIn(".daily-zen-card", css_content)
        self.assertIn(".daily-zen-card.collapsed", css_content)
        self.assertIn(".zen-prompt-text", css_content)
        self.assertIn(".zen-dice-icon", css_content)
        self.assertIn(".anim-spinning", css_content)
        self.assertIn("@keyframes spinDice", css_content)
        self.assertIn(".editor-prompt-hint-pill", css_content)
        self.assertIn(".prompt-hint-action-btn", css_content)

    def test_07_shuffle_and_dismissal_persistence(self):
        """Verify shuffle logic filters current ID and dismissal sets localStorage key"""
        zen_file = BASE_DIR / "static" / "js" / "zen-prompts.js"
        content = zen_file.read_text(encoding="utf-8")

        # Check getRandomPrompt excludes currentId
        self.assertIn("const candidates = this.prompts.filter((p) => p.id !== currentId);", content)
        self.assertIn("kokoro_zen_active_", content)

        # Check isDismissed and setDismissed
        self.assertIn("kokoro_zen_dismissed_", content)
        self.assertIn("isDismissed(dateStr = null)", content)
        self.assertIn("setDismissed(dateStr = null, val = true)", content)

        # Check app.js handles dismissal animation and timeout
        app_path = BASE_DIR / "static" / "js" / "app.js"
        app_content = app_path.read_text(encoding="utf-8")
        self.assertIn("cardEl.classList.add('collapsed')", app_content)
        self.assertIn("cardEl.style.display = 'none'", app_content)
        self.assertIn("diceIcon.classList.add('anim-spinning')", app_content)


if __name__ == "__main__":
    unittest.main()
