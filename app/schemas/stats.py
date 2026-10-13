"""
Kokoro (心) Statistics Schemas (SSoT)
Strictly typed Data Transfer Objects for summary analytics and mood breakdown.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass(frozen=True)
class MoodCountDTO:
    """Breakdown metrics for a specific mood."""
    count: int
    percent: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StatsSummaryDTO:
    """Summary statistics strictly scoped to the authenticated user."""
    total_entries: int
    total_photos: int
    streak_days: int
    serene_percent: float
    mood_breakdown: Dict[str, Dict[str, Any]]
    mood_counts: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        """Format as expected by Kokoro Client frontend."""
        return {
            "status": "success",
            "totalEntries": self.total_entries,
            "totalPhotos": self.total_photos,
            "streakDays": self.streak_days,
            "serenePercent": self.serene_percent,
            "moodBreakdown": self.mood_breakdown,
            "moodCounts": self.mood_counts
        }
