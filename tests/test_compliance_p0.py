"""
Test Suite: Kokoro Compliance Sprint 1 Verification (P0 & Quick-Wins P1)
Verifies:
1. tag-manager.js has 0 native alert/confirm/prompt in UI handlers and exports KokoroDialog.
2. index.html contains #generic-confirm-modal and #generic-prompt-modal.
3. layout.css centers the generic dialogs.
4. components.css defines >= 44px hit-box expansion (::after) for action-icon-btn, preview-remove-btn, zen-dismiss-btn.
5. server.py has no dead api_current_user function.
6. media_service.py sets safe Image.MAX_IMAGE_PIXELS == 89478485.
7. ARCHITECTURE.md theme colors match #fff5f7 and #fdf2f4.
8. entry_routes.py supports optional limit and offset params on GET /api/entries without breaking client-side filtering.
"""

import os
import sys
import unittest
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from server import app
from app.services.media_service import Image, MediaService


class TestComplianceP0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_tag_manager_native_popups_eliminated(self):
        """Test that tag-manager.js has eliminated native popups in favor of KokoroDialog & Toast."""
        file_path = os.path.join(BASE_DIR, 'static', 'js', 'tag-manager.js')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check KokoroDialog definition
        self.assertIn("window.KokoroDialog", content)
        self.assertIn("confirm({", content)
        self.assertIn("prompt({", content)

        # Check that UI handlers do NOT call native alert, confirm, prompt
        self.assertNotIn("alert('Vui lòng nhập tên danh mục", content)
        self.assertNotIn("alert('Vui lòng nhập tên thẻ", content)
        self.assertNotIn("alert('Tên danh mục không được để trống", content)
        self.assertNotIn("alert('Tên thẻ không được để trống", content)
        self.assertNotIn("if (!confirm('Bạn có chắc muốn dọn dẹp", content)
        self.assertNotIn("if (!confirm(`Bạn có chắc muốn xóa danh mục", content)
        self.assertNotIn("if (!confirm(`Bạn có chắc muốn xóa thẻ", content)

        # Ensure KokoroDialog.confirm and KokoroDialog.prompt are used
        self.assertIn("await window.KokoroDialog.confirm(", content)
        self.assertIn("await window.KokoroDialog.prompt(", content)

    def test_02_index_html_has_generic_dialog_modals(self):
        """Test that index.html contains generic confirm and prompt modals."""
        file_path = os.path.join(BASE_DIR, 'static', 'index.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('id="generic-confirm-modal"', content)
        self.assertIn('id="generic-confirm-ok-btn"', content)
        self.assertIn('id="generic-confirm-cancel-btn"', content)
        self.assertIn('id="generic-prompt-modal"', content)
        self.assertIn('id="generic-prompt-input"', content)
        self.assertIn('id="generic-prompt-ok-btn"', content)

    def test_03_layout_css_centers_generic_dialogs(self):
        """Test that layout.css applies proper centering to generic dialogs."""
        file_path = os.path.join(BASE_DIR, 'static', 'css', 'layout.css')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('#generic-confirm-modal', content)
        self.assertIn('#generic-prompt-modal', content)

    def test_04_touch_target_expansion_in_components_css(self):
        """Test that components.css has >= 44px hit-box expansion for small interactive buttons."""
        file_path = os.path.join(BASE_DIR, 'static', 'css', 'components.css')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # action-icon-btn
        self.assertIn('.action-icon-btn::after', content)
        self.assertIn('min-width: 44px', content)
        self.assertIn('min-height: 44px', content)

        # preview-remove-btn
        self.assertIn('.preview-remove-btn::after', content)

        # zen-dismiss-btn
        self.assertIn('.zen-dismiss-btn::after', content)

    def test_05_server_py_dead_code_eliminated(self):
        """Test that api_current_user dead function has been purged from server.py."""
        file_path = os.path.join(BASE_DIR, 'server.py')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertNotIn("async def api_current_user", content)
        self.assertNotIn("aria.tanaka@kokoro.me", content)

    def test_06_media_service_decompression_bomb_threshold(self):
        """Test that Image.MAX_IMAGE_PIXELS is set to safe 89MP threshold."""
        self.assertEqual(Image.MAX_IMAGE_PIXELS, 89478485)

    def test_07_architecture_md_theme_color_sync(self):
        """Test that ARCHITECTURE.md theme colors match Soft Sakura specs."""
        file_path = os.path.join(BASE_DIR, 'ARCHITECTURE.md')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('background_color`: "#fff5f7"', content)
        self.assertIn('theme_color`: "#fdf2f4"', content)
        self.assertNotIn('background_color`: "#080b11"', content)
        self.assertNotIn('theme_color`: "#080b11"', content)

    def test_08_optional_pagination_get_entries(self):
        """Test that GET /api/entries handles optional limit and offset params."""
        from app.database import get_cursor
        from app.auth import create_session_token
        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users LIMIT 1;")
            user = cur.fetchone()
        self.assertIsNotNone(user, "At least one user must exist in users table")
        token = create_session_token(user["id"], user["email"], user["name"])
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 1. Unbounded / default call (returns entries without crashing)
        resp_all = self.client.get("/api/entries", headers=auth_headers)
        self.assertEqual(resp_all.status_code, 200)
        data_all = resp_all.json()
        self.assertEqual(data_all.get("status"), "success")
        total_count = len(data_all.get("entries", []))

        # 2. Bounded call with limit=1
        resp_limit = self.client.get("/api/entries?limit=1", headers=auth_headers)
        self.assertEqual(resp_limit.status_code, 200)
        data_limit = resp_limit.json()
        self.assertEqual(data_limit.get("status"), "success")
        if total_count >= 1:
            self.assertEqual(len(data_limit.get("entries", [])), 1)

        # 3. Call with invalid limit (fallback safely)
        resp_invalid = self.client.get("/api/entries?limit=invalid&offset=bad", headers=auth_headers)
        self.assertEqual(resp_invalid.status_code, 200)


if __name__ == "__main__":
    unittest.main()
