"""
Kokoro (心) Entry Controller Routes
Strict presentation controller: handles HTTP, parses DTOs, delegates to EntryRepository & MediaService.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers, < 300 lines.
"""

import logging
from typing import Any, Dict, List, Optional
import psycopg2
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from app.auth import get_current_user
from app.services.media_service import MediaService
from app.repositories.entry_repository import EntryRepository
from app.schemas.entry import EntryCreateDTO, EntryUpdateDTO, EntryFilterDTO
from app.exceptions import KokoroDomainError, EntryNotFoundError, InvalidInputError
from app.routes.entry_helpers import (
    parse_category_id, parse_deleted_photo_ids, process_photos, clean_photos,
    export_entries, import_entries, handle_route_exception
)

# Aliases for internal backward compatibility
_parse_category_id = parse_category_id
_parse_deleted_photo_ids = parse_deleted_photo_ids
_process_photos = process_photos
_clean_photos = clean_photos

logger = logging.getLogger("kokoro.routes.entry")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}

DEFAULT_PAGE_SIZE = 15
MAX_PAGE_SIZE = 50


def require_auth(request: Request):
    """Authenticate request or return 401 JSONResponse tuple (user, err_response)."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error", "message": "Vui lòng đăng nhập để xem và quản lý nhật ký 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)
    return user, None


async def get_entries(request: Request) -> JSONResponse:
    """Retrieve entries strictly scoped to authenticated user with safe server-side pagination."""
    user, err = require_auth(request)
    if err:
        return err

    qp = request.query_params
    is_all = qp.get("all") == "true"

    if is_all:
        limit_val = 5000
        offset_val = 0
    else:
        try:
            raw_limit = qp.get("limit")
            limit_val = max(1, min(int(raw_limit), MAX_PAGE_SIZE)) if raw_limit is not None else DEFAULT_PAGE_SIZE
        except (ValueError, TypeError):
            limit_val = DEFAULT_PAGE_SIZE

        try:
            raw_offset = qp.get("offset")
            offset_val = max(0, int(raw_offset)) if raw_offset is not None else 0
        except (ValueError, TypeError):
            offset_val = 0

    filters = EntryFilterDTO(
        mood=qp.get("mood"), category_param=qp.get("category_id") or qp.get("category"),
        tag=qp.get("tag"), month=qp.get("month"), search=qp.get("search"),
        limit=limit_val, offset=offset_val
    )
    try:
        entries = EntryRepository.get_entries(user["id"], filters)
        total_count = EntryRepository.count_entries(user["id"], filters)
        has_more = (offset_val + len(entries)) < total_count and not is_all

        return JSONResponse({
            "status": "success",
            "entries": entries,
            "pagination": {
                "total": total_count,
                "limit": limit_val,
                "offset": offset_val,
                "has_more": has_more
            }
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return handle_route_exception(e, "tải danh sách nhật ký")


async def get_calendar_summary(request: Request) -> JSONResponse:
    """Ultra-lightweight endpoint returning minimal entry summary for calendar and profile streak."""
    user, err = require_auth(request)
    if err:
        return err

    month = request.query_params.get("month")
    try:
        summary = EntryRepository.get_calendar_summary(user["id"], month=month)
        return JSONResponse({"status": "success", "entries": summary}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return handle_route_exception(e, "tải tóm tắt lịch")


async def get_entry_by_id(request: Request) -> JSONResponse:
    """Retrieve a single entry by id strictly owned by current user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        entry_id = int(request.path_params["id"])
    except (ValueError, TypeError, KeyError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)
    try:
        entry = EntryRepository.get_by_id(entry_id, user["id"])
        if not entry:
            return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết"}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)
        return JSONResponse({"status": "success", "entry": entry}, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return handle_route_exception(e, "tải bài viết")


async def create_entry(request: Request) -> JSONResponse:
    """Create a new journal entry with multipart form data belonging to user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        form = await request.form()
    except Exception as e:
        logger.warning("[entry_routes.create_entry] Lỗi phân tích multipart form: %s", e)
        return JSONResponse({"status": "error", "message": f"Dữ liệu form không hợp lệ: {e}"}, status_code=status.HTTP_400_BAD_REQUEST)

    title, content = form.get("title", "").strip() or "Khoảnh khắc tĩnh lặng", form.get("content", "").strip()
    photo_files = form.getlist("photos")
    if not content and not any(hasattr(p, "filename") and p.filename for p in photo_files):
        return JSONResponse({"status": "error", "message": "Vui lòng nhập nội dung hoặc đính kèm ít nhất một hình ảnh 🌸"}, status_code=status.HTTP_400_BAD_REQUEST)

    tags = [t.strip() for t in form.get("tags", "").replace(",", " ").split() if t.strip()]
    processed_photos = []
    try:
        processed_photos = await process_photos(photo_files)
        dto = EntryCreateDTO(
            title=title, content=content, mood=form.get("mood", "serene").strip(),
            weather=form.get("weather", "sunny").strip(),
            entry_date=form.get("entry_date", "").strip() or None,
            created_at=form.get("created_at", "").strip() or None,
            category_id=parse_category_id(form.get("category_id")), tags=tags
        )
        created = EntryRepository.create_entry(user["id"], dto, processed_photos)
        return JSONResponse({
            "status": "success", "message": "Đã lưu nhật ký thành công 🌸",
            "entry_id": created["id"], "id": created["id"], "entry": created
        }, status_code=status.HTTP_201_CREATED, headers=NO_CACHE_HEADERS)
    except Exception as e:
        clean_photos(processed_photos)
        return handle_route_exception(e, "tạo bài viết")


async def update_entry(request: Request) -> JSONResponse:
    """Update an existing journal entry strictly owned by user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        entry_id = int(request.path_params["id"])
        form = await request.form()
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.warning("[entry_routes.update_entry] Lỗi form parse: %s", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

    tags = [t.strip() for t in form.get("tags", "").replace(",", " ").split() if t.strip()]
    del_ids = parse_deleted_photo_ids(form)
    cat_id = parse_category_id(form.get("category_id")) if "category_id" in form else None

    processed_photos = []
    try:
        processed_photos = await process_photos(form.getlist("photos"))
        dto = EntryUpdateDTO(
            title=form.get("title", "").strip() or "Khoảnh khắc tĩnh lặng",
            content=form.get("content", "").strip(),
            mood=form.get("mood", "serene").strip(), weather=form.get("weather", "sunny").strip(),
            entry_date=form.get("entry_date", "").strip() or None,
            created_at=form.get("created_at", "").strip() or None,
            category_id=cat_id, update_category="category_id" in form,
            tags=tags, deleted_photo_ids=del_ids
        )
        updated, deleted_paths = EntryRepository.update_entry(entry_id, user["id"], dto, processed_photos)
        if not updated:
            return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền sửa."}, status_code=status.HTTP_404_NOT_FOUND)
        if deleted_paths:
            MediaService.delete_photo_files(deleted_paths)
        return JSONResponse({
            "status": "success", "message": "Đã cập nhật bài viết thành công 🌸",
            "entry_id": updated["id"], "id": updated["id"], "entry": updated
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        clean_photos(processed_photos)
        return handle_route_exception(e, "cập nhật bài viết")


async def delete_entry_photo(request: Request) -> JSONResponse:
    """Delete a specific photo from an entry strictly owned by user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        entry_id = int(request.path_params["id"])
        photo_id = int(request.path_params["photo_id"])
    except (ValueError, TypeError, KeyError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        deleted_paths = EntryRepository.delete_single_photo(entry_id, photo_id, user["id"])
        if not deleted_paths:
            return JSONResponse({"status": "error", "message": "Không tìm thấy ảnh hoặc bạn không có quyền xóa."}, status_code=status.HTTP_404_NOT_FOUND)
        MediaService.delete_photo_files(deleted_paths)
        return JSONResponse({"status": "success", "message": "Đã xóa ảnh thành công 🌸", "photo_id": photo_id})
    except Exception as e:
        return handle_route_exception(e, "xóa ảnh")


async def delete_entry(request: Request) -> JSONResponse:
    """Delete an entry and all its associated photos strictly owned by user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        entry_id = int(request.path_params["id"])
    except (ValueError, TypeError, KeyError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        photo_paths = EntryRepository.get_photo_paths_for_entry(entry_id, user["id"])
        if not EntryRepository.delete_entry(entry_id, user["id"]):
            return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền xóa."}, status_code=status.HTTP_404_NOT_FOUND)
        if photo_paths:
            MediaService.delete_photo_files(photo_paths)
        return JSONResponse({"status": "success", "message": "Đã xóa bài viết thành công. 🌸", "id": entry_id})
    except Exception as e:
        return handle_route_exception(e, "xóa bài viết")


async def toggle_pin_entry(request: Request) -> JSONResponse:
    """Toggle is_pinned status of an entry strictly owned by user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        entry_id = int(request.path_params["id"])
    except (ValueError, TypeError, KeyError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        is_pinned = EntryRepository.toggle_pin(entry_id, user["id"])
        if is_pinned is None:
            return JSONResponse({"status": "error", "message": "Không tìm thấy bài viết hoặc bạn không có quyền ghim."}, status_code=status.HTTP_404_NOT_FOUND)
        return JSONResponse({
            "status": "success", "id": entry_id, "is_pinned": is_pinned,
            "message": "Đã ghim bài viết ✨" if is_pinned else "Đã bỏ ghim bài viết"
        })
    except Exception as e:
        return handle_route_exception(e, "ghim bài viết")


# =========================================================================
# ROUTE TABLE (Scoped Strictly to Entries)
# =========================================================================
entry_routes = [
    Route("/api/entries", get_entries, methods=["GET"]),
    Route("/api/entries", create_entry, methods=["POST"]),
    Route("/api/entries/calendar-summary", get_calendar_summary, methods=["GET"]),
    Route("/api/entries/export", export_entries, methods=["GET"]),
    Route("/api/entries/import", import_entries, methods=["POST"]),
    Route("/api/entries/{id:int}", get_entry_by_id, methods=["GET"]),
    Route("/api/entries/{id:int}", update_entry, methods=["PUT"]),
    Route("/api/entries/{id:int}", delete_entry, methods=["DELETE"]),
    Route("/api/entries/{id:int}/photos/{photo_id:int}", delete_entry_photo, methods=["DELETE"]),
    Route("/api/entries/{id:int}/pin", toggle_pin_entry, methods=["PATCH"]),
]
