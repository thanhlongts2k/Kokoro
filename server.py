import json
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app.config import Config
from app.database import init_db, get_cursor

# Ensure database tables exist on startup
try:
    init_db()
except Exception as e:
    print(f"[Kokoro Server] Warning: Database auto-init error: {e}")

# Base static and upload directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Config.UPLOAD_DIR

# --------------------------------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------------------------------

async def api_health(request):
    """Healthcheck endpoint verifying DB and Server status."""
    db_status = "connected"
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1;")
    except Exception as e:
        db_status = f"error: {e}"

    return JSONResponse({
        "status": "online",
        "app": "Kokoro (心) PWA Journal",
        "theme": "Soft Sakura Pastel / Healing Light Frosted Glass",
        "port": Config.PORT,
        "database": f"PostgreSQL 18 ({db_status})",
        "mock_auth": Config.MOCK_AUTH
    })

async def api_current_user(request):
    """Return currently active user profile (Mock user in dev)."""
    with get_cursor() as cur:
        cur.execute("SELECT id, name, email, avatar_url, created_at FROM users LIMIT 1;")
        user = cur.fetchone()

    if user:
        # Convert created_at to ISO string
        if user.get("created_at"):
            user["created_at"] = user["created_at"].isoformat()
        return JSONResponse({"user": user})

    return JSONResponse({
        "user": {
            "id": 1,
            "name": "Aria Tanaka",
            "email": "aria.tanaka@kokoro.me",
            "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
        }
    })

from app.routes.entry_routes import entry_routes

# --------------------------------------------------------------------------
# APPLICATION ROUTING & MIDDLEWARE
# --------------------------------------------------------------------------

routes = [
    Route("/api/health", api_health, methods=["GET"]),
    Route("/api/auth/me", api_current_user, methods=["GET"]),
    *entry_routes,
    Mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads"),
    Mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static"),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=Config.DEBUG, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(f"[Kokoro] Khoi dong may chu PWA Soft Sakura tai http://0.0.0.0:{Config.PORT}")
    print(f"[Kokoro] Truy cap tai: http://localhost:{Config.PORT}")
    uvicorn.run(
        "server:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        log_level="info"
    )