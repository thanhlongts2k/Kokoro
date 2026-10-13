"""
Kokoro (心) Category & Mood Taxonomy Routes
Dedicated modular router for categories CRUD operations.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

from typing import List
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.auth import get_current_user
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreateDTO, CategoryUpdateDTO
from app.exceptions import KokoroDomainError, CategoryNotFoundError, CategoryDuplicateError, InvalidInputError

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
            "message": "Vui lòng đăng nhập để xem và quản lý danh mục 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)
    return user, None


async def get_categories(request: Request) -> JSONResponse:
    """GET /api/categories: Retrieve all categories for current user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        categories = CategoryRepository.get_categories(user["id"])
        return JSONResponse({
            "status": "success",
            "categories": [c.to_dict() for c in categories]
        }, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def create_category(request: Request) -> JSONResponse:
    """POST /api/categories: Create a new category."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        data = await request.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip()
    if not name:
        return JSONResponse({"status": "error", "message": "Tên danh mục không được để trống 🌸"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    icon = (data.get("icon") or "📁").strip() or "📁"
    color = (data.get("color") or "#ec4899").strip() or "#ec4899"

    user_id = user["id"]
    try:
        if CategoryRepository.check_duplicate_name(user_id, name):
            return JSONResponse({"status": "error", "message": f"Danh mục '{name}' đã tồn tại."}, status_code=status.HTTP_409_CONFLICT, headers=NO_CACHE_HEADERS)

        dto = CategoryCreateDTO(name=name, icon=icon, color=color)
        category = CategoryRepository.create_category(user_id, dto)

        return JSONResponse({
            "status": "success",
            "message": "Đã tạo danh mục thành công 🌸",
            "category": category.to_dict()
        }, status_code=status.HTTP_201_CREATED, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def update_category(request: Request) -> JSONResponse:
    """PUT /api/categories/{id:int}: Update an existing category."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    cat_id = request.path_params.get("id")
    try:
        cat_id = int(cat_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    try:
        data = await request.json()
    except Exception:
        data = {}

    name = data.get("name")
    if name is not None:
        name = name.strip()
        if not name:
            return JSONResponse({"status": "error", "message": "Tên danh mục không được để trống 🌸"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    icon = data.get("icon")
    if icon is not None:
        icon = icon.strip() or "📁"

    color = data.get("color")
    if color is not None:
        color = color.strip() or "#ec4899"

    sort_order = data.get("sort_order")
    if sort_order is not None:
        try:
            sort_order = int(sort_order)
        except (ValueError, TypeError):
            sort_order = None

    try:
        existing = CategoryRepository.get_by_id(cat_id, user_id)
        if not existing:
            return JSONResponse({"status": "error", "message": "Không tìm thấy danh mục hoặc bạn không có quyền sửa."}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)

        if name and name.lower() != existing.name.lower():
            if CategoryRepository.check_duplicate_name(user_id, name, exclude_id=cat_id):
                return JSONResponse({"status": "error", "message": f"Danh mục '{name}' đã tồn tại."}, status_code=status.HTTP_409_CONFLICT, headers=NO_CACHE_HEADERS)

        dto = CategoryUpdateDTO(name=name, icon=icon, color=color, sort_order=sort_order)
        updated = CategoryRepository.update_category(user_id, cat_id, dto, old_name=existing.name)

        return JSONResponse({
            "status": "success",
            "message": "Đã cập nhật danh mục thành công 🌸",
            "category": updated.to_dict()
        }, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


async def delete_category(request: Request) -> JSONResponse:
    """DELETE /api/categories/{id:int}: Delete a category and preserve entries."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    cat_id = request.path_params.get("id")
    try:
        cat_id = int(cat_id)
    except (ValueError, TypeError):
        return JSONResponse({"status": "error", "message": "ID không hợp lệ"}, status_code=status.HTTP_400_BAD_REQUEST, headers=NO_CACHE_HEADERS)

    try:
        deleted_name = CategoryRepository.delete_category(user_id, cat_id)
        if not deleted_name:
            return JSONResponse({"status": "error", "message": "Không tìm thấy danh mục để xóa."}, status_code=status.HTTP_404_NOT_FOUND, headers=NO_CACHE_HEADERS)

        return JSONResponse({
            "status": "success",
            "message": f"Đã xóa danh mục '{deleted_name}' thành công 🌸"
        }, headers=NO_CACHE_HEADERS)
    except KokoroDomainError as e:
        return JSONResponse({"status": "error", "message": e.message}, status_code=e.status_code, headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


category_routes: List[Route] = [
    Route("/api/categories", get_categories, methods=["GET"]),
    Route("/api/categories", create_category, methods=["POST"]),
    Route("/api/categories/{id:int}", update_category, methods=["PUT"]),
    Route("/api/categories/{id:int}", delete_category, methods=["DELETE"]),
]
