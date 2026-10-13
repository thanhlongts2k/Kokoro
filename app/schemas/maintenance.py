"""
Kokoro (心) Maintenance & Diagnostics Schemas (SSoT)
Strictly typed Data Transfer Objects (DTO) for maintenance and orphan cleanup operations.
Forbids raw untyped dictionaries as per AGENTS.md compliance guidelines.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass(frozen=True)
class CleanupStatsDTO:
    """Strongly typed metrics returned by MediaService orphan scan and cleanup."""
    scanned_files: int
    active_files_in_db: int
    deleted_count: int
    skipped_grace_period: int
    freed_bytes: int
    freed_mb: float
    grace_period_hours: float
    deleted_filenames: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to serializable dictionary for API response payloads."""
        return asdict(self)


@dataclass(frozen=True)
class MaintenanceResponseDTO:
    """Standardized maintenance endpoint JSON envelope."""
    status: str
    message: str
    data: CleanupStatsDTO

    def to_dict(self) -> Dict[str, Any]:
        """Convert response envelope to JSON serializable structure."""
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data.to_dict()
        }
