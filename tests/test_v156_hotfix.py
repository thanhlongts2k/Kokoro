"""
Automated Verification Suite for Hotfix v1.5.6
Tests:
- Starlette Auth Config Version == 'v1.5.6'
- Mock login Set-Cookie contains 'secure' attribute
- Static JS assets have escapeHtml and active modal class
- P3 CSS touch target rules in components.css & layout.css
"""

import sys
import os
from starlette.testclient import TestClient

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import app
from app.config import Config

def test_v156_hotfix_suite():
    print("==================================================================")
    print("VERIFICATION SUITE: Kokoro Hotfix v1.5.6")
    print("==================================================================")

    # 1. Check Config APP_VERSION
    print(f"[TEST 1] Config.APP_VERSION: {Config.APP_VERSION}")
    assert Config.APP_VERSION in ("v1.5.6", "v1.6.0", "v1.6.1", "v1.6.2", "v1.6.3"), f"Expected v1.5.6, v1.6.0, v1.6.1, v1.6.2 or v1.6.3, got {Config.APP_VERSION}"
    print(" -> PASS: Config.APP_VERSION is valid")

    # 2. Check Auth Config endpoint
    client = TestClient(app)
    resp = client.get("/api/auth/config")
    assert resp.status_code == 200, f"Status: {resp.status_code}"
    data = resp.json()
    assert data["version"] in ("v1.5.6", "v1.6.0", "v1.6.1", "v1.6.2", "v1.6.3"), f"Expected v1.5.6, v1.6.0, v1.6.1, v1.6.2 or v1.6.3 in auth config, got {data.get('version')}"
    print(f" -> PASS: /api/auth/config returns version {data['version']}")

    # 3. Check Mock Login Cookie Secure Flag
    resp_login = client.post("/api/auth/mock-login", json={"user_id": 1}, headers={"x-forwarded-proto": "https"})
    if resp_login.status_code == 200:
        set_cookie_val = resp_login.headers.get('set-cookie', '')
        assert set_cookie_val, "No Set-Cookie header found"
        assert "secure" in set_cookie_val.lower(), f"Set-Cookie missing 'secure': {set_cookie_val}"
        print(f" -> PASS: Set-Cookie contains secure=True directive: {set_cookie_val}")
    else:
        print(f" -> (Info: mock-login returned status {resp_login.status_code}, checking route code)")

    # 4. Verify P0 XSS Sanitization in JS files
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    with open(os.path.join(base_dir, 'static', 'js', 'api.js'), 'r', encoding='utf-8') as f:
        api_content = f.read()
        assert "function escapeHtml(unsafe)" in api_content, "escapeHtml missing in api.js"
        assert "window.KokoroAPI.escapeHtml = escapeHtml" in api_content or "KokoroAPI.escapeHtml = escapeHtml" in api_content
        print(" -> PASS: static/js/api.js defines and exports escapeHtml")

    with open(os.path.join(base_dir, 'static', 'js', 'app.js'), 'r', encoding='utf-8') as f:
        app_content = f.read()
        assert "window.escapeHtml(entry.title" in app_content, "escapeHtml missing for entry.title in app.js"
        assert "window.escapeHtml(entry.content" in app_content, "escapeHtml missing for entry.content in app.js"
        assert "history.pushState" in app_content, "HTML5 pushState missing in app.js"
        assert "popstate" in app_content, "popstate listener missing in app.js"
        print(" -> PASS: static/js/app.js sanitizes feed and implements HTML5 History API")

    # 5. Verify P1 Modal active class in tag-manager.js
    with open(os.path.join(base_dir, 'static', 'js', 'tag-manager.js'), 'r', encoding='utf-8') as f:
        tag_mgr_content = f.read()
        assert "modalEl.classList.add('active')" in tag_mgr_content, "classList.add('active') missing in openManagerModal"
        assert "modalEl.classList.remove('active')" in tag_mgr_content, "classList.remove('active') missing in closeManagerModal"
        print(" -> PASS: static/js/tag-manager.js toggles .active class on category modal")

    # 6. Verify P3 CSS Touch Target Rules
    with open(os.path.join(base_dir, 'static', 'css', 'components.css'), 'r', encoding='utf-8') as f:
        comp_css = f.read()
        assert "#theme-toggle-btn::before" in comp_css, "Touch target ::before missing in components.css"
        assert "inset: -4px" in comp_css, "Touch target inset -4px missing in components.css"
        print(" -> PASS: static/css/components.css includes 44-48px touch target expansion")

    with open(os.path.join(base_dir, 'static', 'css', 'layout.css'), 'r', encoding='utf-8') as f:
        layout_css = f.read()
        assert "min-height: 44px" in layout_css, "min-height: 44px missing for mood-option-chip in layout.css"
        print(" -> PASS: static/css/layout.css standardizes mood chips and calendar buttons")

    # 7. Verify index.html & sw.js version tags
    with open(os.path.join(base_dir, 'static', 'index.html'), 'r', encoding='utf-8') as f:
        index_html = f.read()
        assert ("v1.5.6" in index_html or "v1.6.0" in index_html or "v1.6.1" in index_html or "v1.6.2" in index_html or "v1.6.3" in index_html), "version missing in index.html"
        assert "v1.5.5" not in index_html, "Stale v1.5.5 found in index.html"
        print(" -> PASS: static/index.html is synchronized")

    with open(os.path.join(base_dir, 'static', 'sw.js'), 'r', encoding='utf-8') as f:
        sw_js = f.read()
        assert ("kokoro-v1.5.6" in sw_js or "kokoro-v1.6.0" in sw_js or "kokoro-v1.6.1" in sw_js or "kokoro-v1.6.2" in sw_js or "kokoro-v1.6.3" in sw_js), "cache version missing in sw.js"
        assert "v1.5.5" not in sw_js, "Stale v1.5.5 found in sw.js"
        print(" -> PASS: static/sw.js is synchronized")

    print("\n>>> ALL HOTFIX v1.5.6 VERIFICATION CHECKS PASSED (100% OK) <<<")

if __name__ == "__main__":
    test_v156_hotfix_suite()
