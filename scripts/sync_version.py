"""
KOKORO (心) — SINGLE SOURCE OF TRUTH (SSoT) VERSION SYNCHRONIZER
Usage:
    python scripts/sync_version.py           # Sync all files to VERSION file
    python scripts/sync_version.py 1.7.8     # Bump to new version and sync
    python scripts/sync_version.py --check   # Verify synchronization (exit 0/1)
"""

import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = BASE_DIR / "VERSION"
CONFIG_FILE = BASE_DIR / "app" / "config.py"
SW_FILE = BASE_DIR / "static" / "sw.js"
INDEX_FILE = BASE_DIR / "static" / "index.html"

def get_target_version():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        ver = sys.argv[1].lstrip("v").strip()
        VERSION_FILE.write_text(ver + "\n", encoding="utf-8")
        return ver
    return VERSION_FILE.read_text(encoding="utf-8").strip().lstrip("v")

def sync():
    target_ver = get_target_version()
    semver = f"v{target_ver}"
    print(f"[Kokoro SSoT Version] Synchronizing entire platform to {semver} ({target_ver})...")

    # 1. Update app/config.py
    config_code = CONFIG_FILE.read_text(encoding="utf-8")
    new_config_code = re.sub(
        r'APP_VERSION:\s*str\s*=\s*"[^"]+"',
        f'APP_VERSION: str = "{semver}"',
        config_code
    )
    CONFIG_FILE.write_text(new_config_code, encoding="utf-8")
    print(f" -> [OK] app/config.py updated to {semver}")

    # 2. Update static/sw.js
    sw_code = SW_FILE.read_text(encoding="utf-8")
    # Update APP_VERSION constant or CACHE_NAME
    if "const APP_VERSION =" in sw_code:
        sw_code = re.sub(r"const APP_VERSION = '[^']+';", f"const APP_VERSION = '{target_ver}';", sw_code)
    else:
        sw_code = re.sub(r"const CACHE_NAME = '[^']+';", f"const CACHE_NAME = 'kokoro-{semver}';", sw_code)
    # Update any ?v= query strings
    sw_code = re.sub(r"\?v=\d+\.\d+\.\d+", f"?v={target_ver}", sw_code)
    # Update header comment
    sw_code = re.sub(r"// Kokoro Service Worker v\d+\.\d+\.\d+", f"// Kokoro Service Worker {semver}", sw_code)
    SW_FILE.write_text(sw_code, encoding="utf-8")
    print(f" -> [OK] static/sw.js cache & query strings updated to {semver}")

    # 3. Update static/index.html
    html_code = INDEX_FILE.read_text(encoding="utf-8")
    html_code = re.sub(
        r'id="app-version-badge">v\d+\.\d+\.\d+</span>',
        f'id="app-version-badge">{semver}</span>',
        html_code
    )
    html_code = re.sub(r"\?v=\d+\.\d+\.\d+", f"?v={target_ver}", html_code)
    INDEX_FILE.write_text(html_code, encoding="utf-8")
    print(f" -> [OK] static/index.html badge & asset tags updated to {semver}")

    print(f"\n✨ SUCCESS: 100% of Kokoro version artifacts are synchronized to {semver} ✨\n")

def check():
    target_ver = VERSION_FILE.read_text(encoding="utf-8").strip().lstrip("v")
    semver = f"v{target_ver}"
    errors = []

    config_code = CONFIG_FILE.read_text(encoding="utf-8")
    if f'APP_VERSION: str = "{semver}"' not in config_code:
        errors.append(f"app/config.py is out of sync with {semver}")

    sw_code = SW_FILE.read_text(encoding="utf-8")
    if f"kokoro-{semver}" not in sw_code and f"APP_VERSION = '{target_ver}'" not in sw_code:
        errors.append(f"static/sw.js is out of sync with {semver}")

    html_code = INDEX_FILE.read_text(encoding="utf-8")
    if f'id="app-version-badge">{semver}</span>' not in html_code:
        errors.append(f"static/index.html badge is out of sync with {semver}")

    if errors:
        print("[ERROR] Version synchronization mismatch:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print(f"[OK] 100% synchronized with VERSION ({semver})")
        sys.exit(0)

if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        sync()
