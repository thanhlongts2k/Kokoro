import os
import sys
import time
from playwright.sync_api import sync_playwright

def main():
    print("[Playwright Test] Starting Profile Dropdown & Friendly Name Verification...")
    screenshot_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot_path = os.path.join(screenshot_dir, "desktop_profile_dropdown_open.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("[Step 1] Navigating to http://127.0.0.1:5050/ ...")
        page.goto("http://127.0.0.1:5050/", wait_until="networkidle")
        time.sleep(1)

        # Login as user 38 ("Nguyen Thanh Long")
        print("[Step 2] Switching/logging in as user 38 (Nguyen Thanh Long)...")
        page.evaluate("""async () => {
            if (window.KokoroAPI) {
                const res = await window.KokoroAPI.mockLogin(38);
                if (window.KokoroAuth) {
                    await window.KokoroAuth.handleLoginSuccess(res.user);
                }
            }
        }""")
        time.sleep(1)

        # Verify Header Name
        header_name = page.locator("#header-user-name").inner_text()
        print(f"[Step 3] Header User Name: {ascii(header_name)}")
        assert "Long" in header_name or "Nguy" in header_name, f"Unexpected header name: {header_name}"

        # Verify Greeting Banner text: Must say 'Chào Long,'
        greeting_text = page.locator("#welcome-greeting-title").inner_text()
        print(f"[Step 4] Greeting Banner Text: {ascii(greeting_text)}")
        assert "Long" in greeting_text, f"Greeting banner does not contain 'Long': {greeting_text}"
        assert "Nguy" not in greeting_text, f"Greeting banner erroneously contains family name: {greeting_text}"
        print("  -> PASS: Greeting banner properly displays friendly first name: 'Chao Long'!")

        # Step 5: Click Profile Pill on Header
        print("[Step 5] Clicking #user-profile-pill to open dropdown...")
        profile_pill = page.locator("#user-profile-pill")
        profile_pill.click()
        time.sleep(0.5)

        # Step 6: Verify dropdown is visible
        dropdown = page.locator("#profile-dropdown-menu")
        is_visible = dropdown.is_visible()
        print(f"[Step 6] Dropdown is_visible: {is_visible}")
        assert is_visible, "Profile dropdown menu is NOT visible after clicking!"

        # Step 7: Verify required items inside dropdown
        print("[Step 7] Checking required dropdown menu items...")
        
        # 1. Khoa PIN
        lock_pin = page.locator("#passcode-settings-btn")
        lock_now = page.locator("#lock-screen-now-btn")
        assert lock_pin.is_visible() and lock_now.is_visible(), "Missing PIN security options"
        print("  -> PASS: Khoa PIN options are visible (#passcode-settings-btn, #lock-screen-now-btn)")

        # 2. Dem / Ngay (Theme toggle)
        theme_toggle = page.locator("#dropdown-theme-toggle-btn")
        assert theme_toggle.is_visible(), "Missing Dem / Ngay theme toggle option in dropdown"
        print("  -> PASS: Dem / Ngay theme toggle is visible (#dropdown-theme-toggle-btn)")

        # 3. Sao luu / Khoi phuc
        export_btn = page.locator("#export-backup-btn")
        import_btn = page.locator("#import-backup-btn")
        assert export_btn.is_visible() and import_btn.is_visible(), "Missing Sao luu / Khoi phuc backup options"
        print("  -> PASS: Sao luu / Khoi phuc options are visible (#export-backup-btn, #import-backup-btn)")

        # 4. Dang xuat
        logout_btn = page.locator("#logout-btn")
        assert logout_btn.is_visible(), "Missing Dang xuat option in dropdown"
        print("  -> PASS: Dang xuat option is visible (#logout-btn)")

        # Step 8: Capture Screenshot
        page.screenshot(path=screenshot_path)
        print(f"[Step 8] Screenshot saved to: {screenshot_path}")

        # Step 9: Verify outside click closes dropdown
        print("[Step 9] Clicking outside to verify dropdown closes...")
        page.mouse.click(200, 200)
        time.sleep(0.3)
        assert not dropdown.is_visible(), "Dropdown should close when clicking outside!"
        print("  -> PASS: Dropdown closes upon clicking outside.")

        # Step 10: Verify second click opens dropdown again
        print("[Step 10] Clicking profile pill again to verify re-opening...")
        profile_pill.click()
        time.sleep(0.3)
        assert dropdown.is_visible(), "Dropdown should re-open on second pill click!"
        print("  -> PASS: Dropdown successfully toggles on subsequent clicks.")

        browser.close()
        print("=================================================================")
        print("  ALL PLAYWRIGHT TESTS PASSED 100%! VERIFICATION SUCCESSFUL!")
        print("=================================================================")

if __name__ == "__main__":
    main()
