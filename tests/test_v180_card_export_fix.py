"""
Test Suite: Kokoro v1.8.0 Card Export Fix Verification
Covers:
1. Fix entry Scope & ReferenceError in static/js/card-canvas-engine.js
2. drawDecorations parameter signature and 3 call sites in renderCard()
3. Safe optional chaining fallback for songName in Music theme
4. JPEG 0.92 MIME-type standardization in static/js/card-export.js
5. Mobile / iOS PWA native share integration for saving to Photos
6. Rendering anti-spam guards (this.isRendering) on download() and share()
7. Node.js runtime execution test across all 5 themes (Sakura, Polaroid, Scrapbook, Music, Editorial)
"""

import unittest
import os
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent


class TestKokoroV180CardExportFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine_path = BASE_DIR / "static" / "js" / "card-canvas-engine.js"
        cls.export_path = BASE_DIR / "static" / "js" / "card-export.js"
        cls.engine_code = cls.engine_path.read_text(encoding="utf-8")
        cls.export_code = cls.export_path.read_text(encoding="utf-8")

    def test_01_draw_decorations_signature_has_entry(self):
        """Verify drawDecorations has entry parameter right after ctx."""
        self.assertIn("drawDecorations(ctx, entry, layout, theme", self.engine_code)

    def test_02_all_call_sites_pass_entry(self):
        """Verify all 3 layout branches in renderCard pass entry to drawDecorations."""
        # 1. photo-only layout
        self.assertIn("this.drawDecorations(ctx, entry, 'photo-only', themeId", self.engine_code)
        # 2. photo-text layout
        self.assertIn("this.drawDecorations(ctx, entry, 'photo-text', themeId", self.engine_code)
        # 3. text-only layout
        self.assertIn("this.drawDecorations(ctx, entry, 'text-only', themeId", self.engine_code)

    def test_03_song_name_safe_optional_chaining(self):
        """Verify songName uses defensive optional chaining without bare entry reference."""
        self.assertIn("const songName = (entry?.songTitle || entry?.song_title || entry?.title || 'Giai điệu ngày bình yên');", self.engine_code)

    def test_04_jpeg_mime_type_standardization(self):
        """Verify card-export.js standardizes canvas.toBlob to image/jpeg at 0.92 quality."""
        self.assertIn("'image/jpeg', 0.92", self.export_code)
        self.assertIn("new File([blob], filename, { type: 'image/jpeg' })", self.export_code)

    def test_05_mobile_ios_share_photo_saving(self):
        """Verify download() detects mobile/iOS and invokes navigator.share for Photo Saving."""
        self.assertIn("isMobile", self.export_code)
        self.assertIn("navigator.canShare", self.export_code)
        self.assertIn("files: [this.currentExportFile]", self.export_code)
        self.assertIn("navigator.share(shareData)", self.export_code)

    def test_06_rendering_guards_against_click_spam(self):
        """Verify download() and share() guard against click spam during rendering."""
        self.assertIn("if (!this.currentBlobUrl || !this.activeEntry || this.isRendering) return;", self.export_code)
        self.assertIn("if (!this.activeEntry || this.isRendering) return;", self.export_code)

    def test_07_all_five_themes_runtime_execution_node(self):
        """Verify all 5 themes execute cleanly via Node.js without ReferenceError."""
        node_script = """
global.window = {};
const { KokoroCardCanvasEngine } = require('./static/js/card-canvas-engine.js');
const mockCtx = {
  save() {},
  restore() {},
  translate() {},
  rotate() {},
  beginPath() {},
  closePath() {},
  moveTo() {},
  lineTo() {},
  quadraticCurveTo() {},
  bezierCurveTo() {},
  stroke() {},
  fill() {},
  arc() {},
  roundRect() {},
  fillRect() {},
  fillText() {},
  measureText() { return { width: 50 }; }
};
const themes = ['sakura', 'polaroid', 'scrapbook', 'music', 'editorial'];
const testEntry = { title: 'Test Entry', songTitle: 'Bài Ca Hy Vọng' };
for (const theme of themes) {
  KokoroCardCanvasEngine.drawDecorations(mockCtx, testEntry, 'photo-text', theme, false, 1080, 1080, 500, [], 60, 960, 60, 960, 60, 960, 900, { x: 60, y: 100, w: 960, h: 400 });
  // Also test with empty entry
  KokoroCardCanvasEngine.drawDecorations(mockCtx, null, 'photo-text', theme, false, 1080, 1080, 500, [], 60, 960, 60, 960, 60, 960, 900, { x: 60, y: 100, w: 960, h: 400 });
}
console.log('OK_5_THEMES');
"""
        proc = subprocess.run(["node", "-e", node_script], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0, f"Node script failed: {proc.stderr}")
        self.assertIn("OK_5_THEMES", proc.stdout)


if __name__ == "__main__":
    unittest.main()
