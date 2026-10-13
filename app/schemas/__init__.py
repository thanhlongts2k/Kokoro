"""
Schemas package exports for Kokoro application (SSoT).
Strictly typed Data Transfer Objects for domain isolation.
"""

from app.schemas.maintenance import CleanupStatsDTO, MaintenanceResponseDTO
from app.schemas.category import CategoryDTO, CategoryCreateDTO, CategoryUpdateDTO
from app.schemas.tag import TagDTO, TagCreateDTO, TagUpdateDTO
from app.schemas.stats import MoodCountDTO, StatsSummaryDTO
from app.schemas.user import UserDTO, UserSessionDTO
from app.schemas.entry import EntryPhotoDTO, EntryDTO, EntryCreateDTO, EntryUpdateDTO, EntryFilterDTO

__all__ = [
    "CleanupStatsDTO",
    "MaintenanceResponseDTO",
    "CategoryDTO",
    "CategoryCreateDTO",
    "CategoryUpdateDTO",
    "TagDTO",
    "TagCreateDTO",
    "TagUpdateDTO",
    "MoodCountDTO",
    "StatsSummaryDTO",
    "UserDTO",
    "UserSessionDTO",
    "EntryPhotoDTO",
    "EntryDTO",
    "EntryCreateDTO",
    "EntryUpdateDTO",
    "EntryFilterDTO",
]
