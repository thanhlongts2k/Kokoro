"""
Unit & Integration Tests for Kokoro Sprint Quick Critical Fixes (DEBT-01, DEBT-03, DEBT-04, DEBT-05)
Covers:
1. Domain Exceptions hierarchy, status codes, and invariant checks (app.exceptions)
2. Repository domain exception raising (InvalidInputError, CategoryDuplicateError)
3. HTTP Status code standardization across controllers (starlette.status)
4. Offline queue 401/403 data-loss prevention contract in static/js/api.js (DEBT-01)
5. Modal Accessibility attributes (role=dialog, aria-modal=true) in static/index.html (DEBT-05)
6. Global Escape key handling for dialogs in static/js/tag-manager.js & static/js/card-export.js (DEBT-05)
"""

import sys
import os
import unittest
from starlette.testclient import TestClient
from starlette import status

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.database import init_db, get_cursor, seed_mock_users_for_testing, clean_mock_users_after_testing
from app.auth import create_session_token
from app.exceptions import (
    KokoroDomainError,
    EntryNotFoundError,
    CategoryNotFoundError,
    CategoryDuplicateError,
    TagNotFoundError,
    InvalidInputError,
    UnauthorizedError,
)
from app.repositories.entry_repository import EntryRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.entry import EntryCreateDTO
from app.schemas.category import CategoryCreateDTO


class TestSprint3QuickFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            init_db()
            seed_mock_users_for_testing()
        except Exception as e:
            raise unittest.SkipTest(f"Database not accessible in this environment: {e}")
        cls.client = TestClient(app, base_url="https://testserver")

        with get_cursor() as cur:
            cur.execute("SELECT id, email, name FROM users WHERE email = 'aria.tanaka@kokoro.me';")
            cls.user = cur.fetchone()

        cls.user_id = cls.user["id"]
        cls.token = create_session_token(cls.user_id, cls.user["email"], cls.user["name"])
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        clean_mock_users_after_testing()

    def test_01_domain_exceptions_hierarchy_and_status_codes(self):
        """Verify custom domain exceptions have appropriate status codes and inherit KokoroDomainError"""
        # Base
        base_err = KokoroDomainError("Base error", status_code=500)
        self.assertIsInstance(base_err, Exception)
        self.assertEqual(base_err.status_code, 500)
        self.assertEqual(str(base_err), "Base error")

        # EntryNotFoundError -> 404
        entry_err = EntryNotFoundError(999999)
        self.assertIsInstance(entry_err, KokoroDomainError)
        self.assertEqual(entry_err.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("999999", entry_err.message)

        # CategoryNotFoundError -> 404
        cat_not_found = CategoryNotFoundError(888)
        self.assertIsInstance(cat_not_found, KokoroDomainError)
        self.assertEqual(cat_not_found.status_code, status.HTTP_404_NOT_FOUND)

        # CategoryDuplicateError -> 409
        cat_dup = CategoryDuplicateError("Kỷ niệm")
        self.assertIsInstance(cat_dup, KokoroDomainError)
        self.assertEqual(cat_dup.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Kỷ niệm", cat_dup.message)

        # TagNotFoundError -> 404
        tag_err = TagNotFoundError("#unknown")
        self.assertIsInstance(tag_err, KokoroDomainError)
        self.assertEqual(tag_err.status_code, status.HTTP_404_NOT_FOUND)

        # InvalidInputError -> 400
        inv_err = InvalidInputError("Dữ liệu không hợp lệ")
        self.assertIsInstance(inv_err, KokoroDomainError)
        self.assertEqual(inv_err.status_code, status.HTTP_400_BAD_REQUEST)

        # UnauthorizedError -> 401
        unauth_err = UnauthorizedError("Phiên đăng nhập hết hạn")
        self.assertIsInstance(unauth_err, KokoroDomainError)
        self.assertEqual(unauth_err.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_entry_repository_raises_invalid_input_error(self):
        """Verify EntryRepository raises InvalidInputError when content is empty"""
        empty_dto = EntryCreateDTO(
            title="",
            content="   ",  # whitespace only
            mood="happy",
        )
        with self.assertRaises(InvalidInputError):
            EntryRepository.create_entry(self.user_id, empty_dto)

    def test_03_category_repository_raises_category_duplicate_error(self):
        """Verify CategoryRepository raises CategoryDuplicateError for duplicate category name"""
        unique_name = "Sprint3 Test Unique Category 🌸"
        # Create first time
        first_dto = CategoryCreateDTO(name=unique_name, icon="🌸", color="#ec4899")
        created = CategoryRepository.create_category(self.user_id, first_dto)
        self.assertIsNotNone(created)

        try:
            # Second time must raise CategoryDuplicateError
            with self.assertRaises(CategoryDuplicateError):
                CategoryRepository.create_category(self.user_id, first_dto)
        finally:
            # Cleanup
            CategoryRepository.delete_category(self.user_id, created.id)

    def test_04_api_controllers_return_standard_status_codes(self):
        """Verify API controllers return starlette.status compliant responses"""
        # 1. Non-existent entry returns 404
        res_404 = self.client.get("/api/entries/9999999", headers=self.headers)
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)

        # 2. Empty entry creation returns 400
        res_400 = self.client.post("/api/entries", data={"content": ""}, headers=self.headers)
        self.assertEqual(res_400.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Unauthorized access returns 401
        res_401 = self.client.get("/api/entries/1")
        self.assertEqual(res_401.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4. Auth config returns 200
        res_200 = self.client.get("/api/auth/config")
        self.assertEqual(res_200.status_code, status.HTTP_200_OK)

    def test_05_offline_queue_401_protection_static_contract(self):
        """Verify static/js/api.js implements 401/403 protection and does not purge offline entries (DEBT-01)"""
        api_js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'api.js')
        with open(api_js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Contract checks in syncOfflineQueue:
        self.assertIn("syncOfflineQueue", content)
        self.assertIn("DEBT-01", content)
        self.assertIn("status === 401", content)
        self.assertIn("status === 403", content)
        # Ensure break; occurs on 401/403
        self.assertTrue(
            "if (status === 401 || status === 403" in content or
            "status === 401" in content and "break;" in content,
            "Must halt syncing on 401/403 without deleting offline item"
        )
        # Only unrecoverable errors (400, 422) trigger deletion
        self.assertIn("isUnrecoverableClientError", content)
        self.assertIn("status === 400 || status === 422", content)

    def test_06_modal_a11y_attributes_in_html(self):
        """Verify static/index.html includes role=dialog and aria-modal=true for all modals (DEBT-05)"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # 1. Generic Confirm Modal
        self.assertIn('id="generic-confirm-modal"', html)
        self.assertIn('role="dialog"', html)
        self.assertIn('aria-modal="true"', html)
        self.assertIn('aria-labelledby="generic-confirm-title"', html)

        # 2. Generic Prompt Modal
        self.assertIn('id="generic-prompt-modal"', html)
        self.assertIn('aria-labelledby="generic-prompt-title"', html)

        # 3. Card Export Modal
        self.assertIn('id="card-export-modal"', html)
        self.assertIn('aria-labelledby="card-export-title"', html)

    def test_07_modal_escape_key_listeners(self):
        """Verify static/js/tag-manager.js and card-export.js implement Escape key listeners (DEBT-05)"""
        # tag-manager.js
        tag_mgr_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'tag-manager.js')
        with open(tag_mgr_path, 'r', encoding='utf-8') as f:
            tag_mgr_content = f.read()

        self.assertIn("e.key === 'Escape'", tag_mgr_content)
        self.assertIn("onKeyDown", tag_mgr_content)
        self.assertIn("window.addEventListener('keydown', onKeyDown)", tag_mgr_content)

        # card-export.js
        card_export_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'card-export.js')
        with open(card_export_path, 'r', encoding='utf-8') as f:
            card_export_content = f.read()

        self.assertIn("e.key === 'Escape'", card_export_content)
        self.assertIn("this.close()", card_export_content)


if __name__ == '__main__':
    unittest.main()
