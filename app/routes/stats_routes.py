"""
Kokoro (心) Statistics & Analytics Routes
Dedicated modular router for summary analytics operations.
Complies with AGENTS.md Modular Layered Architecture (avoids bloating entry_routes.py).
"""

from typing import List
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.auth import get_current_user
from app.repositories.stats_repository import StatsRepository


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
            "message": "Vui lòng đăng nhập để xem số liệu thống kê 🌸",
            "authenticated": False
        }, status_code=401, headers=NO_CACHE_HEADERS)
    return user, None


async def get_stats(request: Request) -> JSONResponse:
    """GET /api/stats/summary: Calculate summary statistics strictly scoped to user."""
    user, err_resp = require_auth(request)
    if err_resp:
        return err_resp

    try:
        stats_dto = StatsRepository.get_stats_summary(user["id"])
        return JSONResponse(stats_dto.to_dict(), headers=NO_CACHE_HEADERS)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500, headers=NO_CACHE_HEADERS)


stats_routes: List[Route] = [
    Route("/api/stats/summary", get_stats, methods=["GET"]),
]
