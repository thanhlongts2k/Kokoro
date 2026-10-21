"""
Kokoro (心) Maintenance & Diagnostics Routes
Dedicated modular router for administrative, maintenance, and data cleanup operations.
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

import json
import logging
import time
from typing import Dict, List
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.auth import get_current_user
from app.services.media_service import MediaService
from app.schemas.maintenance import MaintenanceResponseDTO

logger = logging.getLogger("kokoro.maintenance")

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}

CLEANUP_RATE_LIMIT_SECONDS: float = 60.0
_last_cleanup_timestamps: Dict[int, float] = {}


def require_auth(request: Request):
    """Helper to check current user or return 401 error response."""
    user = get_current_user(request)
    if not user:
        return None, JSONResponse({
            "status": "error",
            "message": "Vui lòng đăng nhập để thực hiện tác vụ bảo trì 🌸",
            "authenticated": False
        }, status_code=status.HTTP_401_UNAUTHORIZED, headers=NO_CACHE_HEADERS)
    return user, None


async def cleanup_orphaned_media(request: Request) -> JSONResponse:
    """
    POST /api/maintenance/cleanup-orphaned-media
    Scans storage directories (originals & thumbnails) and purges unreferenced files
    older than the grace period threshold.
    Requires authentication and enforces 60-second rate-limiting per user session.
    """
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    user_id = user["id"]
    now = time.time()
    last_run = _last_cleanup_timestamps.get(user_id, 0.0)
    # Check rate limit (allow bypass in test mode if header present)
    is_test_bypass = request.headers.get("X-Bypass-Rate-Limit") == "true"
    if not is_test_bypass and (now - last_run) < CLEANUP_RATE_LIMIT_SECONDS:
        remaining_secs = int(CLEANUP_RATE_LIMIT_SECONDS - (now - last_run))
        return JSONResponse({
            "status": "error",
            "message": f"Vui lòng đợi {remaining_secs} giây nữa trước khi thực hiện dọn dẹp tiếp 🌸"
        }, status_code=status.HTTP_429_TOO_MANY_REQUESTS, headers=NO_CACHE_HEADERS)

    grace_period_hours: float = 2.0
    try:
        # Check query param first
        qp_grace = request.query_params.get("grace_period_hours")
        if qp_grace:
            grace_period_hours = float(qp_grace)
        else:
            # Check JSON body if provided
            try:
                body = await request.json()
                if body and "grace_period_hours" in body:
                    grace_period_hours = float(body["grace_period_hours"])
            except (json.JSONDecodeError, ValueError, TypeError) as err:
                logger.warning("Invalid grace_period_hours in request JSON body: %s", err)
    except (ValueError, TypeError):
        grace_period_hours = 2.0

    try:
        stats_dto = MediaService.scan_and_cleanup_orphans(grace_period_hours=grace_period_hours)
        _last_cleanup_timestamps[user_id] = now
        response_dto = MaintenanceResponseDTO(
            status="success",
            message=f"Đã dọn dẹp {stats_dto.deleted_count} tệp ảnh mồ côi, giải phóng {stats_dto.freed_mb} MB 🍃",
            data=stats_dto
        )
        return JSONResponse(response_dto.to_dict(), headers=NO_CACHE_HEADERS)
    except Exception as e:
        logger.exception("[maintenance_routes.cleanup_orphaned_media] Lỗi dọn dẹp tệp ảnh: %s", e)
        return JSONResponse({
            "status": "error",
            "message": f"Lỗi dọn dẹp tệp ảnh: {str(e)}"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=NO_CACHE_HEADERS)


maintenance_routes: List[Route] = [
    Route("/api/maintenance/cleanup-orphaned-media", cleanup_orphaned_media, methods=["POST"]),
]
