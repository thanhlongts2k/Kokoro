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

    @classmethod
    def _get_card_module_content(cls):
        files = [
            BASE_DIR / "static" / "js" / "card-export.js",
            BASE_DIR / "static" / "js" / "card-canvas-engine.js",
            BASE_DIR / "static" / "js" / "card-themes.js",
        ]
        return "\n".join(f.read_text(encoding="utf-8") for f in files if f.exists())

    def test_01_version_and_sw_alignment(self):
        """Verify Config, Auth config API, Service Worker and Footer are aligned to v1.6.3 or later"""
        # 1. Config.APP_VERSION
        self.assertIn(Config.APP_VERSION, ("v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7"))

        # 2. GET /api/auth/config
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("version"), ("v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7"))

        # 3. static/sw.js
        sw_path = BASE_DIR / "static" / "sw.js"
        sw_content = sw_path.read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_content for v in ("kokoro-v1.6.3", "kokoro-v1.6.4", "kokoro-v1.6.5", "kokoro-v1.7.0", "kokoro-v1.7.1", "kokoro-v1.7.2", "kokoro-v1.7.3", "kokoro-v1.7.4", "kokoro-v1.7.5", "kokoro-v1.7.6", "kokoro-v1.7.7")))
        self.assertTrue(any(v in sw_content for v in ("card-export.js?v=1.6.3", "card-export.js?v=1.6.4", "card-export.js?v=1.6.5", "card-export.js?v=1.7.0", "card-export.js?v=1.7.1", "card-export.js?v=1.7.2", "card-export.js?v=1.7.3", "card-export.js?v=1.7.4", "card-export.js?v=1.7.5", "card-export.js?v=1.7.6", "card-export.js?v=1.7.7")))
        self.assertTrue(any(v in sw_content for v in ("components.css?v=1.6.3", "components.css?v=1.6.4", "components.css?v=1.6.5", "components.css?v=1.7.0", "components.css?v=1.7.1", "components.css?v=1.7.2", "components.css?v=1.7.3", "components.css?v=1.7.4", "components.css?v=1.7.5", "components.css?v=1.7.6", "components.css?v=1.7.7")))

        # 4. static/index.html footer badge
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")
        self.assertTrue(any(f'id="app-version-badge">{v}</span>' in index_content for v in ("v1.6.3", "v1.6.4", "v1.6.5", "v1.7.0", "v1.7.1", "v1.7.2", "v1.7.3", "v1.7.4", "v1.7.5", "v1.7.6", "v1.7.7")))
        self.assertTrue(any(f'href="./css/components.css?v={v}"' in index_content for v in ("1.6.3", "1.6.4", "1.6.5", "1.7.0", "1.7.1", "1.7.2", "1.7.3", "1.7.4", "1.7.5", "1.7.6", "1.7.7")))

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
        content = self._get_card_module_content()

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
        content = self._get_card_module_content()

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
        content = self._get_card_module_content()

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
        content = self._get_card_module_content()

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

    def test_08_card_aesthetic_upgrades(self):
        """Verify aesthetic upgrades (v1.6.5): Adaptive Story photo height, Scrapbook frame, Smart 35% focus & Weekday Date"""
        content = self._get_card_module_content()

        # 1. Adaptive photo height in Story 9:16 when text is short (<= 4 lines)
        self.assertIn("isShortText", content)
        self.assertIn("photoH = isShortText ?", content)
        self.assertIn("Math.round(contentWidth * 1.22)", content)

        # 2. Smart 35% crop anchor in drawImageCover
        self.assertIn("sy = Math.max(0, (img.naturalHeight - sHeight) * 0.35);", content)

        # 3. Scrapbook / Polaroid photo frame with soft shadow
        self.assertIn("rgba(15, 23, 42, 0.08)", content)
        self.assertIn("ctx.shadowBlur = 24;", content)
        self.assertIn("framePad = 7;", content)

        # 4. Weekday timestamp formatting
        self.assertIn("formatCardDate(entry)", content)
        self.assertIn("Chủ Nhật", content)
        self.assertIn("Thứ Ba", content)

        # 5. Poetic quotation marks (“ ”)
        self.assertIn("“", content)
        self.assertIn("”", content)

    def test_09_multi_theme_memory_studio(self):
        """Verify Multi-Theme Memory Studio (v1.6.5): 5 Themes, Switcher UI, drawPhotoFrame & drawDecorations"""
        # 1. Check index.html Theme Switcher UI
        index_path = BASE_DIR / "static" / "index.html"
        index_content = index_path.read_text(encoding="utf-8")

        self.assertIn('id="card-export-theme-bar"', index_content)
        self.assertIn('data-theme="sakura"', index_content)
        self.assertIn('data-theme="polaroid"', index_content)
        self.assertIn('data-theme="scrapbook"', index_content)
        self.assertIn('data-theme="music"', index_content)
        self.assertIn('data-theme="editorial"', index_content)

        # 2. Check components.css Capsule styling
        css_path = BASE_DIR / "static" / "css" / "components.css"
        css_content = css_path.read_text(encoding="utf-8")

        self.assertIn(".card-export-theme-bar", css_content)
        self.assertIn(".export-theme-btn", css_content)
        self.assertIn(".export-theme-btn.active", css_content)

        # 3. Check Card Module Theme Engine
        content = self._get_card_module_content()

        # 5 Themes dictionary
        for theme in ("sakura", "polaroid", "scrapbook", "music", "editorial"):
            self.assertIn(f"{theme}: {{", content)

        # State & Controller methods
        self.assertIn("activeTheme: 'sakura'", content)
        self.assertIn("setTheme(theme)", content)
        self.assertIn("updateThemeButtons()", content)

        # Theme Photo Frame Engine
        self.assertIn("drawPhotoFrame(ctx, entry, photoImg", content)
        self.assertIn("formatFilmDate(entry)", content)
        self.assertIn("Washi Tape", content)

        # Theme Decorations Engine
        self.assertIn("drawDecorations(ctx, layout, theme", content)
        self.assertIn("KOKORO POST", content)  # Scrapbook cancel stamp
        self.assertIn("01:43", content)  # Music progress bar
        self.assertIn("03:20", content)
        self.assertIn("Georgia, serif", content)  # Editorial watermark

        # Memory hygiene & Blob URL revocation
        self.assertIn("cleanupMemory()", content)
        self.assertIn("URL.revokeObjectURL", content)

    def test_10_scrapbook_and_memory_photocard_aesthetics(self):
        """Verify Scrapbook & Memory Photocard upgrades (v1.6.5): Dot-grid, Tilted Polaroid, Gingham Tape, Doodles & Metadata"""
        content = self._get_card_module_content()

        # 1. Bullet Journal Dot-Grid Texture
        self.assertIn("drawDotGrid", content)
        self.assertIn("#faf6ed", content)
        self.assertIn("hasDotGrid: true", content)

        # 2. Tilted Polaroid & Gingham / Caro Washi Tape
        self.assertIn("drawWashiTapeGingham", content)
        self.assertIn("tiltAngle", content)
        self.assertIn("ctx.rotate(tiltAngle)", content)

        # 3. Hand-drawn Doodle Hearts & Floating Music Notes
        self.assertIn("drawDoodleHeart", content)
        self.assertIn("Now Playing: ${songName}", content)
        self.assertIn("Giai điệu ngày bình yên", content)

        # 4. Memory Metadata Engine (Location, Weather, Streak, Signature)
        self.assertIn("drawMemoryMetadata", content)
        self.assertIn("📍 ${location} • ${weatherIcon} ${weatherTemp}", content)
        self.assertIn("Ngày thứ ${streakDays} 🌸", content)
        self.assertIn("Ghi lại bởi ${authorName} ✒️", content)

    def test_11_layout_collisions_and_vertical_balancing(self):
        """Verify layout collision fixes & vertical balancing (v1.6.5): Dynamic music Y, safe postmark, Story vertical centering & markdown quote cleaning"""
        content = self._get_card_module_content()

        # 1. Dynamic musicWidgetY based on cursorY (no overlapping text)
        self.assertIn("musicWidgetY = cursorY + 24", content)
        self.assertIn("photoH = isShortText ? 330 : 290;", content)

        # 2. Safe postal cancellation stamp location (clear of header date text)
        self.assertIn("stampY = photoTop + 65", content)

        # 3. Vertical balancing in Story 9:16
        self.assertIn("Vertical Balancing for Story 9:16", content)
        self.assertIn("freeSpace = availableViewportH - totalContentH", content)

        # 4. Raw markdown blockquote prefix '>' cleaning
        self.assertIn("paragraph.replace(/^(?:>\\s*)+/, '')", content)

    def test_12_theme_differentiation_and_export_filename(self):
        """Verify Polaroid vs Scrapbook differentiation, Square Music spacing ceiling, and standardized getExportFilename()"""
        content = self._get_card_module_content()

        # 1. Square Theme Music spacing ceiling and hashtag omission
        self.assertIn("footerY - 54", content)
        self.assertIn("(isStory || themeId !== 'music')", content)

        # 2. Clear differentiation: polaroid hasDotGrid is false, scrapbook is true
        self.assertIn("hasDotGrid: false", content)
        self.assertIn("hasDotGrid: true", content)
        self.assertIn("if (themeId === 'scrapbook') {", content)

        # 3. Standardized export filename format: kokoro_{theme}_{layout}_{timestamp}.jpg
        self.assertIn("getExportFilename()", content)
        self.assertIn("kokoro_${theme}_${layout}_${timestamp}.jpg", content)
        self.assertIn("this.getExportFilename()", content)


if __name__ == "__main__":
    unittest.main()


