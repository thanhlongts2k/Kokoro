"""
Kokoro (心) Category Schemas (SSoT)
Strictly typed Data Transfer Objects for category/mood taxonomy.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class CategoryDTO:
    """Strongly typed DTO representing a category in Kokoro."""
    id: int
    user_id: int
    name: str
    icon: str
    color: str
    sort_order: int
    created_at: Optional[str] = None
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to serializable dictionary for client response."""
        data = asdict(self)
        if self.created_at:
            data["createdAt"] = self.created_at
        return data


@dataclass(frozen=True)
class CategoryCreateDTO:
    """Input payload for creating a new category."""
    name: str
    icon: str = "📁"
    color: str = "#ec4899"


@dataclass(frozen=True)
class CategoryUpdateDTO:
    """Input payload for updating an existing category."""
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
