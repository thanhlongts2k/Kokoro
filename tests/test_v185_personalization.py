"""
Test Suite: Milestone v1.8.5 Personalization Hub Verification
Tests:
1. Pillow Avatar Processing: Center crop 1:1, resize to 256x256, compress to WebP (85% quality).
2. MediaService Avatar Deletion: Safely removes old avatar file upon replacement.
3. User Profile REST API (PUT /api/users/profile):
   - Valid update with multipart/form-data (name, bio <= 250 chars, use_custom_profile, avatar_file).
   - Toggle use_custom_profile=False to sync with Google GIS avatar.
   - Payload verification of GET /api/auth/me including bio, custom_avatar_url, use_custom_profile, effectiveAvatarUrl.
4. Edge & Failure States:
   - Unauthorized access without session (401 Unauthorized with clean error payload).
   - Avatar file exceeding 5MB limit (400 Bad Request).
   - Non-image payload uploaded (400 Bad Request).
   - Bio exceeding 250 characters (400 Bad Request).
   - Empty name submission (400 Bad Request).
5. Mandatory Behavioral Fallback Testing (Anti-cheating / No static string matching):
   - Missing/Empty DB states and null custom_avatar fallback to Google avatar or sakura default.
   - Accessible UI Fallback containers verification for error & empty states.
6. Architectural Line Bounds:
   - app/routes/entry_routes.py strictly < 300 lines.
   - static/js/app.js strictly < 400 lines.
"""

import os
import sys
import io
import time
import unittest
from pathlib import Path
from PIL import Image
from starlette import status
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server import app
from app.config import Config
from app.database import init_db, get_cursor, seed_mock_users_for_testing
from app.auth import create_session_token
from app.services.media_service import MediaService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserDTO


class TestPersonalizationHubV185(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_mock_users_for_testing()
        cls.client = TestClient(app, base_url="https://testserver")

        with get_cursor() as cur:
            cur.execute("SELECT id, email, name, google_id, avatar_url FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            cls.user = cur.fetchone()

        cls.user_id = cls.user["id"]
        cls.token = create_session_token(cls.user_id, cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    def _generate_synthetic_image(self, width: int = 400, height: int = 300, color: str = "pink", fmt: str = "PNG") -> bytes:
        """Generate in-memory test image bytes."""
        img = Image.new("RGB", (width, height), color=color)
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()

    # =========================================================================
    # 1. PILLOW WEBP 256x256 AVATAR PROCESSING & CLEANUP
    # =========================================================================
    def test_01_avatar_center_crop_and_webp_resize(self):
        """Verify MediaService center-crops non-square images to 1:1 and resizes to 256x256 WebP."""
        # Create non-square 800x400 image
        raw_bytes = self._generate_synthetic_image(width=800, height=400, color="lavender", fmt="JPEG")
        rel_url = MediaService.process_and_save_avatar(raw_bytes, self.user_id)

        self.assertTrue(rel_url.startswith("/uploads/avatars/avatar_"))
        self.assertTrue(rel_url.endswith(".webp"))

        disk_path = Config.BASE_DIR / rel_url.lstrip("/")
        self.assertTrue(disk_path.exists(), f"Processed avatar file must exist at {disk_path}")
        self.assertGreater(disk_path.stat().st_size, 0)

        # Inspect resulting image format and dimensions
        with Image.open(disk_path) as processed_img:
            self.assertEqual(processed_img.format, "WEBP")
            self.assertEqual(processed_img.size, (256, 256), "Avatar must be strictly 256x256 square")

        # Test safe deletion
        MediaService.delete_avatar_file(rel_url)
        self.assertFalse(disk_path.exists(), "Old avatar file should be removed from disk")

    # =========================================================================
    # 2. REST API: PUT /api/users/profile & GET /api/auth/me
    # =========================================================================
    def test_02_update_profile_valid_multipart(self):
        """Verify PUT /api/users/profile accepts multipart/form-data and updates user profile."""
        img_bytes = self._generate_synthetic_image(width=300, height=300, color="peachpuff", fmt="PNG")

        form_data = {
            "name": "Aria Tanaka 🌸",
            "bio": "Hạnh phúc là từng khoảnh khắc tĩnh lặng giữa cuộc sống bộn bề.",
            "use_custom_profile": "true"
        }
        files = {
            "avatar_file": ("my_avatar.png", io.BytesIO(img_bytes), "image/png")
        }

        resp = self.client.put("/api/users/profile", data=form_data, files=files, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.text)

        body = resp.json()
        self.assertEqual(body["status"], "success")
        user = body["user"]
        self.assertEqual(user["name"], "Aria Tanaka 🌸")
        self.assertEqual(user["bio"], "Hạnh phúc là từng khoảnh khắc tĩnh lặng giữa cuộc sống bộn bề.")
        self.assertTrue(user["use_custom_profile"])
        self.assertTrue(user["custom_avatar_url"].startswith("/uploads/avatars/"))
        self.assertEqual(user["effectiveAvatarUrl"], user["custom_avatar_url"])

        # Verify GET /api/auth/me exposes new profile fields
        me_resp = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
        me_data = me_resp.json()
        self.assertTrue(me_data["authenticated"])
        me_user = me_data["user"]
        self.assertEqual(me_user["bio"], user["bio"])
        self.assertEqual(me_user["custom_avatar_url"], user["custom_avatar_url"])
        self.assertTrue(me_user["use_custom_profile"])

    def test_03_google_sync_toggle_switcher(self):
        """Verify toggling use_custom_profile=false restores Google GIS avatar as effective avatar."""
        form_data = {
            "name": "Aria Tanaka",
            "bio": "Đang đồng bộ Google",
            "use_custom_profile": "false"
        }
        resp = self.client.put("/api/users/profile", data=form_data, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        user = resp.json()["user"]
        self.assertFalse(user["use_custom_profile"])
        # When use_custom_profile is False, effectiveAvatarUrl must be the original Google avatar
        self.assertEqual(user["effectiveAvatarUrl"], user["avatar_url"])

    # =========================================================================
    # 3. EDGE CASES & ERROR STATES (STRICT HTTP CONTRACTS)
    # =========================================================================
    def test_04_unauthorized_profile_update(self):
        """Verify unauthenticated requests return 401 Unauthorized with error message."""
        resp = self.client.put("/api/users/profile", data={"name": "Hacker", "bio": "Fail"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.json()["authenticated"], False)

    def test_05_avatar_exceeding_size_limit(self):
        """Verify uploaded avatar > 5MB is rejected with 400 Bad Request."""
        large_bytes = b"0" * (5 * 1024 * 1024 + 1024)  # 5MB + 1KB
        files = {
            "avatar_file": ("giant.png", io.BytesIO(large_bytes), "image/png")
        }
        resp = self.client.put("/api/users/profile", data={"name": "Aria"}, files=files, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("5MB", resp.json()["message"])

    def test_06_invalid_file_format(self):
        """Verify non-image file uploads are rejected with 400 Bad Request."""
        text_bytes = b"This is a text script, not an image!"
        files = {
            "avatar_file": ("script.txt", io.BytesIO(text_bytes), "text/plain")
        }
        resp = self.client.put("/api/users/profile", data={"name": "Aria"}, files=files, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("hình ảnh hợp lệ", resp.json()["message"])

    def test_07_bio_exceeding_250_characters(self):
        """Verify bio longer than 250 characters is rejected with 400 Bad Request."""
        long_bio = "A" * 251
        resp = self.client.put("/api/users/profile", data={"bio": long_bio}, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("250", resp.json()["message"])

    def test_08_empty_display_name_validation(self):
        """Verify empty or whitespace-only name is rejected with 400 Bad Request."""
        resp = self.client.put("/api/users/profile", data={"name": "   "}, headers=self.headers)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("trống", resp.json()["message"])

    # =========================================================================
    # 4. MANDATORY FALLBACK & BEHAVIORAL EXECUTION VERIFICATION
    # =========================================================================
    def test_09_user_dto_fallback_behavior(self):
        """Verify UserDTO behavior on null/missing avatar fields."""
        # 1. User with no custom avatar and use_custom_profile=True falls back to google avatar
        dto1 = UserDTO(id=999, email="test@kokoro.me", name="Test", avatar_url="https://google.com/avatar.png", use_custom_profile=True)
        dict1 = dto1.to_dict()
        self.assertEqual(dict1["effectiveAvatarUrl"], "https://google.com/avatar.png")

        # 2. User with no avatar at all has None effective avatar (UI falls back to sakura default)
        dto2 = UserDTO(id=998, email="test2@kokoro.me", name="Test2", avatar_url=None, custom_avatar_url=None)
        dict2 = dto2.to_dict()
        self.assertIsNone(dict2["effectiveAvatarUrl"])

    def test_10_client_fallback_and_error_handling_in_node(self):
        """Verify Client ProfileStats handles errors, missing user, and renders fallback without crashing."""
        import subprocess
        # Node script to simulate client-side ProfileStats rendering and error handling
        node_script = """
        const fs = require('fs');
        const path = require('path');

        // Mock browser DOM
        global.document = {
          elements: {},
          getElementById(id) {
            if (!this.elements[id]) {
              this.elements[id] = {
                id,
                style: {},
                classList: {
                  add: function(c) { this[c] = true; },
                  remove: function(c) { delete this[c]; }
                },
                textContent: '',
                value: '',
                src: '',
                addEventListener: function(evt, fn) { this['on' + evt] = fn; }
              };
            }
            return this.elements[id];
          },
          querySelectorAll() { return []; },
          documentElement: { getAttribute: () => 'light' }
        };
        global.window = {
          KokoroAPI: { resolveMediaUrl: (url) => url },
          lockBodyScroll: () => {}
        };

        const code = fs.readFileSync(path.join(process.cwd(), 'static', 'js', 'profile-stats.js'), 'utf8');
        eval(code);
        const ProfileStats = global.window.ProfileStats;

        // 1. Test fallback when user is null (Guest mode fallback)
        ProfileStats.renderProfileView({ user: null, entries: [], stats: {} });
        const nameEl = global.document.getElementById('profile-view-name');
        const avatarEl = global.document.getElementById('profile-view-avatar');
        const bioEl = global.document.getElementById('profile-view-bio');

        if (nameEl.textContent !== 'Khách vãng lai') {
          console.error('Expected fallback name "Khách vãng lai", got: ' + nameEl.textContent);
          process.exit(1);
        }
        if (avatarEl.src !== './icons/sakura.svg') {
          console.error('Expected fallback avatar "./icons/sakura.svg", got: ' + avatarEl.src);
          process.exit(1);
        }
        if (bioEl.style.display !== 'none') {
          console.error('Bio element should be hidden for null user');
          process.exit(1);
        }

        // 2. Test edit profile open when user is guest (must safely abort with warning)
        global.window.KokoroToast = { show: (msg, type) => { global.lastToast = { msg, type }; } };
        ProfileStats.openEditProfileModal(null);
        if (!global.lastToast || global.lastToast.type !== 'warning') {
          console.error('Expected warning toast for unauthenticated edit attempt');
          process.exit(1);
        }

        // 3. Test modal opening for authenticated user with bio
        const authUser = {
          id: 1,
          name: 'Aria',
          email: 'aria@kokoro.me',
          bio: 'Zen living',
          use_custom_profile: true,
          custom_avatar_url: '/uploads/avatars/avatar_1.webp'
        };
        ProfileStats.openEditProfileModal({ currentUser: authUser });
        const modal = global.document.getElementById('edit-profile-modal');
        if (modal.style.display !== 'flex') {
          console.error('Modal should display flex when opened');
          process.exit(1);
        }
        const nameInput = global.document.getElementById('edit-profile-name-input');
        if (nameInput.value !== 'Aria') {
          console.error('Name input should be populated with Aria');
          process.exit(1);
        }
        const bioInput = global.document.getElementById('edit-profile-bio-input');
        if (bioInput.value !== 'Zen living') {
          console.error('Bio input should be populated with "Zen living"');
          process.exit(1);
        }

        console.log('NODE_CLIENT_TESTS_PASS');
        """
        proc = subprocess.run(["node", "-e", node_script], cwd=str(BASE_DIR), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node client test failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
        self.assertIn("NODE_CLIENT_TESTS_PASS", proc.stdout)

    # =========================================================================
    # 5. ARCHITECTURAL LINE BOUNDS
    # =========================================================================
    def test_11_hard_file_line_bounds(self):
        """Verify entry_routes.py < 300 lines and app.js < 400 lines (AGENTS.md strict bounds)."""
        entry_routes_path = BASE_DIR / "app" / "routes" / "entry_routes.py"
        app_js_path = BASE_DIR / "static" / "js" / "app.js"

        entry_routes_lines = len(entry_routes_path.read_text(encoding="utf-8").splitlines())
        app_js_lines = len(app_js_path.read_text(encoding="utf-8").splitlines())

        self.assertLess(entry_routes_lines, 300, f"entry_routes.py exceeded limit: {entry_routes_lines} >= 300")
        self.assertLess(app_js_lines, 400, f"app.js exceeded limit: {app_js_lines} >= 400")


if __name__ == "__main__":
    unittest.main()
