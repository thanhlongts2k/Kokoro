import os
import time
import uuid
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from app.config import Config
from app.schemas.maintenance import CleanupStatsDTO
from app.repositories.photo_repository import PhotoRepository

ORIGINALS_DIR = Config.UPLOAD_DIR / "originals"
THUMBNAILS_DIR = Config.UPLOAD_DIR / "thumbnails"

ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

# Safe threshold for decompression bomb protection (~89 MegaPixels)
Image.MAX_IMAGE_PIXELS = 89478485

class MediaService:
    MAX_DIMENSION: int = 1600
    THUMB_DIMENSION: int = 400
    WEBP_QUALITY: int = 82

    @classmethod
    def process_and_save_image(cls, file_bytes: bytes, original_filename: str) -> Tuple[str, str, int, int, int]:
        """
        Process an uploaded image using Pillow:
        - Auto-orient based on EXIF
        - Downscale to MAX_DIMENSION if needed
        - Convert to WebP format
        - Generate thumbnail WebP (max 400px)
        - Returns: (file_path, thumb_path, file_size, width, height)
        """
        import io
        img = Image.open(io.BytesIO(file_bytes))

        # Auto-rotate based on EXIF data safely
        try:
            transposed = ImageOps.exif_transpose(img)
            if transposed is not None:
                img = transposed
        except Exception as e:
            print(f"[MediaService] EXIF orientation warning: {e}")

        # Convert palette/CMYK to RGB/RGBA for safe WebP encoding
        if img.mode in ("P", "CMYK"):
            img = img.convert("RGBA" if "transparency" in img.info else "RGB")

        orig_w, orig_h = img.size

        # Scale down original if exceeds MAX_DIMENSION
        if max(orig_w, orig_h) > cls.MAX_DIMENSION:
            scale_ratio = cls.MAX_DIMENSION / max(orig_w, orig_h)
            new_w = int(orig_w * scale_ratio)
            new_h = int(orig_h * scale_ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        final_w, final_h = img.size

        # Generate unique filename identifier
        file_uuid = uuid.uuid4().hex
        orig_filename = f"{file_uuid}.webp"
        thumb_filename = f"{file_uuid}_thumb.webp"

        orig_full_path = ORIGINALS_DIR / orig_filename
        thumb_full_path = THUMBNAILS_DIR / thumb_filename

        # Save main WebP
        img.save(orig_full_path, "WEBP", quality=cls.WEBP_QUALITY, method=4)
        file_size = os.path.getsize(orig_full_path)

        # Generate and save thumbnail
        thumb_img = img.copy()
        thumb_img.thumbnail((cls.THUMB_DIMENSION, cls.THUMB_DIMENSION), Image.Resampling.LANCZOS)
        thumb_img.save(thumb_full_path, "WEBP", quality=cls.WEBP_QUALITY, method=4)

        # Relative paths stored for serving via /uploads/...
        rel_file_path = f"uploads/originals/{orig_filename}"
        rel_thumb_path = f"uploads/thumbnails/{thumb_filename}"

        return rel_file_path, rel_thumb_path, file_size, final_w, final_h

    @classmethod
    def delete_photo_files(cls, file_paths: List[str]) -> None:
        """Safely delete photo files from disk given relative paths."""
        for path_str in file_paths:
            if not path_str or not path_str.startswith("uploads/"):
                continue
            full_path = Config.BASE_DIR / path_str
            if full_path.exists() and full_path.is_file():
                try:
                    full_path.unlink()
                except Exception as e:
                    print(f"[MediaService] Warning: Could not delete {full_path}: {e}")

    @classmethod
    def scan_and_cleanup_orphans(cls, grace_period_hours: float = 2.0) -> CleanupStatsDTO:
        """
        Scan physical storage directories (originals & thumbnails), match against active database records,
        and safely remove orphaned media files.
        
        CRITICAL ARCHITECTURE & SAFETY RULES (AGENTS.md):
        1. Layer Isolation: PhotoRepository isolates all SQL queries, preventing DB leakage into domain service.
        2. Strict Typing: Returns strongly-typed CleanupStatsDTO instead of untyped string-keyed dicts.
        3. Windows Path Normalization: Compares strictly by file basename (e.g. 'abc.webp') rather than full path
           strings to eliminate cross-OS path separator mismatches ('/' vs '\\').
        4. Grace Period Protection: Skips unreferenced files modified within the last `grace_period_hours`
           (default: 2 hours) to avoid deleting active editor drafts in-progress.
        5. Never deletes system or hidden files (.gitkeep, .DS_Store, etc.).
        """
        # 1. Fetch active photo filenames via persistence abstraction
        active_filenames = PhotoRepository.get_all_active_photo_filenames()

        # 2. Setup scan metrics & cutoff threshold
        now = time.time()
        cutoff_time = now - (grace_period_hours * 3600.0)

        scanned_count = 0
        deleted_count = 0
        skipped_grace_period = 0
        freed_bytes = 0
        deleted_filenames: List[str] = []

        directories_to_scan = [ORIGINALS_DIR, THUMBNAILS_DIR]

        for target_dir in directories_to_scan:
            if not target_dir.exists() or not target_dir.is_dir():
                continue

            for file_path in target_dir.iterdir():
                # Skip non-files or hidden/keep files
                if not file_path.is_file() or file_path.name.startswith("."):
                    continue

                scanned_count += 1
                fname = file_path.name

                # If file exists in DB active set -> KEEP (SAFE)
                if fname in active_filenames:
                    continue

                # File is unreferenced in DB. Check Grace Period.
                try:
                    file_mtime = file_path.stat().st_mtime
                    file_size = file_path.stat().st_size
                except OSError:
                    continue

                if file_mtime > cutoff_time:
                    # Recently created/modified draft asset within grace period -> PROTECT
                    skipped_grace_period += 1
                    continue

                # Orphaned file older than grace period threshold -> SAFE DELETION
                try:
                    file_path.unlink()
                    deleted_count += 1
                    freed_bytes += file_size
                    deleted_filenames.append(fname)
                except Exception as del_err:
                    print(f"[MediaService] Error removing orphaned file {file_path}: {del_err}")

        freed_mb = round(freed_bytes / (1024 * 1024), 2)

        return CleanupStatsDTO(
            scanned_files=scanned_count,
            active_files_in_db=len(active_filenames),
            deleted_count=deleted_count,
            skipped_grace_period=skipped_grace_period,
            freed_bytes=freed_bytes,
            freed_mb=freed_mb,
            grace_period_hours=grace_period_hours,
            deleted_filenames=deleted_filenames
        )


