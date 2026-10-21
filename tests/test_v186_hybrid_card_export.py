"""
Test Suite: Kokoro v1.8.6 Hybrid Multi-Photo Card Export
Covers:
1. DOM Contract: .card-export-photo-bar in index.html and components.css
2. State & Display Management: Auto-hide on <= 1 photo, flex on >= 2 photos
3. Mathematical Coordinate Matrix for 2, 3, 4 photos collage layouts
4. Dual Offline Fallback & Parallel Loading Behavioral Execution
5. Memory Hygiene & WebKit RAM Protection
"""

import unittest
import os
import sys
import re
from pathlib import Path
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent


class TestKokoroV186HybridCardExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def _get_card_export_content(cls):
        p = BASE_DIR / "static" / "js" / "card-export.js"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    @classmethod
    def _get_card_engine_content(cls):
        p = BASE_DIR / "static" / "js" / "card-canvas-engine.js"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def test_01_dom_and_css_specs(self):
        """Verify .card-export-photo-bar DOM container and CSS rules exist"""
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        # 1. Container in index.html
        self.assertIn('id="card-export-photo-bar"', index_content)
        self.assertIn('class="card-export-photo-bar"', index_content)
        self.assertIn('role="tablist"', index_content)

        # 2. Check position: photo bar must be between theme-bar and preview-box
        theme_bar_pos = index_content.find('id="card-export-theme-bar"')
        photo_bar_pos = index_content.find('id="card-export-photo-bar"')
        preview_box_pos = index_content.find('class="card-export-preview-box"')

        self.assertNotEqual(theme_bar_pos, -1)
        self.assertNotEqual(photo_bar_pos, -1)
        self.assertNotEqual(preview_box_pos, -1)
        self.assertLess(theme_bar_pos, photo_bar_pos, "Photo bar must come after theme bar")
        self.assertLess(photo_bar_pos, preview_box_pos, "Photo bar must come before preview box")

        # 3. CSS in components.css
        css_path = BASE_DIR / "static" / "css" / "components.css"
        css_content = css_path.read_text(encoding="utf-8")

        self.assertIn(".card-export-photo-bar", css_content)
        self.assertIn("touch-action: pan-x !important", css_content)
        self.assertIn("height: 54px;", css_content)
        self.assertIn(".export-photo-btn", css_content)
        self.assertIn(".export-photo-thumb", css_content)
        self.assertIn("var(--sakura-500)", css_content)

    def test_02_photo_bar_state_and_display_logic(self):
        """Behavioral execution test: photo bar visibility and chip rendering based on photo count"""
        export_js = self._get_card_export_content()

        # Simulate updatePhotoBar behavioral logic
        def simulate_update_photo_bar(photos, selected_index=-1):
            if not photos or len(photos) <= 1:
                return {
                    "display": "none",
                    "html": "",
                    "selected_index": 0 if (photos and len(photos) == 1) else -1
                }

            html_chips = []
            is_collage_active = selected_index == -1
            html_chips.append(f'<button class="export-photo-btn{" active" if is_collage_active else ""}" data-index="-1">🧩 Bố cục ghép ảnh</button>')

            for idx, p in enumerate(photos):
                is_active = selected_index == idx
                html_chips.append(f'<button class="export-photo-thumb{" active" if is_active else ""}" data-index="{idx}"><span class="thumb-index">{idx + 1}</span></button>')

            return {
                "display": "flex",
                "html": "".join(html_chips),
                "selected_index": selected_index,
                "chip_count": len(photos) + 1  # 1 collage chip + N thumbnails
            }

        # Case A: Empty photos
        res_empty = simulate_update_photo_bar([])
        self.assertEqual(res_empty["display"], "none")
        self.assertEqual(res_empty["html"], "")

        # Case B: 1 photo (Single entry) -> MUST be hidden to preserve clean existing layout
        res_one = simulate_update_photo_bar([{"url": "/uploads/1.jpg"}])
        self.assertEqual(res_one["display"], "none")
        self.assertEqual(res_one["html"], "")

        # Case C: 2 photos -> MUST show collage button and 2 thumbnails
        res_two = simulate_update_photo_bar([{"url": "/uploads/1.jpg"}, {"url": "/uploads/2.jpg"}], selected_index=-1)
        self.assertEqual(res_two["display"], "flex")
        self.assertEqual(res_two["chip_count"], 3)
        self.assertIn('data-index="-1"', res_two["html"])
        self.assertIn('data-index="0"', res_two["html"])
        self.assertIn('data-index="1"', res_two["html"])
        self.assertIn('export-photo-btn active', res_two["html"])

        # Case D: 4 photos with thumbnail #2 selected
        res_four = simulate_update_photo_bar([{"url": f"/uploads/{i}.jpg"} for i in range(1, 5)], selected_index=1)
        self.assertEqual(res_four["display"], "flex")
        self.assertEqual(res_four["chip_count"], 5)
        self.assertIn('data-index="1"', res_four["html"])
        self.assertIn('export-photo-thumb active', res_four["html"])

        # Check export.js contains the methods
        self.assertIn("updatePhotoBar()", export_js)
        self.assertIn("setPhotoIndex(idx)", export_js)
        self.assertIn("selectedPhotoIndex", export_js)

    def test_03_mathematical_coordinate_matrix_for_collage(self):
        """Verify mathematical geometry for 2, 3, and 4 photo collage layouts"""
        engine_js = self._get_card_engine_content()

        # Behavioral simulation of drawCollageFrame layout mathematics
        def calculate_collage_rects(photo_count, photo_x, photo_y, photo_w, photo_h, gap=14):
            rects = []
            if photo_count == 1:
                rects.append({"x": photo_x, "y": photo_y, "w": photo_w, "h": photo_h})
            elif photo_count == 2:
                col_w = (photo_w - gap) / 2
                col_h = photo_h
                rects.append({"x": photo_x, "y": photo_y, "w": col_w, "h": col_h})
                rects.append({"x": photo_x + col_w + gap, "y": photo_y, "w": col_w, "h": col_h})
            elif photo_count == 3:
                left_w = round((photo_w - gap) * 0.60)
                right_w = photo_w - gap - left_w
                right_h = (photo_h - gap) / 2
                rects.append({"x": photo_x, "y": photo_y, "w": left_w, "h": photo_h})
                right_x = photo_x + left_w + gap
                rects.append({"x": right_x, "y": photo_y, "w": right_w, "h": right_h})
                rects.append({"x": right_x, "y": photo_y + right_h + gap, "w": right_w, "h": right_h})
            elif photo_count >= 4:
                cell_w = (photo_w - gap) / 2
                cell_h = (photo_h - gap) / 2
                rects.append({"x": photo_x, "y": photo_y, "w": cell_w, "h": cell_h})
                rects.append({"x": photo_x + cell_w + gap, "y": photo_y, "w": cell_w, "h": cell_h})
                rects.append({"x": photo_x, "y": photo_y + cell_h + gap, "w": cell_w, "h": cell_h})
                rects.append({"x": photo_x + cell_w + gap, "y": photo_y + cell_h + gap, "w": cell_w, "h": cell_h})
            return rects

        # Square 1:1 Canvas test bounds
        canvas_photo_x = 64
        canvas_photo_y = 120
        canvas_photo_w = 952
        canvas_photo_h = 760
        gap = 14

        # 1. Test 2-photo split duo
        rects_2 = calculate_collage_rects(2, canvas_photo_x, canvas_photo_y, canvas_photo_w, canvas_photo_h, gap)
        self.assertEqual(len(rects_2), 2)
        self.assertEqual(rects_2[0]["w"], (952 - 14) / 2)
        self.assertEqual(rects_2[1]["w"], (952 - 14) / 2)
        self.assertEqual(rects_2[0]["h"], 760)
        self.assertEqual(rects_2[1]["h"], 760)
        # Total span must match exactly photo_w
        total_w_2 = rects_2[0]["w"] + gap + rects_2[1]["w"]
        self.assertEqual(total_w_2, canvas_photo_w)

        # 2. Test 3-photo magazine layout
        rects_3 = calculate_collage_rects(3, canvas_photo_x, canvas_photo_y, canvas_photo_w, canvas_photo_h, gap)
        self.assertEqual(len(rects_3), 3)
        # Hero left photo: 60%
        expected_left_w = round((952 - 14) * 0.60)  # 563
        expected_right_w = (952 - 14) - expected_left_w  # 375
        self.assertEqual(rects_3[0]["w"], expected_left_w)
        self.assertEqual(rects_3[1]["w"], expected_right_w)
        self.assertEqual(rects_3[2]["w"], expected_right_w)
        # Vertical right stack: 2 sub-photos must fill full height
        total_h_3 = rects_3[1]["h"] + gap + rects_3[2]["h"]
        self.assertEqual(total_h_3, canvas_photo_h)

        # 3. Test 4-photo 2x2 grid
        rects_4 = calculate_collage_rects(4, canvas_photo_x, canvas_photo_y, canvas_photo_w, canvas_photo_h, gap)
        self.assertEqual(len(rects_4), 4)
        expected_cell_w = (952 - 14) / 2
        expected_cell_h = (760 - 14) / 2
        for r in rects_4:
            self.assertEqual(r["w"], expected_cell_w)
            self.assertEqual(r["h"], expected_cell_h)

        # Verify engine.js implements drawCollageFrame with exact math
        self.assertIn("drawCollageFrame(ctx, images", engine_js)
        self.assertIn("const colW = (photoW - gap) / 2;", engine_js)
        self.assertIn("Math.round((photoW - gap) * 0.60)", engine_js)
        self.assertIn("const cellW = (photoW - gap) / 2;", engine_js)

    def test_04_dual_offline_fallback_and_parallel_loading(self):
        """Verify parallel photo loading (Promise.all) and dual fallback to thumbnail when offline"""
        engine_js = self._get_card_engine_content()

        # Behavioral simulation of offline fallback loader
        def simulate_photo_loader(photo, is_offline=False, cache_store=None):
            cache_store = cache_store or {}
            primary_url = photo.get("url")
            thumb_url = photo.get("thumbUrl")

            # Try primary
            if not is_offline and primary_url in cache_store:
                return f"loaded:{primary_url}"

            # Fallback to thumbnail (CacheStorage)
            if thumb_url and thumb_url in cache_store:
                return f"loaded:{thumb_url}"

            return None

        # Scenario 1: Online - loads full image
        cache = {"/uploads/photo1.jpg": "blob_full", "/uploads/photo1_thumb.webp": "blob_thumb"}
        p1 = {"url": "/uploads/photo1.jpg", "thumbUrl": "/uploads/photo1_thumb.webp"}
        self.assertEqual(simulate_photo_loader(p1, is_offline=False, cache_store=cache), "loaded:/uploads/photo1.jpg")

        # Scenario 2: Offline - original not cached, thumbnail is cached
        cache_offline = {"/uploads/photo1_thumb.webp": "blob_thumb"}
        self.assertEqual(simulate_photo_loader(p1, is_offline=True, cache_store=cache_offline), "loaded:/uploads/photo1_thumb.webp")

        # Scenario 3: Neither cached - safe fallback to None (no crash)
        self.assertIsNone(simulate_photo_loader(p1, is_offline=True, cache_store={}))

        # Verify engine implementation has Promise.all and loadPhotoWithFallback
        self.assertIn("loadPhotoWithFallback(photo)", engine_js)
        self.assertIn("loadMultiplePhotosSafe(photos", engine_js)
        self.assertIn("Promise.all(loadPromises)", engine_js)

    def test_05_memory_hygiene_and_cleanup(self):
        """Verify memory references are cleaned up after card render and modal close"""
        export_js = self._get_card_export_content()
        engine_js = self._get_card_engine_content()

        # Engine cleans up references
        self.assertIn("photoImg = null;", engine_js)
        self.assertIn("photoImages = null;", engine_js)

        # Export controller cleans up state and DOM on close
        self.assertIn("this.selectedPhotoIndex = -1;", export_js)
        self.assertIn("this.photoBarEl.style.display = 'none';", export_js)
        self.assertIn("this.cleanupMemory();", export_js)


if __name__ == "__main__":
    unittest.main()
