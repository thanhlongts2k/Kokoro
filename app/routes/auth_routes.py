"""
Authentication Endpoints for Kokoro (心)
Endpoints:
- GET  /api/auth/config      (Client GIS initialization configuration)
- GET  /api/auth/me          (Current session user)
- GET  /api/auth/mock-users  (List mock accounts for easy dev switching)
- POST /api/auth/mock-login  (Dev 1-click login)
- POST /api/auth/google      (Google Identity Services credential verification)
- POST /api/auth/logout      (Clear session cookie)
"""

import logging
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger("kokoro.auth")

from app.config import Config
from app.database import get_cursor
from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_DURATION_SECONDS,
    create_session_token,
    get_current_user,
    get_user_by_id,
    upsert_user,
    verify_google_id_token
)

async def auth_config(request: Request) -> JSONResponse:
    """Return public auth settings for client GIS and UI initialization."""
    return JSONResponse({
        "status": "success",
        "version": Config.APP_VERSION,
        "google_client_id": Config.GOOGLE_CLIENT_ID,
        "mock_auth": Config.MOCK_AUTH
    })

async def auth_me(request: Request) -> JSONResponse:
    """Return currently authenticated user from session or Bearer token."""
    user = get_current_user(request)
    if user:
        return JSONResponse({"status": "success", "authenticated": True, "user": user})
    return JSONResponse({"status": "unauthenticated", "authenticated": False, "user": None})

async def list_mock_users(request: Request) -> JSONResponse:
    """List available development users for quick switching."""
    if not Config.MOCK_AUTH:
        return JSONResponse({"status": "error", "message": "Mock auth disabled in production"}, status_code=403)

    with get_cursor() as cur:
        cur.execute("SELECT id, google_id, email, name, avatar_url FROM users ORDER BY id ASC;")
        users = [dict(r) for r in cur.fetchall()]

    return JSONResponse({"status": "success", "users": users})

async def mock_login(request: Request) -> JSONResponse:
    """Development quick login as a selected user."""
    if not Config.MOCK_AUTH:
        return JSONResponse({"status": "error", "message": "Mock auth disabled in production"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        body = {}

    user_id = body.get("user_id")
    if not user_id:
        # Default to first user in database
        with get_cursor() as cur:
            cur.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1;")
            row = cur.fetchone()
            user_id = row["id"] if row else 1

    user = get_user_by_id(int(user_id))
    if not user:
        return JSONResponse({"status": "error", "message": f"Không tìm thấy user id {user_id}"}, status_code=404)

    token = create_session_token(user["id"], user["email"], user["name"])

    response = JSONResponse({
        "status": "success",
        "message": f"Đăng nhập thành công với tài khoản {user['name']} 🌸",
        "user": user,
        "token": token
    })

    # Set persistent HttpOnly session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        samesite="lax",
        path="/"
    )
    return response

async def google_login(request: Request) -> JSONResponse:
    """Verify Google Identity Services credential and establish session."""
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Invalid JSON: {e}"}, status_code=400)

    credential = body.get("credential")
    if not credential:
        return JSONResponse({"status": "error", "message": "Thiếu mã xác thực Google credential"}, status_code=400)

    try:
        id_info = verify_google_id_token(credential)
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Xác thực Google ID Token thất bại: {e}"}, status_code=401)

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name") or email
    avatar_url = id_info.get("picture")

    if not google_id or not email:
        return JSONResponse({"status": "error", "message": "Google Token không chứa email hoặc sub"}, status_code=400)

    # Upsert user in PostgreSQL & create session token
    try:
        user = upsert_user(google_id, email, name, avatar_url)
        token = create_session_token(user["id"], user["email"], user["name"])
    except Exception as e:
        logger.error(f"[Auth] Lỗi lưu người dùng Google vào PostgreSQL: {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": f"Không thể lưu thông tin tài khoản: {e}"}, status_code=500)

    response = JSONResponse({
        "status": "success",
        "message": f"Chào mừng {user['name']} đến với Kokoro! 🌸",
        "user": user,
        "token": token
    })

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        samesite="lax",
        path="/"
    )
    return response

async def logout(request: Request) -> JSONResponse:
    """Log out current user by clearing session cookie."""
    response = JSONResponse({"status": "success", "message": "Đã đăng xuất khỏi Kokoro 🌸"})
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return response

auth_routes = [
    Route("/api/auth/config", auth_config, methods=["GET"]),
    Route("/api/auth/me", auth_me, methods=["GET"]),
    Route("/api/auth/mock-users", list_mock_users, methods=["GET"]),
    Route("/api/auth/mock-login", mock_login, methods=["POST"]),
    Route("/api/auth/google", google_login, methods=["POST"]),
    Route("/api/auth/logout", logout, methods=["POST"]),
]
