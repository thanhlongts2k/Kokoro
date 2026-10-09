import os
import uuid
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image, ImageOps
from app.config import Config

ORIGINALS_DIR = Config.UPLOAD_DIR / "originals"
THUMBNAILS_DIR = Config.UPLOAD_DIR / "thumbnails"

ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

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

        # Auto-rotate based on EXIF data
        img = ImageOps.exif_transpose(img)

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
