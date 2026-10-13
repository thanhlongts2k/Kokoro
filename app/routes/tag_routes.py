"""
Kokoro (心) Tag Management Routes
Dedicated modular router for tags CRUD and orphan cleanup operations.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

import json
import logging
from typing import List
import psycopg2
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.auth import get_current_user
from app.repositories.tag_repository import TagRepository
from app.exceptions import KokoroDomainError, TagNotFoundError, InvalidInputError

logger = logging.getLogger("kokoro.routes.tag")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}


def require_auth(request: Request):
    """Helper to check current user or return 401 error response."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error",
            "message": "Vui lòng đăng nhập để xem và quản lý thẻ 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)
    return user, None


async def get_tags(request: Request) -> JSONResponse:
    """GET /api/tags: Retrieve tags strictly scoped to authenticated user with usage counts."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        tags = TagRepository.get_tags(user["id"])
        return JSONResponse({
            "status": "success",
            "tags": [t.to_dict() for t in tags]
        }, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as err:
        logger.error("[tag_routes.get_tags] Lỗi cơ sở dữ liệu: %s", err)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi tải danh sách thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[tag_routes.get_tags] Lỗi không xác định khi tải danh sách thẻ: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi tải danh sách thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def create_tag(request: Request) -> JSONResponse:
    """POST /api/tags: Proactively create a new tag for the authenticated user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError, TypeError):
        data = {}

    raw_name = (data.get("name") or "").strip()
    if not raw_name:
        return JSONResponse({"status": "error", "message": "Tên thẻ không được để trống 🏷️"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    clean_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"
    clean_name = "#" + clean_name.lstrip("#").strip()
    if clean_name == "#":
        return JSONResponse({"status": "error", "message": "Tên thẻ không hợp lệ 🏷️"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    try:
        tag = TagRepository.create_tag(user["id"], clean_name)
        return JSONResponse({
            "status": "success",
            "message": f"Đã tạo thẻ {clean_name} thành công 🏷️",
            "tag": tag.to_dict()
        }, status_code=status.HTTP_201_CREATED, headers=NO_CACHE_HEADERS)
    except InvalidInputError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as err:
        logger.error("[tag_routes.create_tag] Lỗi cơ sở dữ liệu: %s", err)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi tạo thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[tag_routes.create_tag] Lỗi không xác định khi tạo thẻ: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi tạo thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def update_tag(request: Request) -> JSONResponse:
    """PUT /api/tags/{id:int}: Rename an existing tag (merges if target name exists)."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    tag_id = request.path_params.get("id")
    try:
        tag_id = int(tag_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError, TypeError):
        data = {}

    raw_name = data.get("name", "").strip()
    if not raw_name:
        return JSONResponse({"status": "error", "message": "Tên thẻ không được để trống."}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    new_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"

    try:
        result = TagRepository.rename_or_merge_tag(user["id"], tag_id, new_name)
        if not result:
            return JSONResponse({"status": "error", "message": "Không tìm thấy thẻ chủ đề."}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)

        final_id, final_name = result
        return JSONResponse({
            "status": "success",
            "message": "Đã đổi tên thẻ chủ đề thành công.",
            "tag": {"id": final_id, "name": final_name}
        }, headers=NO_CACHE_HEADERS)
    except TagNotFoundError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)
    except InvalidInputError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as err:
        logger.error("[tag_routes.update_tag] Lỗi cơ sở dữ liệu: %s", err)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi cập nhật thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[tag_routes.update_tag] Lỗi không xác định khi cập nhật thẻ: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi cập nhật thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def delete_tag(request: Request) -> JSONResponse:
    """DELETE /api/tags/{id:int}: Delete a tag and its associations."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    tag_id = request.path_params.get("id")
    try:
        tag_id = int(tag_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    try:
        success = TagRepository.delete_tag(user["id"], tag_id)
        if not success:
            return JSONResponse({"status": "error", "message": "Không tìm thấy thẻ chủ đề."}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)

        return JSONResponse({
            "status": "success",
            "message": "Đã xóa thẻ chủ đề thành công."
        }, headers=NO_CACHE_HEADERS)
    except TagNotFoundError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as err:
        logger.error("[tag_routes.delete_tag] Lỗi cơ sở dữ liệu: %s", err)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi xóa thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[tag_routes.delete_tag] Lỗi không xác định khi xóa thẻ: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi xóa thẻ"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def cleanup_orphan_tags(request: Request) -> JSONResponse:
    """DELETE /api/tags/cleanup-orphans: Remove all tags with 0 associations for user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        deleted_count = TagRepository.cleanup_orphan_tags(user["id"])
        return JSONResponse({
            "status": "success",
            "message": f"Đã dọn dẹp {deleted_count} thẻ chủ đề mồ côi.",
            "deleted_count": deleted_count
        }, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except psycopg2.Error as err:
        logger.error("[tag_routes.cleanup_orphan_tags] Lỗi cơ sở dữ liệu: %s", err)
        return JSONResponse({"status": "error", "message": "Lỗi cơ sở dữ liệu khi dọn dẹp thẻ mồ côi"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[tag_routes.cleanup_orphan_tags] Lỗi không xác định khi dọn dẹp thẻ mồ côi: %s", e)
        return JSONResponse({"status": "error", "message": "Lỗi hệ thống khi dọn dẹp thẻ mồ côi"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


tag_routes: List[Route] = [
    Route("/api/tags", get_tags, methods=["GET"]),
    Route("/api/tags", create_tag, methods=["POST"]),
    Route("/api/tags/cleanup-orphans", cleanup_orphan_tags, methods=["DELETE"]),
    Route("/api/tags/{id:int}", update_tag, methods=["PUT"]),
    Route("/api/tags/{id:int}", delete_tag, methods=["DELETE"]),
]
