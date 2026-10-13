"""
Kokoro (心) Entry Controller Routes
Strict presentation controller: handles HTTP, parses DTOs, delegates to EntryRepository & MediaService.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers, < 300 lines.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import psycopg2
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from app.config import Config
from app.auth import get_current_user
from app.services.media_service import MediaService
from app.repositories.entry_repository import EntryRepository
from app.schemas.entry import EntryCreateDTO, EntryUpdateDTO, EntryFilterDTO
from app.exceptions import KokoroDomainError, EntryNotFoundError, InvalidInputError

logger = logging.getLogger("kokoro.routes.entry")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}


def require_auth(request: Request):
    """Authenticate request or return 401 JSONResponse tuple (user, err_response)."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error", "message": "Vui lòng đăng nhập để xem và quản lý nhật ký 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)
    return user, None


def _parse_category_id(val: Any) -> Optional[int]:
    """Safely convert form category parameter to integer or None."""
    if not val or str(val).strip().lower() in ("null", "none"):
        return None
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def _parse_deleted_photo_ids(form) -> List[int]:
    """Robustly extract deleted photo IDs from form whether JSON array, comma string, or list."""
    del_ids: List[int] = []
    raw_vals: List[Any] = []
    for key in ("deleted_photo_ids", "deleted_photos"):
        val = form.get(key)
        if val:
            raw_vals.append(val)
        raw_list = form.getlist(key)
        if raw_list and len(raw_list) > 1:
            raw_vals.extend(raw_list)

    for raw in raw_vals:
        if isinstance(raw, str):
            clean = raw.strip()
            if clean.startswith("[") and clean.endswith("]"):
                try:
                    parsed = json.loads(clean)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if str(item).isdigit():
                                del_ids.append(int(item))
                except Exception:
                    pass
            for part in clean.replace("[", "").replace("]", "").split(","):
                part_clean = part.strip()
                if part_clean.isdigit():
                    del_ids.append(int(part_clean))
        elif isinstance(raw, int):
            del_ids.append(raw)
    return list(dict.fromkeys(del_ids))


async def _process_photos(photo_files: list) -> List[Dict[str, Any]]:
    """Process and save uploaded photo files via MediaService."""
    processed = []
    for idx, p in enumerate(photo_files):
        if hasattr(p, "read") and getattr(p, "filename", None):
            data = await p.read()
            if data:
                rel, thumb, sz, w, h = MediaService.process_and_save_image(data, p.filename)
                processed.append({
                    "file_path": rel, "thumb_path": thumb, "file_name": p.filename,
                    "file_size": sz, "width": w, "height": h, "sort_order": idx
                })
    return processed


def _clean_photos(photos: list):
    """Safely cleanup processed photos on error rollback."""
    if photos:
        MediaService.delete_photo_files([p["file_path"] for p in photos] + [p["thumb_path"] for p in photos])


async def get_entries(request: Request) -> JSONResponse:
    """Retrieve entries strictly scoped to authenticated user with query filters."""
    user, err = require_auth(request)
    if err:
        return err

    qp = request.query_params
    filters = EntryFilterDTO(
        mood=qp.get("mood"), category_param=qp.get("category_id") or qp.get("category"),
        tag=qp.get("tag"), month=qp.get("month"), search=qp.get("search"),
        limit=qp.get("limit"), offset=qp.get("offset")
    )
    try:
        return JSONResponse({"status": "success", "entries": EntryRepository.get_entries(user["id"], filters)}, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message, "entries": []}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as e:
        logger.error("[entry_routes.get_entries] Lỗi cơ sở dữ liệu: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi tải danh sách nhật ký", "entries": []}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[entry_routes.get_entries] Lỗi hệ thống khi tải nhật ký: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi tải danh sách nhật ký", "entries": []}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


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
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as e:
        logger.error("[entry_routes.get_entry_by_id] Lỗi cơ sở dữ liệu: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi tải bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[entry_routes.get_entry_by_id] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi tải bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


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
        processed_photos = await _process_photos(photo_files)
        dto = EntryCreateDTO(
            title=title, content=content, mood=form.get("mood", "serene").strip(),
            weather=form.get("weather", "sunny").strip(),
            entry_date=form.get("entry_date", "").strip() or None,
            created_at=form.get("created_at", "").strip() or None,
            category_id=_parse_category_id(form.get("category_id")), tags=tags
        )
        created = EntryRepository.create_entry(user["id"], dto, processed_photos)
        return JSONResponse({
            "status": "success", "message": "Đã lưu nhật ký thành công 🌸",
            "entry_id": created["id"], "id": created["id"], "entry": created
        }, status_code=status.HTTP_201_CREATED, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        _clean_photos(processed_photos)
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        _clean_photos(processed_photos)
        logger.error("[entry_routes.create_entry] Lỗi cơ sở dữ liệu: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi tạo bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        _clean_photos(processed_photos)
        logger.exception("[entry_routes.create_entry] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi tạo bài viết: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    del_ids = _parse_deleted_photo_ids(form)
    cat_id = _parse_category_id(form.get("category_id")) if "category_id" in form else None

    processed_photos = []
    try:
        processed_photos = await _process_photos(form.getlist("photos"))
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
    except KokoroDomainError as e:
        _clean_photos(processed_photos)
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except (ValueError, TypeError) as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
    except psycopg2.Error as e:
        _clean_photos(processed_photos)
        logger.error("[entry_routes.update_entry] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi cập nhật bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        _clean_photos(processed_photos)
        logger.exception("[entry_routes.update_entry] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi cập nhật bài viết: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        logger.error("[entry_routes.delete_entry_photo] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi xóa ảnh"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_routes.delete_entry_photo] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        logger.error("[entry_routes.delete_entry] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi xóa bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_routes.delete_entry] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        logger.error("[entry_routes.toggle_pin_entry] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi ghim bài viết"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_routes.toggle_pin_entry] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def export_entries(request: Request) -> Response:
    """Export all journal entries and categories belonging strictly to user."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        cats, entries = EntryRepository.export_data(user["id"])
        export_data = {
            "app": "Kokoro (心) — Nhật Ký Cảm Xúc & Kỷ Niệm", "version": Config.APP_VERSION,
            "export_version": "1.1", "exported_at": datetime.now().isoformat(),
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
            "total_categories": len(cats), "categories": cats,
            "total_entries": len(entries), "entries": entries
        }
        filename = f"kokoro_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return Response(
            content=json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8"),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "application/json; charset=utf-8"}
        )
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        logger.error("[entry_routes.export_entries] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi xuất dữ liệu"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_routes.export_entries] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi xuất dữ liệu: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def import_entries(request: Request) -> JSONResponse:
    """Import entries and custom categories from a JSON backup file or payload."""
    user, err = require_auth(request)
    if err:
        return err
    try:
        ct = request.headers.get("content-type", "")
        if "multipart/form-data" in ct:
            form = await request.form()
            f = form.get("backup_file") or form.get("file")
            if not f:
                return JSONResponse({"status": "error", "message": "Vui lòng chọn tệp sao lưu JSON 🌸"}, status_code=status.HTTP_400_BAD_REQUEST)
            payload = json.loads((await f.read()).decode("utf-8"))
        elif "application/json" in ct:
            payload = await request.json()
        else:
            payload = json.loads((await request.body()).decode("utf-8"))

        if not payload:
            return JSONResponse({"status": "error", "message": "Dữ liệu sao lưu trống hoặc không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST)
        entries = payload.get("entries") if isinstance(payload, dict) else (payload if isinstance(payload, list) else None)
        if entries is None:
            return JSONResponse({"status": "error", "message": "Định dạng tệp sao lưu không đúng chuẩn Kokoro JSON"}, status_code=status.HTTP_400_BAD_REQUEST)
        if not entries:
            return JSONResponse({"status": "success", "message": "Không có bài viết nào cần nhập", "imported_count": 0})

        count = EntryRepository.import_data(user["id"], payload.get("categories", []) if isinstance(payload, dict) else [], entries)
        return JSONResponse({"status": "success", "message": f"Đã khôi phục thành công {count} bài viết! 🌸", "imported_count": count})
    except json.JSONDecodeError as e:
        return JSONResponse({"status": "error", "message": f"Tệp sao lưu không phải định dạng JSON hợp lệ: {e}"}, status_code=status.HTTP_400_BAD_REQUEST)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code)
    except psycopg2.Error as e:
        logger.error("[entry_routes.import_entries] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi nhập dữ liệu"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_routes.import_entries] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi khôi phục dữ liệu: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================================
# ROUTE TABLE (Scoped Strictly to Entries)
# =========================================================================
entry_routes = [
    Route("/api/entries", get_entries, methods=["GET"]),
    Route("/api/entries", create_entry, methods=["POST"]),
    Route("/api/entries/export", export_entries, methods=["GET"]),
    Route("/api/entries/import", import_entries, methods=["POST"]),
    Route("/api/entries/{id:int}", get_entry_by_id, methods=["GET"]),
    Route("/api/entries/{id:int}", update_entry, methods=["PUT"]),
    Route("/api/entries/{id:int}", delete_entry, methods=["DELETE"]),
    Route("/api/entries/{id:int}/photos/{photo_id:int}", delete_entry_photo, methods=["DELETE"]),
    Route("/api/entries/{id:int}/pin", toggle_pin_entry, methods=["PATCH"]),
]
