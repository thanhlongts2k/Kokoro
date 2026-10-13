"""
Kokoro (心) Tag Schemas (SSoT)
Strictly typed Data Transfer Objects for tag management.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class TagDTO:
    """Strongly typed DTO representing a tag with its usage metrics."""
    id: int
    name: str
    usage_count: int = 0
    created_at: Optional[str] = None
    user_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to serializable dictionary for API response."""
        data = asdict(self)
        if self.created_at:
            data["createdAt"] = self.created_at
        return data


@dataclass(frozen=True)
class TagCreateDTO:
    """Input payload for creating a new tag."""
    name: str


@dataclass(frozen=True)
class TagUpdateDTO:
    """Input payload for renaming a tag."""
    name: str
