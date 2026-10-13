"""
Repositories package exports for Kokoro application (SSoT).
Data Access Objects (DAO) isolating PostgreSQL persistence from Domain & Controllers.
"""

from app.repositories.photo_repository import PhotoRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.entry_repository import EntryRepository

__all__ = [
    "PhotoRepository",
    "CategoryRepository",
    "TagRepository",
    "StatsRepository",
    "UserRepository",
    "EntryRepository",
]
