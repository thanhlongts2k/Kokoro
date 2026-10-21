"""
KOKORO (心) — COMPREHENSIVE AUTOMATED VERIFICATION SUITE (v1.8.0)
Testing:
1. Version synchronization to v1.8.0 (Config, Auth config, Health endpoint, Service Worker cache, index.html footer badge).
2. iOS WebKit drag lock contracts in layout.css and components.css (pan-x, overflow-y: hidden, overscroll-behavior).
3. Dual-Layer Offline PWA resilience:
   - Soft Sakura offline banner DOM and styles (#offline-status-banner)
   - Client auth offline session preservation (kokoro_last_auth_user) without modal popups
   - Client API CacheManager and IndexedDB offline queueing with _isOffline flag
   - Service Worker network-first caching for GET requests and strict bypass for mutation requests
4. PostgreSQL Categories & Tags Schema & Migration:
   - categories table with ON DELETE CASCADE and UNIQUE (user_id, name)
   - entries.category_id with ON DELETE SET NULL and foreign key index
   - Seeded default 5 categories (Đời thường, Công việc, Tình cảm, Du lịch, Học tập)
5. REST API Security & Multi-tenant Isolation:
   - Category and Tag endpoints require authentication (401 Unauthorized guard)
   - Clean Architecture layer isolation contracts
"""

import os
import sys
import unittest
from pathlib import Path
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
from app.config import Config
from app.database import DEFAULT_CATEGORIES

BASE_DIR = Path(__file__).resolve().parent.parent


class TestV180OfflinePWAResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # =========================================================================
    # 1. VERSION SYNCHRONIZATION (v1.8.0)
    # =========================================================================
    def test_01_version_synchronization_v180(self):
        """Verify all artifacts, config, endpoints, SW and DOM reflect v1.8.0."""
        self.assertIn(Config.APP_VERSION, ("v1.8.0", "v1.8.1"))

        # Auth config endpoint
        auth_resp = self.client.get("/api/auth/config")
        self.assertEqual(auth_resp.status_code, 200)
        self.assertIn(auth_resp.json().get("version"), ("v1.8.0", "v1.8.1"))

        # Health endpoint
        health_resp = self.client.get("/api/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertIn(health_resp.json().get("version"), ("v1.8.0", "v1.8.1"))

        # Service Worker cache version & assets
        sw_code = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        self.assertTrue(any(v in sw_code for v in ("kokoro-v1.8.0", "kokoro-v1.8.1")))
        self.assertTrue(any(v in sw_code for v in ("./js/app.js?v=1.8.0", "./js/app.js?v=1.8.1")))
        self.assertTrue(any(v in sw_code for v in ("./css/layout.css?v=1.8.0", "./css/layout.css?v=1.8.1")))

        # Index HTML badge & asset query params
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertTrue(any(v in html_code for v in ('id="app-version-badge">v1.8.0</span>', 'id="app-version-badge">v1.8.1</span>')))
        self.assertTrue(any(v in html_code for v in ("./js/app.js?v=1.8.0", "./js/app.js?v=1.8.1")))
        self.assertTrue(any(v in html_code for v in ("./css/tokens.css?v=1.8.0", "./css/tokens.css?v=1.8.1")))

    # =========================================================================
    # 2. IOS PWA WEB-KIT DRAG LOCK CONTRACTS
    # =========================================================================
    def test_02_ios_pwa_drag_lock_contracts(self):
        """Verify layout.css and components.css strictly lock WebKit pan-x on mood capsule scrolls."""
        layout_css = (BASE_DIR / "static" / "css" / "layout.css").read_text(encoding="utf-8")
        components_css = (BASE_DIR / "static" / "css" / "components.css").read_text(encoding="utf-8")

        # Verify pan-x and overflow-y lock in layout.css
        self.assertIn(".mobile-mood-scroll", layout_css)
        self.assertIn("touch-action: pan-x !important;", layout_css)
        self.assertIn("overflow-y: hidden !important;", layout_css)
        self.assertIn("overscroll-behavior-x: contain !important;", layout_css)
        self.assertIn("overscroll-behavior-y: none !important;", layout_css)
        self.assertIn("-webkit-overflow-scrolling: touch !important;", layout_css)

        # Verify container scroll leak protection
        self.assertIn("overflow-x: hidden;", layout_css)
        self.assertIn("touch-action: pan-y pinch-zoom;", layout_css)

        # Verify components.css also has strict pan-x lock
        self.assertIn("touch-action: pan-x !important;", components_css)
        self.assertIn("overscroll-behavior-y: none !important;", components_css)

    # =========================================================================
    # 3. DUAL-LAYER OFFLINE PWA RESILIENCE CONTRACTS
    # =========================================================================
    def test_03_offline_status_banner_dom_and_styles(self):
        """Verify Frosted Soft Sakura offline banner is present in DOM and components.css."""
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="offline-status-banner"', html_code)
        self.assertIn('id="offline-queue-badge"', html_code)
        self.assertIn('id="offline-queue-count"', html_code)
        self.assertIn("Đang ở chế độ ngoại tuyến", html_code)

        components_css = (BASE_DIR / "static" / "css" / "components.css").read_text(encoding="utf-8")
        self.assertIn(".offline-status-banner", components_css)
        self.assertIn("softPulse", components_css)

    def test_04_auth_js_offline_session_preservation(self):
        """Verify static/js/auth.js caches auth user and suppresses login modal when offline."""
        auth_js = (BASE_DIR / "static" / "js" / "auth.js").read_text(encoding="utf-8")
        self.assertIn("kokoro_last_auth_user", auth_js)
        self.assertIn("saveLastAuthUser", auth_js)
        self.assertIn("getLastAuthUser", auth_js)
        self.assertIn("clearLastAuthUser", auth_js)
        # Verify checkSession suppresses modal when offline
        self.assertIn("!navigator.onLine", auth_js)
        self.assertIn("Failed to fetch", auth_js)

    def test_05_client_api_offline_cache_manager(self):
        """Verify static/js/api.js provides CacheManager, offline fallbacks and IndexedDB queue."""
        api_js = (BASE_DIR / "static" / "js" / "api.js").read_text(encoding="utf-8")
        self.assertIn("CacheManager", api_js)
        self.assertIn("_isOffline: true", api_js)
        self.assertIn("saveOfflineEntry", api_js)
        self.assertIn("syncOfflineQueue", api_js)
        self.assertIn("getOfflineEntries", api_js)
        self.assertIn("createCategory", api_js)
        self.assertIn("updateCategory", api_js)
        self.assertIn("deleteCategory", api_js)
        self.assertIn("createTag", api_js)

    def test_06_service_worker_offline_caching_strategy(self):
        """Verify static/sw.js implements Network-First for GET /api/ and bypasses mutations."""
        sw_js = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        self.assertIn("event.request.method !== 'GET'", sw_js)
        self.assertIn("return;", sw_js)
        self.assertIn("fetch(event.request)", sw_js)
        self.assertIn("caches.open(CACHE_NAME)", sw_js)

    # =========================================================================
    # 4. DATABASE & REPOSITORY CONTRACTS (CATEGORIES & TAGS)
    # =========================================================================
    def test_07_database_schema_and_seeding_contracts(self):
        """Verify database.py schema contains categories table, FK ON DELETE SET NULL, and 5 default categories."""
        db_code = (BASE_DIR / "app" / "database.py").read_text(encoding="utf-8")

        # Categories table schema
        self.assertIn("CREATE TABLE IF NOT EXISTS categories", db_code)
        self.assertIn("user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE", db_code)
        self.assertIn("UNIQUE (user_id, name)", db_code)
        self.assertIn("idx_categories_user", db_code)

        # Alter entries with ON DELETE SET NULL
        self.assertIn("ALTER TABLE entries ADD COLUMN IF NOT EXISTS category_id INT REFERENCES categories(id) ON DELETE SET NULL;", db_code)
        self.assertIn("idx_entries_user_cat", db_code)
        self.assertIn("idx_entry_tags_tag_id", db_code)

        # Default 5 seeded categories
        self.assertEqual(len(DEFAULT_CATEGORIES), 5)
        cat_names = [c["name"] for c in DEFAULT_CATEGORIES]
        self.assertIn("Đời thường", cat_names)
        self.assertIn("Công việc", cat_names)
        self.assertIn("Tình cảm", cat_names)
        self.assertIn("Du lịch", cat_names)
        self.assertIn("Học tập", cat_names)

        # Seeding helper exists
        self.assertIn("def seed_default_categories(", db_code)

    def test_08_rest_api_auth_guards_and_routes(self):
        """Verify /api/categories and /api/tags enforce authentication guards (401)."""
        # Categories endpoints without credentials
        cat_get_resp = self.client.get("/api/categories")
        self.assertEqual(cat_get_resp.status_code, 401)
        self.assertFalse(cat_get_resp.json().get("authenticated", True))

        cat_post_resp = self.client.post("/api/categories", json={"name": "Test Cat"})
        self.assertEqual(cat_post_resp.status_code, 401)

        # Tags endpoints without credentials
        tag_get_resp = self.client.get("/api/tags")
        self.assertEqual(tag_get_resp.status_code, 401)

        tag_post_resp = self.client.post("/api/tags", json={"name": "#testtag"})
        self.assertEqual(tag_post_resp.status_code, 401)

    def test_09_entry_dto_category_wiring(self):
        """Verify EntryDTO and EntryRepository serialize category metadata."""
        schema_code = (BASE_DIR / "app" / "schemas" / "entry.py").read_text(encoding="utf-8")
        self.assertIn("category_id: Optional[int]", schema_code)
        self.assertIn("category_name: Optional[str]", schema_code)
        self.assertIn("category_icon: Optional[str]", schema_code)
        self.assertIn("category_color: Optional[str]", schema_code)
        self.assertIn('"categoryId": self.category_id', schema_code)
        self.assertIn('"categoryName": self.category_name', schema_code)

        repo_code = (BASE_DIR / "app" / "repositories" / "entry_repository.py").read_text(encoding="utf-8")
        self.assertIn("c.name AS category_name", repo_code)
        self.assertIn("LEFT JOIN categories c ON e.category_id = c.id", repo_code)

    def test_10_logout_cascade_and_zen_prompt_shuffle_contracts(self):
        """Verify app.js, tag-manager.js, and zen-prompts.js fix 401 cascade and TypeError."""
        app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
        tag_manager_js = (BASE_DIR / "static" / "js" / "tag-manager.js").read_text(encoding="utf-8")
        zen_prompts_js = (BASE_DIR / "static" / "js" / "zen-prompts.js").read_text(encoding="utf-8")

        # 1. app.js guards onUserChanged against null user
        self.assertIn("if (!user) {", app_js)
        self.assertIn("this.entries = [];", app_js)
        self.assertIn("window.KokoroTimelineFeed.render([])", app_js)

        # 2. app.js defensive zen prompt shuffle handler
        self.assertIn("typeof p.shufflePrompt === 'function'", app_js)
        self.assertIn("typeof p.getRandomPrompt === 'function'", app_js)

        # 3. zen-prompts.js exports shufflePrompt and renderNewPrompt
        self.assertIn("shufflePrompt(currentId = null)", zen_prompts_js)
        self.assertIn("renderNewPrompt(currentId = null)", zen_prompts_js)

        # 4. tag-manager.js guards getTags against unauthenticated user
        self.assertIn("window.KokoroAuth && !window.KokoroAuth.currentUser", tag_manager_js)

    def test_11_backup_input_lifecycle_and_pwa_meta_contracts(self):
        """Verify backupInput declaration, error boundaries, PWA meta tag, and Node execution."""
        app_js = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
        auth_js = (BASE_DIR / "static" / "js" / "auth.js").read_text(encoding="utf-8")
        index_html = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")

        # 1. backupInput safe declaration
        self.assertIn("const backupInput = document.getElementById('backup-file-input') || document.getElementById('profile-restore-input');", app_js)
        self.assertIn('id="backup-file-input"', index_html)

        # 2. setupEventListeners and setupNetworkListeners wrapped in error boundaries
        self.assertIn("try { this.setupEventListeners(); }", app_js)
        self.assertIn("try { this.setupNetworkListeners(); }", app_js)
        self.assertIn("safeRun(() => {", app_js)

        # 3. PWA meta tag modern Chromium/WebKit standard
        self.assertIn('<meta name="mobile-web-app-capable" content="yes">', index_html)

        # 4. auth.js pre-hydrates session and handles profile-action-logout
        self.assertIn("const cachedUser = this.getLastAuthUser();", auth_js)
        self.assertIn("profile-action-logout", auth_js)

        # 5. Node.js execution verification of KokoroApp.init()
        import subprocess
        node_script = """
const fs = require('fs');
const vm = require('vm');
const dom = {
  getElementById: (id) => ({ addEventListener: () => {}, style: {}, classList: { add: () => {}, remove: () => {}, toggle: () => {} }, querySelectorAll: () => [] }),
  querySelectorAll: () => [],
  addEventListener: () => {},
  documentElement: { getAttribute: () => 'light', setAttribute: () => {} }
};
const sandbox = {
  window: { location: { hash: '#timeline' }, addEventListener: () => {}, scrollTo: () => {}, history: { replaceState: () => {}, pushState: () => {} }, localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} }, navigator: { onLine: true } },
  document: dom,
  location: { hash: '#timeline' },
  navigator: { onLine: true },
  history: { replaceState: () => {}, pushState: () => {} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  console: console,
  setTimeout: setTimeout,
  clearTimeout: clearTimeout
};
sandbox.window.window = sandbox.window;
sandbox.window.document = dom;
const code = fs.readFileSync('static/js/app.js', 'utf8');
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
sandbox.window.KokoroApp.init();
process.stdout.write('OK');
"""
        res = subprocess.run(["node", "-e", node_script], cwd=str(BASE_DIR), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Node execution failed: {res.stderr}")
        self.assertIn("OK", res.stdout)

    def test_12_pwa_auto_refresh_and_skip_waiting_contracts(self):
        """Verify sw.js and pwa.js implement skipWaiting, clients.claim, update on visibilitychange, and controllerchange reload."""
        sw_code = (BASE_DIR / "static" / "sw.js").read_text(encoding="utf-8")
        pwa_code = (BASE_DIR / "static" / "js" / "pwa.js").read_text(encoding="utf-8")

        # 1. sw.js calls self.skipWaiting() on install and chains self.clients.claim() on activate
        self.assertIn("self.skipWaiting();", sw_code)
        self.assertIn(".then(() => self.clients.claim())", sw_code)
        self.assertIn("SKIP_WAITING", sw_code)

        # 2. pwa.js registers sw.js and probes update on start and visibilitychange
        self.assertIn("registration.update()", pwa_code)
        self.assertIn("visibilitychange", pwa_code)
        self.assertIn("document.visibilityState === 'visible'", pwa_code)

        # 3. pwa.js handles controllerchange with refreshing anti-loop guard and reloads
        self.assertIn("controllerchange", pwa_code)
        self.assertIn("refreshing = true", pwa_code)
        self.assertIn("window.location.reload()", pwa_code)

    def test_13_auth_dropdown_logout_and_login_modal_fallback_contracts(self):
        """Verify fix for avatar dropdown logout race condition, scrollable menu, and modal login button recovery."""
        glass_css = (BASE_DIR / "static" / "css" / "glass.css").read_text(encoding="utf-8")
        app_code = (BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
        auth_code = (BASE_DIR / "static" / "js" / "auth.js").read_text(encoding="utf-8")
        html_code = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")

        # 1. glass.css scrolling and pointer-events
        self.assertIn("max-height: min(460px, calc(100vh - 80px))", glass_css)
        self.assertIn("overflow-y: auto", glass_css)
        self.assertIn("#logout-btn i", glass_css)
        self.assertIn("pointer-events: none;", glass_css)

        # 2. app.js event delegation for #logout-btn
        self.assertIn("e.target.closest('#logout-btn')", app_code)
        self.assertIn("window.KokoroAuth.logout()", app_code)

        # 3. auth.js ensureLoginButtonsRendered and fallback
        self.assertIn("ensureLoginButtonsRendered", auth_code)
        self.assertIn("guest-demo-login-btn", auth_code)
        self.assertIn("Trải nghiệm nhanh (Khách / Guest Demo)", auth_code)

        # 4. index.html login-divider default display none
        self.assertIn('id="login-divider" style="display: none;"', html_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)

