"""
Authentication & Authorization Module for Kokoro (心)
Supports:
1. Google Identity Services (GIS) ID Token verification via google-auth
2. JWT-based session tokens with HttpOnly cookies & Bearer headers
3. Mock authentication for local development and test automation
"""

import time
from typing import Optional, Dict, Any
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from starlette.requests import Request

from app.config import Config
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserDTO

SESSION_COOKIE_NAME = "kokoro_session"
JWT_ALGORITHM = "HS256"
SESSION_DURATION_SECONDS = 30 * 24 * 3600  # 30 days

def create_session_token(user_id: int, email: str, name: str) -> str:
    """Generate a signed JWT session token."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "email": email,
        "name": name,
        "iat": now,
        "exp": now + SESSION_DURATION_SECONDS
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify signature and expiration of JWT session token."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def verify_google_id_token(credential: str) -> Dict[str, Any]:
    """
    Verify Google ID Token using google-auth library against Google's public certs.
    Returns decoded token dictionary containing 'sub', 'email', 'name', 'picture'.
    """
    req = google_requests.Request()
    if not Config.GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID chưa được cấu hình trong .env.")
    
    # Verify signature and audience
    decoded_info = id_token.verify_oauth2_token(credential, req, Config.GOOGLE_CLIENT_ID)
    return decoded_info

def upsert_user(google_id: str, email: str, name: str, avatar_url: Optional[str] = None) -> UserDTO:
    """Insert or update user details via UserRepository."""
    return UserRepository.upsert_user(google_id, email, name, avatar_url)

def get_user_by_id(user_id: int) -> Optional[UserDTO]:
    """Retrieve full user profile via UserRepository."""
    return UserRepository.get_by_id(user_id)

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract and authenticate current user from Request.
    Precedence:
    1. HttpOnly Cookie: `kokoro_session`
    2. Authorization Header: `Bearer <token>`
    3. Dev Mock User Header: `X-Mock-User-Id` (when MOCK_AUTH=True)
    """
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()

    if not token:
        token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        payload = verify_session_token(token)
        if payload and "sub" in payload:
            user_id = int(payload["sub"])
            user = get_user_by_id(user_id)
            if user:
                return user

    # Development fallback: Header X-Mock-User-Id
    if Config.MOCK_AUTH:
        mock_id_header = request.headers.get("X-Mock-User-Id")
        if mock_id_header:
            try:
                user = get_user_by_id(int(mock_id_header))
                if user:
                    return user
            except (ValueError, TypeError):
                pass

    return None
