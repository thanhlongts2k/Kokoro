"""
Kokoro (心) User Schemas (SSoT)
Strictly typed Data Transfer Objects for user profile, authentication, and session.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class UserDTO:
    """Strongly typed DTO representing an authenticated user."""
    id: int
    email: str
    name: str
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None

    def __getitem__(self, key: str) -> Any:
        val = getattr(self, key, None)
        if val is None:
            lookup = {
                "createdAt": self.created_at,
                "lastLogin": self.last_login,
                "googleId": self.google_id,
                "avatarUrl": self.avatar_url,
            }
            if key in lookup:
                return lookup[key]
        return val

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for JSON serialization with camelCase aliases."""
        data = asdict(self)
        if self.created_at:
            data["createdAt"] = self.created_at
        if self.last_login:
            data["lastLogin"] = self.last_login
        return data


@dataclass(frozen=True)
class UserSessionDTO:
    """User profile paired with authentication token and cookie directives."""
    user: UserDTO
    token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user.to_dict(),
            "token": self.token
        }
