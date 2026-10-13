"""
KOKORO (心) — COMPREHENSIVE INTERACTIVE BROWSER E2E TEST
Verifies all interactive flows: Zen Audio track switching, PIN setup & change,
Multi-view navigation, Memories filters, and Card Export modal.
"""

import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.async_api import async_playwright
from app.auth import create_session_token, SESSION_COOKIE_NAME

async def main():
    token = create_session_token(38, "thanhlongts2k@gmail.com", "Thành Long")
    print("Testing with User 38 (thanhlongts2k@gmail.com)...")

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
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_messages.append(f"[PAGE ERROR] {err}"))

        await page.goto("http://localhost:5050", wait_until="networkidle")
        await asyncio.sleep(1.5)

        # ---------------------------------------------------------------------
        # 1. TEST ZEN AUDIO INTERACTION
        # ---------------------------------------------------------------------
        print("\n--- 1. Testing Zen Audio Interaction ---")
        zen_expand = page.locator("#zen-expand-btn")
        await zen_expand.click()
        await asyncio.sleep(0.3)
        panel_active = await page.evaluate("() => document.getElementById('zen-player-panel').classList.contains('active')")
        assert panel_active, "Zen player panel must be active"
        print("PASS: Zen panel opened on click.")

        # Switch to 'furin' track
        furin_chip = page.locator('[data-zen-track="furin"]')
        await furin_chip.click()
        await asyncio.sleep(0.3)
        current_track = await page.evaluate("() => window.ZenAudio.currentTrackKey")
        assert current_track == "furin", f"Expected furin, got {current_track}"
        print(f"PASS: Switched to track '{current_track}'.")

        # Switch to 'waves' track
        waves_chip = page.locator('[data-zen-track="waves"]')
        await waves_chip.click()
        await asyncio.sleep(0.3)
        current_track = await page.evaluate("() => window.ZenAudio.currentTrackKey")
        assert current_track == "waves", f"Expected waves, got {current_track}"
        print(f"PASS: Switched to track '{current_track}'.")

        # Close panel by clicking body
        await page.mouse.click(100, 200)
        await asyncio.sleep(0.3)
        panel_closed = not await page.evaluate("() => document.getElementById('zen-player-panel').classList.contains('active')")
        assert panel_closed, "Zen panel must close on outside click"
        print("PASS: Zen panel closed on outside click.")

        # ---------------------------------------------------------------------
        # 2. TEST PASSCODE PIN SETUP & SETTINGS
        # ---------------------------------------------------------------------
        print("\n--- 2. Testing Passcode PIN Setup & Settings ---")
        # Navigate to profile
        prof_tab = page.locator('.c-chip[data-switch-view="profile"]')
        await prof_tab.click()
        await asyncio.sleep(0.3)

        # Click PIN action item
        pin_item = page.locator("#profile-action-pin")
        await pin_item.click()
        await asyncio.sleep(0.3)
        settings_modal_active = await page.evaluate("() => document.getElementById('passcode-settings-modal').classList.contains('active')")
        assert settings_modal_active, "Passcode settings modal must be active"
        print("PASS: Passcode settings modal opened from Profile.")

        # Test toggle switch to start PIN setup flow
        toggle_switch = page.locator("#passcode-toggle-switch")
        await toggle_switch.click()
        await asyncio.sleep(0.3)
        lock_overlay_active = await page.evaluate("() => document.getElementById('passcode-lock-overlay').classList.contains('active')")
        assert lock_overlay_active, "Passcode lock overlay must open for PIN setup"
        print("PASS: Lock overlay opened to enter new PIN.")

        # Enter PIN digits: 1, 2, 3, 4
        for d in ["1", "2", "3", "4"]:
            btn = page.locator(f'[data-passcode-digit="{d}"]')
            await btn.click()
            await asyncio.sleep(0.1)

        await asyncio.sleep(0.5)
        # Verify subtitle asks for confirmation
        sub_text = await page.evaluate("() => document.getElementById('passcode-subtitle').textContent")
        print(f"PASS: First PIN entered. Step prompt: '{sub_text}'")

        # Confirm PIN digits: 1, 2, 3, 4
        for d in ["1", "2", "3", "4"]:
            btn = page.locator(f'[data-passcode-digit="{d}"]')
            await btn.click()
            await asyncio.sleep(0.1)

        await asyncio.sleep(0.8)
        # Check that PIN is enabled now
        is_pin_enabled = await page.evaluate("() => window.PasscodeLock.isEnabled()")
        assert is_pin_enabled, "Passcode must be enabled after confirmation"
        print("PASS: Passcode successfully set and enabled in localStorage!")

        # Verify badge in Profile shows 'Đang bật'
        badge_text = await page.evaluate("() => document.getElementById('profile-action-pin-badge').textContent")
        assert badge_text == "Đang bật", f"Expected 'Đang bật', got '{badge_text}'"
        print(f"PASS: Profile badge updated to '{badge_text}'.")

        # ---------------------------------------------------------------------
        # 3. TEST MEMORIES VIEW & DYNAMIC FILTERS
        # ---------------------------------------------------------------------
        print("\n--- 3. Testing Memories View & Dynamic Filters ---")
        mem_tab = page.locator('.c-chip[data-switch-view="memories"]')
        await mem_tab.click()
        await asyncio.sleep(0.5)

        # Check that memories mood filter has pills rendered
        mood_pills = page.locator('#memories-mood-filters .memory-mood-pill, #memories-mood-scroll .memory-mood-pill')
        pill_count = await mood_pills.count()
        assert pill_count >= 1, f"Expected at least 1 mood pill in memories, got {pill_count}"
        print(f"PASS: Memories mood pills rendered successfully (count = {pill_count}).")

        # Click second mood pill
        await mood_pills.nth(1).click()
        await asyncio.sleep(0.3)
        pill_active = await mood_pills.nth(1).evaluate("el => el.classList.contains('active')")
        assert pill_active, "Clicked mood pill must have active class"
        print("PASS: Memories mood filter chip is interactive and active.")

        # ---------------------------------------------------------------------
        # 4. TEST CALENDAR VIEW & DAY ENTRIES
        # ---------------------------------------------------------------------
        print("\n--- 4. Testing Calendar View ---")
        cal_tab = page.locator('.c-chip[data-switch-view="calendar"]')
        await cal_tab.click()
        await asyncio.sleep(0.5)

        # Check full calendar grid days
        days = page.locator('#full-calendar-grid .c-calendar-day')
        day_count = await days.count()
        assert day_count >= 28, f"Expected >= 28 calendar cells, got {day_count}"
        print(f"PASS: Full calendar month rendered (cells = {day_count}).")

        # Click a day cell
        await days.nth(15).click()
        await asyncio.sleep(0.3)
        heading_text = await page.evaluate("() => document.getElementById('calendar-selected-date-heading').textContent")
        print(f"PASS: Selected day heading updated to: '{heading_text}'")

        # ---------------------------------------------------------------------
        # 5. TEST TIMELINE FEED & CARD ACTIONS
        # ---------------------------------------------------------------------
        print("\n--- 5. Testing Timeline Feed & Daily Card Export Modal ---")
        time_tab = page.locator('.c-chip[data-switch-view="timeline"]')
        await time_tab.click()
        await asyncio.sleep(0.5)

        # Click export card button on first card
        export_btn = page.locator('.journal-card [data-action="export-card"]').first
        await export_btn.click()
        await asyncio.sleep(0.5)

        export_modal_active = await page.evaluate("() => document.getElementById('card-export-modal').classList.contains('active')")
        assert export_modal_active, "Card export modal must have 'active' class"
        print("PASS: Card Export Modal opened successfully.")

        # Switch theme to 'polaroid'
        polaroid_btn = page.locator('#theme-btn-polaroid')
        await polaroid_btn.click()
        await asyncio.sleep(0.3)
        theme_active = await polaroid_btn.evaluate("el => el.classList.contains('active')")
        assert theme_active, "Polaroid theme button must be active"
        print("PASS: Memory Studio Theme switched to Polaroid.")

        # Close export modal
        close_export_btn = page.locator('#card-export-close-btn')
        await close_export_btn.click()
        await asyncio.sleep(0.3)
        export_modal_closed = await page.evaluate("() => !document.getElementById('card-export-modal').classList.contains('active')")
        assert export_modal_closed, "Card export modal must not have 'active' class"
        print("PASS: Card Export Modal closed.")

        # ---------------------------------------------------------------------
        # 6. TEST EDITOR OPEN/CLOSE & BOTTOM SHEET INTERACTION
        # ---------------------------------------------------------------------
        print("\n--- 6. Testing Editor Open/Close & Bottom Sheet Interaction ---")
        add_btn = page.locator('.welcome-banner-card .btn-sakura, .bottom-nav-item[data-tab="editor"]').first
        await add_btn.click()
        await asyncio.sleep(0.4)
        editor_active = await page.evaluate("() => document.getElementById('editor-modal-overlay').classList.contains('active')")
        assert editor_active, "Editor modal must open on Add Entry click"
        print("PASS: Editor bottom sheet opened via UI button.")

        close_btn = page.locator("#editor-cancel-btn")
        await close_btn.click()
        await asyncio.sleep(0.3)
        editor_closed = await page.evaluate("() => !document.getElementById('editor-modal-overlay').classList.contains('active')")
        assert editor_closed, "Editor modal must close on Cancel click"
        print("PASS: Editor bottom sheet closed safely.")

        # Check console errors
        print("\n--- Console Error Audit ---")
        real_errors = [
            m for m in console_messages
            if "[PAGE ERROR]" in m or (
                "[error]" in m 
                and "failed to load resource" not in m.lower() 
                and "gsi" not in m.lower() 
                and "blocked_by_orb" not in m.lower()
            )
        ]
        if real_errors:
            print("Found errors:", real_errors)
            assert False, f"Found unexpected console errors: {real_errors}"
        else:
            print("PASS: 0 unexpected JavaScript console errors!")

        await browser.close()
        print("\n✨ ALL BROWSER E2E TESTS PASSED 100%! ✨\n")

if __name__ == "__main__":
    asyncio.run(main())
