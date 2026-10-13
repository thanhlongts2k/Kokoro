"""
Unit & Integration Tests for Kokoro Modular Clean Architecture Refactoring (Phase 1 & Phase 2)
Covers:
1. Schemas Strict Typing & Serialization (CategoryDTO, TagDTO, StatsSummaryDTO, UserDTO, EntryDTO)
2. CategoryRepository direct CRUD & Invariants (Scoped to user, duplicate check, mood sync)
3. TagRepository direct CRUD & Invariants (Auto-prefix '#', merge duplicate, orphan cleanup)
4. StatsRepository Streak & Mood breakdown calculations
5. HTTP Endpoints via Starlette TestClient (Scoped auth, response contracts, zero regression)
"""

import sys
import os
import unittest
from datetime import datetime
from starlette.testclient import TestClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.database import init_db, get_cursor, seed_mock_users_for_testing, clean_mock_users_after_testing
from app.auth import create_session_token
from app.schemas.category import CategoryDTO, CategoryCreateDTO, CategoryUpdateDTO
from app.schemas.tag import TagDTO, TagCreateDTO, TagUpdateDTO
from app.schemas.stats import MoodCountDTO, StatsSummaryDTO
from app.schemas.user import UserDTO, UserSessionDTO
from app.schemas.entry import EntryPhotoDTO, EntryDTO, EntryCreateDTO
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.stats_repository import StatsRepository


class TestModularSchemasAndRepositories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_mock_users_for_testing()
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

    def test_01_schema_dataclasses_strict_typing(self):
        """Verify strict typing and dictionary serialization for all newly created DTOs"""
        # Category DTOs
        cat_create = CategoryCreateDTO(name="Test Category", icon="🌸", color="#f472b6")
        self.assertEqual(cat_create.name, "Test Category")
        cat_dto = CategoryDTO(id=1, user_id=self.user_id, name="Test Category", icon="🌸", color="#f472b6", sort_order=0, usage_count=5)
        cat_dict = cat_dto.to_dict()
        self.assertEqual(cat_dict["name"], "Test Category")
        self.assertEqual(cat_dict["usage_count"], 5)

        # Tag DTOs
        tag_create = TagCreateDTO(name="#sakura")
        self.assertEqual(tag_create.name, "#sakura")
        tag_dto = TagDTO(id=1, user_id=self.user_id, name="#sakura", usage_count=3)
        tag_dict = tag_dto.to_dict()
        self.assertEqual(tag_dict["name"], "#sakura")
        self.assertEqual(tag_dict["usage_count"], 3)

        # Stats DTOs
        mood_dto = MoodCountDTO(count=10, percent=50.0)
        self.assertEqual(mood_dto.count, 10)
        stats_dto = StatsSummaryDTO(
            total_entries=20,
            total_photos=15,
            streak_days=5,
            serene_percent=50.0,
            mood_breakdown={"serene": {"count": 10, "percent": 50.0}},
            mood_counts={"serene": 10}
        )
        stats_dict = stats_dto.to_dict()
        self.assertEqual(stats_dict["totalEntries"], 20)
        self.assertEqual(stats_dict["streakDays"], 5)
        self.assertIn("serene", stats_dict["moodBreakdown"])

        # User DTOs
        user_dto = UserDTO(id=self.user_id, email=self.user["email"], name=self.user["name"])
        self.assertEqual(user_dto.to_dict()["email"], self.user["email"])

        # Entry DTOs
        photo_dto = EntryPhotoDTO(id=1, url="/uploads/originals/test.webp", thumb_url="/uploads/thumbnails/test.webp", name="test.webp")
        self.assertEqual(photo_dto.to_dict()["url"], "/uploads/originals/test.webp")
        entry_dto = EntryDTO(id=1, user_id=self.user_id, title="Kyoto", content="Kyoto morning", mood="serene", tags=["#kyoto"], photos=[photo_dto])
        self.assertEqual(entry_dto.to_dict()["tags"], ["#kyoto"])

    def test_02_category_repository_lifecycle(self):
        """Test CategoryRepository create, find_by_name, update, and delete methods"""
        test_cat_name = f"Test_Repo_Cat_{int(datetime.now().timestamp())}"
        create_dto = CategoryCreateDTO(name=test_cat_name, icon="🍵", color="#10b981")
        
        created = CategoryRepository.create_category(self.user_id, create_dto)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, test_cat_name)

        # Duplicate check
        dup = CategoryRepository.find_by_name(self.user_id, test_cat_name)
        self.assertIsNotNone(dup)
        self.assertEqual(dup.id, created.id)

        # Update
        updated_name = f"{test_cat_name}_updated"
        update_dto = CategoryUpdateDTO(name=updated_name, icon="🍃", color="#059669")
        updated = CategoryRepository.update_category(self.user_id, created.id, update_dto)
        self.assertEqual(updated.name, updated_name)
        self.assertEqual(updated.icon, "🍃")

        # Delete
        deleted_name = CategoryRepository.delete_category(self.user_id, created.id)
        self.assertEqual(deleted_name, updated_name)

        # Verify not found after delete
        not_found = CategoryRepository.find_by_id(self.user_id, created.id)
        self.assertIsNone(not_found)

    def test_03_tag_repository_lifecycle_and_merging(self):
        """Test TagRepository create, update with auto-merge, and orphan cleanup"""
        tag_a_name = f"#TagA_{int(datetime.now().timestamp())}"
        tag_b_name = f"#TagB_{int(datetime.now().timestamp())}"

        # Create tag A without # prefix to verify auto-formatting
        tag_a = TagRepository.create_tag(self.user_id, TagCreateDTO(name=tag_a_name.lstrip("#")))
        self.assertTrue(tag_a.name.startswith("#"))
        self.assertEqual(tag_a.name, tag_a_name)

        # Create tag B
        tag_b = TagRepository.create_tag(self.user_id, TagCreateDTO(name=tag_b_name))
        self.assertEqual(tag_b.name, tag_b_name)

        # Update tag A to merge into tag B
        merged = TagRepository.update_tag(self.user_id, tag_a.id, TagUpdateDTO(name=tag_b_name))
        self.assertEqual(merged.name, tag_b_name)
        self.assertEqual(merged.id, tag_b.id)

        # Verify tag A no longer exists
        tag_a_check = TagRepository.find_by_id(self.user_id, tag_a.id)
        self.assertIsNone(tag_a_check)

        # Clean up tag B
        deleted = TagRepository.delete_tag(self.user_id, tag_b.id)
        self.assertTrue(deleted)

    def test_04_stats_repository_calculation(self):
        """Test StatsRepository calculation for total entries and streaks"""
        stats = StatsRepository.get_stats_summary(self.user_id)
        self.assertIsInstance(stats, StatsSummaryDTO)
        self.assertGreaterEqual(stats.total_entries, 0)
        self.assertGreaterEqual(stats.streak_days, 0)

        stats_dict = stats.to_dict()
        self.assertEqual(stats_dict["status"], "success")
        self.assertIn("totalEntries", stats_dict)
        self.assertIn("streakDays", stats_dict)
        self.assertIn("moodBreakdown", stats_dict)

    def test_05_category_http_endpoints(self):
        """Verify Category modular REST APIs via TestClient"""
        # Unauthenticated check
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 401)

        # List categories
        resp = self.client.get("/api/categories", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["categories"], list)

        # Create category via API
        cat_name = f"HTTP_Cat_{int(datetime.now().timestamp())}"
        resp = self.client.post("/api/categories", json={"name": cat_name, "icon": "☕", "color": "#78350f"}, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        created_data = resp.json()
        cat_id = created_data["category"]["id"]

        # Duplicate create returns 409
        dup_resp = self.client.post("/api/categories", json={"name": cat_name}, headers=self.headers)
        self.assertEqual(dup_resp.status_code, 409)

        # Update category via API
        resp = self.client.put(f"/api/categories/{cat_id}", json={"name": f"{cat_name}_Renamed", "icon": "🍵"}, headers=self.headers)
        self.assertEqual(resp.status_code, 200)

        # Delete category via API
        del_resp = self.client.delete(f"/api/categories/{cat_id}", headers=self.headers)
        self.assertEqual(del_resp.status_code, 200)

    def test_06_tag_http_endpoints(self):
        """Verify Tag modular REST APIs via TestClient"""
        # Unauthenticated check
        resp = self.client.get("/api/tags")
        self.assertEqual(resp.status_code, 401)

        # List tags
        resp = self.client.get("/api/tags", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIsInstance(data["tags"], list)

        # Create tag via API
        tag_name = f"HTTPTag_{int(datetime.now().timestamp())}"
        resp = self.client.post("/api/tags", json={"name": tag_name}, headers=self.headers)
        self.assertEqual(resp.status_code, 201)
        tag_data = resp.json()
        tag_id = tag_data["tag"]["id"]
        self.assertTrue(tag_data["tag"]["name"].startswith("#"))

        # Update tag via API
        resp = self.client.put(f"/api/tags/{tag_id}", json={"name": f"{tag_name}_Renamed"}, headers=self.headers)
        self.assertEqual(resp.status_code, 200)

        # Cleanup orphans API
        cleanup_resp = self.client.delete("/api/tags/cleanup-orphans", headers=self.headers)
        self.assertEqual(cleanup_resp.status_code, 200)
        self.assertIn("deleted_count", cleanup_resp.json())

    def test_07_stats_http_endpoints(self):
        """Verify Stats summary modular endpoint via TestClient"""
        # Unauthenticated check
        resp = self.client.get("/api/stats/summary")
        self.assertEqual(resp.status_code, 401)

        # Authenticated check
        resp = self.client.get("/api/stats/summary", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("totalEntries", data)
        self.assertIn("streakDays", data)
        self.assertIn("moodBreakdown", data)


if __name__ == "__main__":
    unittest.main()
