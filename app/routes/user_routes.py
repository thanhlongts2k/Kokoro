"""
Kokoro (心) User Profile Routes
Handles user personalization, avatar processing (WebP 256x256), and profile sync.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

import io
import logging
from typing import Optional
from PIL import Image, UnidentifiedImageError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.auth import get_current_user
from app.repositories.user_repository import UserRepository
from app.services.media_service import MediaService

logger = logging.getLogger("kokoro.users")

MAX_AVATAR_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
MAX_BIO_LENGTH: int = 250
MAX_NAME_LENGTH: int = 100
VALID_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "MPO", "GIF", "HEIF", "BMP"}

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}


async def update_user_profile(request: Request) -> JSONResponse:
    """
    PUT /api/users/profile
    Updates authenticated user's profile:
    - name: string (<= 100 chars, non-empty)
    - bio: string (<= 250 chars)
    - use_custom_profile: boolean
    - avatar_file: optional image file (<= 5MB, auto center-cropped & resized to 256x256 WebP)
    """
    user = get_current_user(request)
    if not user:
        return JSONResponse({
            "status": "error",
            "message": "Vui lòng đăng nhập để chỉnh sửa hồ sơ 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)

    user_id = user["id"]

    # Parse content (multipart/form-data or application/json fallback)
    content_type = request.headers.get("content-type", "")
    avatar_file = None
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        name_val = payload.get("name")
        bio_val = payload.get("bio")
        use_custom_val = payload.get("use_custom_profile")
    else:
        try:
            form = await request.form()
        except Exception as e:
            logger.warning("[UserRoutes] Form parsing error: %s", e)
            return JSONResponse({
                "status": "error",
                "message": "Dữ liệu gửi lên không đúng định dạng form-data 🌸"
            }, status_code=status.HTTP_400_BAD_REQUEST)
        name_val = form.get("name")
        bio_val = form.get("bio")
        use_custom_val = form.get("use_custom_profile")
        avatar_file = form.get("avatar_file")

    # 1. Validate Name
    current_name = user.name if hasattr(user, "name") else user.get("name", "")
    if name_val is not None:
        name = str(name_val).strip()
        if not name:
            return JSONResponse({
                "status": "error",
                "message": "Tên hiển thị không được để trống 🌸"
            }, status_code=status.HTTP_400_BAD_REQUEST)
        if len(name) > MAX_NAME_LENGTH:
            return JSONResponse({
                "status": "error",
                "message": f"Tên hiển thị không được vượt quá {MAX_NAME_LENGTH} ký tự 🌸"
            }, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        name = current_name

    # 2. Validate Bio
    current_bio = user.bio if hasattr(user, "bio") else user.get("bio")
    if bio_val is not None:
        bio = str(bio_val).strip()
        if len(bio) > MAX_BIO_LENGTH:
            return JSONResponse({
                "status": "error",
                "message": f"Châm ngôn sống không được vượt quá {MAX_BIO_LENGTH} ký tự 🌸"
            }, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        bio = current_bio

    # 3. Validate and Parse use_custom_profile flag
    current_use_custom = user.use_custom_profile if hasattr(user, "use_custom_profile") else user.get("use_custom_profile", False)
    if use_custom_val is not None:
        if isinstance(use_custom_val, bool):
            use_custom_profile = use_custom_val
        else:
            use_custom_profile = str(use_custom_val).lower() in ("true", "1", "yes", "on")
    else:
        use_custom_profile = bool(current_use_custom)

    # 4. Process Avatar File if uploaded
    current_custom_avatar = user.custom_avatar_url if hasattr(user, "custom_avatar_url") else user.get("custom_avatar_url")
    custom_avatar_url = current_custom_avatar

    if avatar_file and hasattr(avatar_file, "read"):
        file_bytes = await avatar_file.read()
        if len(file_bytes) > 0:
            # Check maximum size
            if len(file_bytes) > MAX_AVATAR_SIZE_BYTES:
                return JSONResponse({
                    "status": "error",
                    "message": "Kích thước ảnh đại diện không được vượt quá 5MB 🌸"
                }, status_code=status.HTTP_400_BAD_REQUEST)

            # Validate image format and integrity
            try:
                probe_img = Image.open(io.BytesIO(file_bytes))
                fmt = probe_img.format
                if not fmt or fmt.upper() not in VALID_IMAGE_FORMATS:
                    return JSONResponse({
                        "status": "error",
                        "message": "Định dạng tệp ảnh không được hỗ trợ (chỉ nhận JPEG, PNG, WEBP) 🌸"
                    }, status_code=status.HTTP_400_BAD_REQUEST)
            except (UnidentifiedImageError, OSError, ValueError) as img_err:
                logger.warning("[UserRoutes] Invalid image upload by user %s: %s", user_id, img_err)
                return JSONResponse({
                    "status": "error",
                    "message": "Tệp tải lên không phải hình ảnh hợp lệ 🌸"
                }, status_code=status.HTTP_400_BAD_REQUEST)

            # Process square center-crop & resize 256x256 WebP
            try:
                new_avatar_url = MediaService.process_and_save_avatar(file_bytes, user_id)
                # Cleanup old avatar file if present
                if current_custom_avatar and current_custom_avatar != new_avatar_url:
                    MediaService.delete_avatar_file(current_custom_avatar)
                custom_avatar_url = new_avatar_url
            except Exception as proc_err:
                logger.error("[UserRoutes] Error processing avatar: %s", proc_err, exc_info=True)
                return JSONResponse({
                    "status": "error",
                    "message": "Không thể xử lý ảnh đại diện. Vui lòng thử lại sau 🌸"
                }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 5. Persist profile update via repository
    try:
        updated_dto = UserRepository.update_profile(
            user_id=user_id,
            name=name,
            bio=bio,
            custom_avatar_url=custom_avatar_url,
            use_custom_profile=use_custom_profile
        )
    except Exception as db_err:
        logger.error("[UserRoutes] Failed to update profile in database for user %s: %s", user_id, db_err, exc_info=True)
        return JSONResponse({
            "status": "error",
            "message": "Lỗi lưu dữ liệu hồ sơ vào cơ sở dữ liệu 🌸"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not updated_dto:
        return JSONResponse({
            "status": "error",
            "message": "Không tìm thấy người dùng để cập nhật 🌸"
        }, status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse({
        "status": "success",
        "message": "Cập nhật hồ sơ cá nhân thành công 🌸",
        "user": updated_dto.to_dict()
    }, headers=NO_CACHE_HEADERS)


user_routes = [
    Route("/api/users/profile", update_user_profile, methods=["PUT", "POST"]),
]
