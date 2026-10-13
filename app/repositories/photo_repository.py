"""
Kokoro (心) Photo Repository
Data Access Object (DAO) isolating SQL persistence queries for entry photos.
Complies with AGENTS.md Layer Isolation rules:
Domain/Application Services must never execute raw SQL directly.
"""

import os
from typing import Set
from app.database import get_cursor


class PhotoRepository:
    """
    Persistence abstraction for the entry_photos table in PostgreSQL.
    """

    @classmethod
    def get_all_active_photo_filenames(cls) -> Set[str]:
        """
        Query all active photo file paths from PostgreSQL and return a set of normalized basenames.
        CRITICAL WINDOWS PATH FIX:
        Normalizes both Unix ('/') and Windows ('\\') paths and extracts only pure filenames
        (e.g., '1234abcd.webp') to avoid cross-OS path separator mismatches.
        """
        active_filenames: Set[str] = set()
        with get_cursor() as cur:
            cur.execute("SELECT file_path, thumb_path FROM entry_photos;")
            rows = cur.fetchall()
            for r in rows:
                if r.get("file_path"):
                    clean_orig = str(r["file_path"]).replace("\\", "/")
                    active_filenames.add(os.path.basename(clean_orig).strip())
                if r.get("thumb_path"):
                    clean_thumb = str(r["thumb_path"]).replace("\\", "/")
                    active_filenames.add(os.path.basename(clean_thumb).strip())

        return active_filenames
