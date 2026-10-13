"""
Test Suite: Kokoro v1.6.3 Daily Card Export (Xuất Thẻ Ảnh Kỷ Niệm Canvas)
Covers:
1. Version & PWA Service Worker Cache Alignment (v1.6.3)
2. Script Loading Order Guard in index.html (card-export.js BEFORE app.js)
3. Fixed 1080p Canvas Buffer Contract (1080x1080 & 1080x1920, Zero DPR Multiplier to prevent iOS Safari crash)
4. Smart Vietnamese Word-Wrap & Paragraph Line-Break Preservation Algorithm
5. Adaptive Layout Modes (Photo Memory Frame + Multiple Photos Badge vs Text-Only Zen Quote)
6. Pre-generated Blob/File for Instant iOS Safari Web Share & Memory Hygiene (revokeObjectURL)
7. DOM Structure & CSS Components Contract
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


class TestKokoroV163CardExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_version_and_sw_alignment(self):
        """Verify Config, Auth config API, Service Worker and Footer are aligned to v1.6.3"""
        # 1. Config.APP_VERSION
        self.assertEqual(Config.APP_VERSION, "v1.6.3")

        # 2. GET /api/auth/config
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("version"), "v1.6.3")

        # 3. static/sw.js
        sw_path = BASE_DIR / "static" / "sw.js"
        sw_content = sw_path.read_text(encoding="utf-8")
        self.assertIn("kokoro-v1.6.3", sw_content)
        self.assertIn("./js/card-export.js?v=1.6.3", sw_content)
        self.assertIn("./css/components.css?v=1.6.3", sw_content)

        # 4. static/index.html footer badge
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")
        self.assertIn('id="app-version-badge">v1.6.3</span>', index_content)
        self.assertIn('href="./css/components.css?v=1.6.3"', index_content)

    def test_02_script_loading_order_guard(self):
        """Ensure card-export.js is loaded BEFORE app.js to prevent ReferenceError"""
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        card_idx = index_content.find("js/card-export.js")
        app_idx = index_content.find("js/app.js")

        self.assertNotEqual(card_idx, -1, "card-export.js script tag not found in index.html")
        self.assertNotEqual(app_idx, -1, "app.js script tag not found in index.html")
        self.assertLess(card_idx, app_idx, "card-export.js MUST be loaded BEFORE app.js")

    def test_03_fixed_1080p_canvas_buffer_contract(self):
        """Verify Canvas physical buffer is locked to 1080p (1080x1080 & 1080x1920) WITHOUT devicePixelRatio multiplication"""
        card_file = BASE_DIR / "static" / "js" / "card-export.js"
        content = card_file.read_text(encoding="utf-8")

        # 1. Target width must be 1080
        self.assertIn("targetWidth = 1080;", content)
        self.assertIn("targetHeight = isStory ? 1920 : 1080;", content)

        # 2. Canvas dimensions set directly to targetWidth & targetHeight (NO dpr multiplier)
        self.assertIn("canvas.width = targetWidth;", content)
        self.assertIn("canvas.height = targetHeight;", content)
        self.assertNotIn("canvas.width = targetWidth *", content)
        self.assertNotIn("canvas.height = targetHeight *", content)

    def test_04_smart_vietnamese_word_wrap_and_paragraphs(self):
        """Verify paragraph splitting, word wrapping and safe truncation with '...'"""
        card_file = BASE_DIR / "static" / "js" / "card-export.js"
        content = card_file.read_text(encoding="utf-8")

        # Check paragraph splitting by \r?\n in wrapAndFitText
        self.assertIn("text.split(/\\r?\\n/)", content)

        # Simulate Python logic matching wrapAndFitText
        def wrap_and_fit_text(text: str, max_chars_per_line: int, max_lines: int):
            paragraphs = re.split(r'\r?\n', text)
            lines = []
            reached_limit = False

            for p in paragraphs:
                p_trimmed = p.strip()
                if not p_trimmed:
                    if len(lines) < max_lines:
                        lines.append("")
                    else:
                        reached_limit = True
                        break
                    continue

                words = p_trimmed.split()
                current_line = ""

                for word in words:
                    test_line = f"{current_line} {word}" if current_line else word
                    if len(test_line) <= max_chars_per_line:
                        current_line = test_line
                    else:
                        if len(lines) + 1 >= max_lines:
                            reached_limit = True
                            # Truncate
                            truncated = current_line
                            while truncated and len(truncated + "...") > max_chars_per_line:
                                last_space = truncated.rfind(" ")
                                if last_space == -1:
                                    truncated = truncated[:-1]
                                else:
                                    truncated = truncated[:last_space]
                            lines.append(f"{truncated}..." if truncated else "...")
                            break
                        else:
                            lines.append(current_line)
                            current_line = word

                if reached_limit:
                    break

                if current_line:
                    if len(lines) + 1 > max_lines:
                        lines.append(f"{current_line[:max_chars_per_line-3]}...")
                        break
                    else:
                        lines.append(current_line)

            return lines

        # Case 1: Multiple paragraphs with empty line (Poem / Journal Rhythm)
        input_text = "Buổi sáng ngắm hoa anh đào nở.\n\nTách trà ấm sưởi ấm tâm hồn.\nBình yên giữa lòng thành phố."
        result_lines = wrap_and_fit_text(input_text, 35, 10)
        self.assertEqual(len(result_lines), 4)
        self.assertEqual(result_lines[0], "Buổi sáng ngắm hoa anh đào nở.")
        self.assertEqual(result_lines[1], "")  # Empty paragraph preserved
        self.assertEqual(result_lines[2], "Tách trà ấm sưởi ấm tâm hồn.")
        self.assertEqual(result_lines[3], "Bình yên giữa lòng thành phố.")

        # Case 2: Very long text truncation (Safe limits)
        long_text = "Hôm nay là một ngày thật đặc biệt. " * 30
        truncated_lines = wrap_and_fit_text(long_text, 40, 5)
        self.assertEqual(len(truncated_lines), 5)
        self.assertTrue(truncated_lines[-1].endswith("..."))

        # Case 3: Mini Inline Formatter tokens (**bold** & ==highlight==)
        self.assertIn("tokenizeParagraph(paragraph)", content)
        self.assertIn("rgba(253, 224, 71", content)  # Pastel yellow highlighter stroke
        self.assertIn("drawFormattedLines", content)

    def test_05_adaptive_layout_and_photo_frame_contract(self):
        """Verify adaptive layout 'CÓ GÌ HIỂN THỊ NẤY': Photo-Only, Photo+Text, and Text-Only modes"""
        card_file = BASE_DIR / "static" / "js" / "card-export.js"
        content = card_file.read_text(encoding="utf-8")

        # 1. Photo-Only Mode Contract (Khi người dùng chỉ đăng ảnh, không có text)
        self.assertIn("LAYOUT 1: PHOTO-ONLY MODE", content)
        self.assertIn("hasPhoto && !hasText", content)
        self.assertIn("this.drawImageCover(ctx, photoImg, photoX, photoY, photoW, photoH, 32);", content)

        # 2. Photo + Text Mode Contract (Bố cục tạp chí ảnh: ảnh trên, chữ dưới)
        self.assertIn("LAYOUT 2: PHOTO + TEXT MODE", content)
        self.assertIn("hasPhoto && hasText", content)
        self.assertIn("drawImageCover(ctx, photoImg", content)
        self.assertIn("+${entry.photos.length - 1} ảnh", content)

        # 3. Text-Only Zen Quote Contract (Trang tản văn thanh thoát, chữ lớn, emblem hoa anh đào)
        self.assertIn("LAYOUT 3: TEXT-ONLY ZEN QUOTE MODE", content)
        self.assertIn("🌸 Kokoro (心) Journal", content)

    def test_06_pregenerated_blob_and_memory_hygiene(self):
        """Verify pre-generated Blob/File for instant Web Share (User Gesture) & memory cleanup"""
        card_file = BASE_DIR / "static" / "js" / "card-export.js"
        content = card_file.read_text(encoding="utf-8")

        # 1. Pre-generate Blob & File right after render
        self.assertIn("canvas.toBlob", content)
        self.assertIn("this.currentBlobUrl = URL.createObjectURL(blob);", content)
        self.assertIn("new File([blob], filename, { type: 'image/png' })", content)

        # 2. Synchronous/Immediate share within User Gesture
        self.assertIn("navigator.share(shareData)", content)
        self.assertIn("this.download();", content)

        # 3. Memory Hygiene: cleanup revokeObjectURL and canvas reset
        self.assertIn("URL.revokeObjectURL(this.currentBlobUrl)", content)
        self.assertIn("this.canvasEl.width = 0;", content)
        self.assertIn("this.canvasEl.height = 0;", content)

    def test_07_dom_markup_and_css_specs(self):
        """Verify modal markup, buttons, and responsive styles exist in index.html, components.css, and app.js"""
        # 1. index.html DOM structure
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        self.assertIn('id="card-export-modal"', index_content)
        self.assertIn('id="card-export-dialog"', index_content)
        self.assertIn('id="card-export-ratio-square"', index_content)
        self.assertIn('id="card-export-ratio-story"', index_content)
        self.assertIn('id="card-export-canvas"', index_content)
        self.assertIn('id="card-export-download-btn"', index_content)
        self.assertIn('id="card-export-share-btn"', index_content)
        self.assertIn('id="card-export-close-btn"', index_content)

        # 2. components.css Styles
        css_path = BASE_DIR / "static" / "css" / "components.css"
        css_content = css_path.read_text(encoding="utf-8")

        self.assertIn("#card-export-modal.active", css_content)
        self.assertIn(".card-export-dialog", css_content)
        self.assertIn(".card-export-preview-canvas", css_content)
        self.assertIn(".export-ratio-btn", css_content)
        self.assertIn(".card-export-act-btn", css_content)

        # 3. app.js timeline button & action binding
        app_path = BASE_DIR / "static" / "js" / "app.js"
        app_content = app_path.read_text(encoding="utf-8")

        self.assertIn('data-action="export-card"', app_content)
        self.assertIn("window.KokoroCardExport.open(entry)", app_content)
        self.assertIn("window.KokoroCardExport.init()", app_content)


if __name__ == "__main__":
    unittest.main()
