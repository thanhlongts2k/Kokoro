"""
Kokoro (心) Entry Controller Helpers
Auxiliary helpers for entry_routes: form parsing, photo uploads processing, and backup import/export.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import psycopg2
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import Config
from app.services.media_service import MediaService
from app.repositories.entry_repository import EntryRepository
from app.exceptions import KokoroDomainError

logger = logging.getLogger("kokoro.routes.entry_helpers")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}


def handle_route_exception(e: Exception, action: str) -> JSONResponse:
    """Centralized exception handler mapping domain, DB, and unexpected errors to JSONResponse."""
    if isinstance(e, KokoroDomainError):
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    if isinstance(e, psycopg2.Error):
        logger.error("[entry_routes.%s] Lỗi DB: %s", action, e)
        return JSONResponse({"status": "error", "message": f"Lỗi cơ sở dữ liệu khi {action}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    logger.exception("[entry_routes.%s] Lỗi hệ thống: %s", action, e)
    return JSONResponse({"status": "error", "message": f"Lỗi hệ thống khi {action}: {str(e)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


def parse_category_id(val: Any) -> Optional[int]:
    """Safely convert form category parameter to integer or None."""
    if not val or str(val).strip().lower() in ("null", "none"):
        return None
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def parse_deleted_photo_ids(form) -> List[int]:
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


async def process_photos(photo_files: list) -> List[Dict[str, Any]]:
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


def clean_photos(photos: list):
    """Safely cleanup processed photos on error rollback."""
    if photos:
        MediaService.delete_photo_files([p["file_path"] for p in photos] + [p["thumb_path"] for p in photos])


async def export_entries(request: Request) -> Response:
    """Export all journal entries and categories belonging strictly to user."""
    from app.routes.entry_routes import require_auth
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
        logger.error("[entry_helpers.export_entries] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi xuất dữ liệu"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_helpers.export_entries] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi xuất dữ liệu: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def import_entries(request: Request) -> JSONResponse:
    """Import entries and custom categories from a JSON backup file or payload."""
    from app.routes.entry_routes import require_auth
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
        logger.error("[entry_helpers.import_entries] Lỗi DB: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi nhập dữ liệu"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception("[entry_helpers.import_entries] Lỗi hệ thống: %s", e)
        return JSONResponse({"status": "error", "message": f"Lỗi khôi phục dữ liệu: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
