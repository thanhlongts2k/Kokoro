"""
Kokoro (心) Entry Schemas (SSoT)
Strictly typed Data Transfer Objects for diary entries and attachments.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class EntryPhotoDTO:
    """Attached photo metadata within an entry."""
    id: int
    url: str
    thumb_url: str
    name: str
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "thumbUrl": self.thumb_url,
            "name": self.name,
            "size": self.size,
            "width": self.width,
            "height": self.height,
            "order": self.order
        }


@dataclass(frozen=True)
class EntryDTO:
    """Strongly typed DTO representing a diary entry."""
    id: int
    user_id: int
    content: str
    title: Optional[str] = None
    mood: str = "serene"
    weather: str = "sunny"
    entry_date: str = ""
    is_pinned: bool = False
    created_at: str = ""
    updated_at: str = ""
    photos: List[EntryPhotoDTO] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    category_color: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entry DTO to frontend JSON representation."""
        return {
            "id": self.id,
            "userId": self.user_id,
            "categoryId": self.category_id,
            "categoryName": self.category_name,
            "categoryIcon": self.category_icon,
            "categoryColor": self.category_color,
            "title": self.title,
            "content": self.content,
            "mood": self.mood,
            "weather": self.weather,
            "entryDate": self.entry_date,
            "isPinned": self.is_pinned,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "photos": [p.to_dict() for p in self.photos],
            "tags": self.tags
        }


@dataclass(frozen=True)
class EntryCreateDTO:
    """Input payload for creating a new diary entry."""
    content: str
    title: Optional[str] = None
    mood: str = "serene"
    weather: str = "sunny"
    entry_date: Optional[str] = None
    created_at: Optional[str] = None
    category_id: Optional[int] = None
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class EntryUpdateDTO:
    """Input payload for updating an existing diary entry."""
    title: str
    content: str
    mood: str = "serene"
    weather: str = "sunny"
    entry_date: Optional[str] = None
    created_at: Optional[str] = None
    category_id: Optional[int] = None
    update_category: bool = False
    tags: List[str] = field(default_factory=list)
    deleted_photo_ids: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class EntryFilterDTO:
    """Query filters for retrieving entries."""
    mood: Optional[str] = None
    category_param: Optional[str] = None
    tag: Optional[str] = None
    month: Optional[str] = None
    search: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
