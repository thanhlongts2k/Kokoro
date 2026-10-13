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
        "version": Config.APP_VERSION,
        "theme": "Soft Sakura Pastel / Healing Light Frosted Glass",
        "port": Config.PORT,
        "database": f"PostgreSQL 18 ({db_status})",
        "mock_auth": Config.MOCK_AUTH
    })

from app.routes.entry_routes import entry_routes
from app.routes.category_routes import category_routes
from app.routes.tag_routes import tag_routes
from app.routes.stats_routes import stats_routes
from app.routes.auth_routes import auth_routes
from app.routes.maintenance_routes import maintenance_routes

# --------------------------------------------------------------------------
# APPLICATION ROUTING & STATIC CACHE OPTIMIZATION
# --------------------------------------------------------------------------

class ImmutableStaticFiles(StaticFiles):
    """Serve uploaded media with aggressive immutable caching."""
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

class AppStaticFiles(StaticFiles):
    """Serve app shell and static frontend assets with smart caching."""
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            norm_path = path.replace("\\", "/").lower()
            if norm_path.endswith(".html") or norm_path in ("", ".", "/", "index.html") or "index.html" in norm_path:
                response.headers["Cache-Control"] = "no-cache, must-revalidate"
            else:
                response.headers["Cache-Control"] = "public, max-age=86400"
        return response

routes = [
    Route("/api/health", api_health, methods=["GET"]),
    *auth_routes,
    *category_routes,
    *tag_routes,
    *stats_routes,
    *entry_routes,
    *maintenance_routes,
    Mount("/uploads", ImmutableStaticFiles(directory=str(UPLOAD_DIR)), name="uploads"),
    Mount("/", AppStaticFiles(directory=str(STATIC_DIR), html=True), name="static"),
]

# --------------------------------------------------------------------------
# PROXY & CORS MIDDLEWARE
# --------------------------------------------------------------------------

class ProxyHeadersMiddleware:
    """
    Handle reverse proxy headers from Nginx:
    - X-Forwarded-Proto: updates scheme (http -> https)
    - X-Forwarded-Prefix: handles subpaths (e.g. /kokoro)
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            proto = headers.get(b"x-forwarded-proto")
            if proto:
                scope["scheme"] = proto.decode("latin1")
            prefix = headers.get(b"x-forwarded-prefix")
            if prefix:
                scope["root_path"] = prefix.decode("latin1").rstrip("/")
        await self.app(scope, receive, send)

middleware = [
    Middleware(ProxyHeadersMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
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
        reload=Config.DEBUG,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="info"
    )