"""
Authentication Endpoints for Kokoro (心)
Endpoints:
- GET  /api/auth/config      (Client GIS initialization configuration)
- GET  /api/auth/me          (Current session user)
- GET  /api/auth/mock-users  (List mock accounts for easy dev switching)
- POST /api/auth/mock-login  (Dev 1-click login)
- POST /api/auth/google      (Google Identity Services credential verification)
- POST /api/auth/logout      (Clear session cookie)
Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
"""

import os
import json
import logging
import psycopg2
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logger = logging.getLogger("kokoro.auth")

from app.config import Config
from app.repositories.user_repository import UserRepository
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
        user_dict = user.to_dict() if hasattr(user, "to_dict") else user
        return JSONResponse({"status": "success", "authenticated": True, "user": user_dict})
    return JSONResponse({"status": "unauthenticated", "authenticated": False, "user": None})

async def list_mock_users(request: Request) -> JSONResponse:
    """List available development users for quick switching."""
    if not Config.MOCK_AUTH:
        return JSONResponse({"status": "error", "message": "Mock auth disabled in production"}, status_code=status.HTTP_403_FORBIDDEN)

    users = [u.to_dict() for u in UserRepository.list_mock_users()]
    return JSONResponse({"status": "success", "users": users})

async def mock_login(request: Request) -> JSONResponse:
    """Development quick login as a selected user."""
    if not Config.MOCK_AUTH:
        return JSONResponse({"status": "error", "message": "Mock auth disabled in production"}, status_code=status.HTTP_403_FORBIDDEN)

    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError, TypeError):
        body = {}

    user_id = body.get("user_id")
    if not user_id:
        mock_users = UserRepository.list_mock_users()
        if not mock_users:
            return JSONResponse({"status": "error", "message": "Không có tài khoản mock khả dụng"}, status_code=status.HTTP_404_NOT_FOUND)
        user = mock_users[0]
    else:
        user = get_user_by_id(int(user_id))

    if not user:
        return JSONResponse({"status": "error", "message": f"Không tìm thấy user id {user_id}"}, status_code=status.HTTP_404_NOT_FOUND)

    # Privacy Guard: ONLY allow mock logins into mock accounts, NEVER real user accounts
    user_google_id = user.google_id if hasattr(user, "google_id") else user.get("google_id", "")
    user_email = user.email if hasattr(user, "email") else user.get("email", "")
    if not (str(user_google_id).startswith("mock_") or str(user_email).endswith("@kokoro.me")):
        logger.warning("[Auth.mock_login] Chặn truy cập trái phép vào tài khoản thật qua mock: user_id=%s, email=%s", user_id, user_email)
        return JSONResponse({"status": "error", "message": "Tài khoản cá nhân không thể đăng nhập qua mock switcher 🌸"}, status_code=status.HTTP_403_FORBIDDEN)

    token = create_session_token(user["id"], user["email"], user["name"])

    response = JSONResponse({
        "status": "success",
        "message": f"Đăng nhập thành công với tài khoản {user['name']} 🌸",
        "user": user.to_dict() if hasattr(user, "to_dict") else user,
        "token": token
    })

    is_secure = os.getenv("COOKIE_SECURE", "").lower() in ("true", "1") or (request.url.scheme == "https") or (request.headers.get("x-forwarded-proto") == "https")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/"
    )
    return response

async def google_login(request: Request) -> JSONResponse:
    """Verify Google Identity Services credential and establish session."""
    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("[Auth.google_login] Lỗi phân tích JSON: %s", e)
        return JSONResponse({"status": "error", "message": f"Invalid JSON: {e}"}, status_code=status.HTTP_400_BAD_REQUEST)

    credential = body.get("credential")
    if not credential:
        return JSONResponse({"status": "error", "message": "Thiếu mã xác thực Google credential"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        id_info = verify_google_id_token(credential)
    except ValueError as e:
        logger.warning("[Auth.google_login] Xác thực Google ID Token thất bại: %s", e)
        return JSONResponse({"status": "error", "message": f"Xác thực Google ID Token thất bại: {e}"}, status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logger.exception("[Auth.google_login] Lỗi không xác định khi xác thực Google ID: %s", e)
        return JSONResponse({"status": "error", "message": f"Xác thực Google ID Token thất bại: {e}"}, status_code=status.HTTP_401_UNAUTHORIZED)

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name") or email
    avatar_url = id_info.get("picture")

    if not google_id or not email:
        return JSONResponse({"status": "error", "message": "Google Token không chứa email hoặc sub"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        user = upsert_user(google_id, email, name, avatar_url)
        token = create_session_token(user["id"], user["email"], user["name"])
    except psycopg2.Error as e:
        logger.error(f"[Auth] Lỗi lưu người dùng Google vào PostgreSQL (psycopg2): {e}", exc_info=True)
        return JSONResponse({"status": "error", "message": f"Không thể lưu thông tin tài khoản: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f"[Auth] Lỗi lưu người dùng Google vào PostgreSQL: {e}")
        return JSONResponse({"status": "error", "message": f"Không thể lưu thông tin tài khoản: {e}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response = JSONResponse({
        "status": "success",
        "message": f"Chào mừng {user['name']} đến với Kokoro! 🌸",
        "user": user.to_dict() if hasattr(user, "to_dict") else user,
        "token": token
    })

    is_secure = os.getenv("COOKIE_SECURE", "").lower() in ("true", "1") or (request.url.scheme == "https") or (request.headers.get("x-forwarded-proto") == "https")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=is_secure,
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
