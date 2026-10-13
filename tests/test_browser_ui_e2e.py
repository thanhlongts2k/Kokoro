"""
KOKORO (心) — BROWSER UI AUTOMATED AUDIT & VERIFICATION SUITE
Uses Playwright with Edge to verify UI components, interactions, and layout integrity.
"""

import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.async_api import async_playwright
from app.auth import create_session_token, SESSION_COOKIE_NAME

async def run_browser_audit():
    token = create_session_token(38, "thanhlongts2k@gmail.com", "Thành Long")
    results = {
        "zen_audio": {},
        "passcode": {},
        "views": {},
        "memories": {},
        "timeline_cards": {}
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        await context.add_cookies([{
            "name": SESSION_COOKIE_NAME,
            "value": token,
            "domain": "localhost",
            "path": "/"
        }])

        page = await context.new_page()
        console_errors = []
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        await page.goto("http://localhost:5050", wait_until="networkidle")
        await asyncio.sleep(1.5)

        # 1. Audit Zen Audio
        zen_toggle = await page.query_selector("#zen-toggle-btn")
        zen_expand = await page.query_selector("#zen-expand-btn")
        zen_panel = await page.query_selector("#zen-player-panel")
        results["zen_audio"]["toggle_exists"] = zen_toggle is not None
        results["zen_audio"]["expand_exists"] = zen_expand is not None
        results["zen_audio"]["panel_exists"] = zen_panel is not None

        # Check mobile visibility of zen controls
        await page.set_viewport_size({"width": 390, "height": 844})
        await asyncio.sleep(0.3)
        expand_mobile_vis = await page.evaluate("() => { const el = document.getElementById('zen-expand-btn'); return el ? window.getComputedStyle(el).display : 'none'; }")
        results["zen_audio"]["mobile_expand_display"] = expand_mobile_vis # 'none' currently! Bug confirmed!

        # Reset to desktop
        await page.set_viewport_size({"width": 1280, "height": 800})
        await asyncio.sleep(0.3)

        # 2. Audit Passcode Settings
        passcode_change_btn = await page.query_selector("#passcode-change-btn")
        passcode_toggle = await page.query_selector("#passcode-toggle-switch")
        passcode_timeout = await page.query_selector("#passcode-timeout-select")
        results["passcode"]["change_btn_exists"] = passcode_change_btn is not None
        results["passcode"]["toggle_exists"] = passcode_toggle is not None
        results["passcode"]["timeout_exists"] = passcode_timeout is not None

        # Check profile badge code
        badge_text = await page.evaluate("() => { const b = document.getElementById('profile-action-pin-badge'); return b ? b.textContent : null; }")
        results["passcode"]["initial_profile_badge"] = badge_text

        # 3. Audit Memories Mood Container ID mismatch
        mem_scroll_exists = await page.evaluate("() => document.getElementById('memories-mood-scroll') !== null")
        mem_filters_exists = await page.evaluate("() => document.getElementById('memories-mood-filters') !== null")
        results["memories"]["memories_mood_scroll_exists"] = mem_scroll_exists # False! Bug confirmed!
        results["memories"]["memories_mood_filters_exists"] = mem_filters_exists # True!

        # 4. Audit Timeline Cards Layout
        cards = await page.query_selector_all(".journal-card")
        results["timeline_cards"]["count"] = len(cards)
        gaps = []
        for i in range(1, len(cards)):
            box_prev = await cards[i-1].bounding_box()
            box_curr = await cards[i].bounding_box()
            if box_prev and box_curr:
                gaps.append(round(box_curr["y"] - (box_prev["y"] + box_prev["height"]), 1))
        results["timeline_cards"]["gaps"] = gaps

        results["console_errors"] = console_errors
        await browser.close()

    return results

if __name__ == "__main__":
    res = asyncio.run(run_browser_audit())
    print("\n================ BROWSER AUDIT FINDINGS ================")
    for k, v in res.items():
        print(f"[{k}]: {v}")
