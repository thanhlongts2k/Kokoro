import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_ios_pwa():
    print("=================================================================")
    print("  KOKORO (心) — PLAYWRIGHT iOS PWA AUDIT & HARDENING TEST")
    print("=================================================================")

    screenshot_dir = os.path.dirname(os.path.abspath(__file__))

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)

        # iPhone 15 Pro viewport
        width, height = 393, 852
        print(f"\n--- Testing iPhone Viewport: {width}x{height} ---")
        context = browser.new_context(
            viewport={"width": width, "height": height},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )
        page = context.new_page()

        page.goto("http://127.0.0.1:5050/", wait_until="networkidle")
        time.sleep(1)

        # 1. Log in as user 38 (Nguyễn Thành Long)
        page.evaluate("""async () => {
            if (window.KokoroAPI) {
                const res = await window.KokoroAPI.mockLogin(38);
                if (window.KokoroAuth) {
                    await window.KokoroAuth.handleLoginSuccess(res.user);
                }
            }
        }""")
        time.sleep(1)

        # 2. Open Editor Modal
        page.evaluate("() => { if (window.Editor) window.Editor.open(); }")
        time.sleep(0.5)

        # 3. SPAM CLICK TEST: Click Save button 10 times rapidly on empty form
        print("\n[TEST 1] Spam clicking Save button 10 times rapidly...")
        for i in range(10):
            page.evaluate("() => { const btn = document.getElementById('editor-save-btn'); if (btn) btn.click(); }")
        time.sleep(0.5)

        # Count visible toasts
        toast_count = page.evaluate("() => document.querySelectorAll('#toast-container .toast-item').length")
        print(f"Total visible toasts in DOM after 10 rapid clicks: {toast_count}")
        assert toast_count <= 2, f"Spam waterfall detected! Expected <= 2 toasts, found {toast_count}"
        assert toast_count == 1, f"Expected exactly 1 deduplicated toast, found {toast_count}"

        # Verify Toast Position on Mobile (Must be at the TOP, not obscuring bottom buttons)
        toast_box = page.evaluate("""() => {
            const container = document.getElementById('toast-container');
            const toast = document.querySelector('#toast-container .toast-item');
            if (!toast) return null;
            const rect = toast.getBoundingClientRect();
            const computed = window.getComputedStyle(container);
            return {
                top: rect.top,
                bottom: rect.bottom,
                cssTop: computed.top,
                cssBottom: computed.bottom
            };
        }""")
        print(f"Toast bounding position: top={toast_box['top']}px (CSS top={toast_box['cssTop']}, CSS bottom={toast_box['cssBottom']})")
        assert toast_box["top"] < 100, f"Toast is not at top of screen! top={toast_box['top']}px"
        print("✓ Toast deduplication & top-positioning verified! Zero spam waterfall!")

        spam_screenshot = os.path.join(screenshot_dir, "ios_spam_click_toast_verified.png")
        page.screenshot(path=spam_screenshot)
        print(f"Saved screenshot: {spam_screenshot}")

        # Wait for toast to fade out
        time.sleep(3.6)

        # 4. Fill in form: Title, Content, Tag, and an Attached Photo
        print("\n[TEST 2] Filling in Diary Entry Form with Text & Image...")
        page.evaluate("""async () => {
            const ed = window.Editor;
            ed.titleInput.value = 'Nóng nực vô cùng';
            ed.contentInput.value = 'Làm trên cty mà cúp điênn';
            ed.tagInput.value = '#cupdien';
            
            // Attach a simulated 1x1 png image
            const res = await fetch('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==');
            const blob = await res.blob();
            const file = new File([blob], 'laptop_workspace.png', { type: 'image/png' });
            ed.handleFiles([file]);
        }""")
        time.sleep(0.5)

        # Check footer buttons geometry inside modal
        footer_geometry = page.evaluate("""() => {
            const footer = document.querySelector('.editor-footer');
            const saveBtn = document.getElementById('editor-save-btn');
            const cancelBtn = document.getElementById('editor-cancel-btn');
            const fRect = footer.getBoundingClientRect();
            const sRect = saveBtn.getBoundingClientRect();
            const cRect = cancelBtn.getBoundingClientRect();
            return {
                footerBottom: fRect.bottom,
                footerHeight: fRect.height,
                saveBtnBottom: sRect.bottom,
                saveBtnHeight: sRect.height,
                cancelBtnBottom: cRect.bottom,
                cancelBtnHeight: cRect.height,
                viewportHeight: window.innerHeight
            };
        }""")
        print(f"Footer geometry: {footer_geometry}")
        # Save button must be completely visible (height around 40px) and inside viewport
        assert footer_geometry["saveBtnHeight"] >= 36, f"Save button height is crushed: {footer_geometry['saveBtnHeight']}"
        assert footer_geometry["saveBtnBottom"] <= footer_geometry["viewportHeight"], f"Save button overflowed viewport! {footer_geometry['saveBtnBottom']} > {footer_geometry['viewportHeight']}"
        print("✓ Button safe area & layout alignment verified! Buttons are fully visible and not cut off!")

        button_screenshot = os.path.join(screenshot_dir, "ios_editor_buttons_safe_area_verified.png")
        page.screenshot(path=button_screenshot)
        print(f"Saved screenshot: {button_screenshot}")

        # 5. Click Save Entry
        print("\n[TEST 3] Clicking Save Button to persist entry...")
        page.click("#editor-save-btn")
        time.sleep(1.5)

        # Check timeline feed for newly saved entry
        has_entry = page.evaluate("""() => {
            const text = document.body.innerText;
            return text.includes('Làm trên cty mà cúp điênn') || text.includes('Nóng nực vô cùng');
        }""")
        print(f"New entry rendered on timeline feed: {has_entry}")
        assert has_entry, "Newly saved entry not found on timeline feed!"

        feed_screenshot = os.path.join(screenshot_dir, "ios_saved_entry_verified.png")
        page.screenshot(path=feed_screenshot)
        print(f"Saved screenshot: {feed_screenshot}")

        browser.close()

    print("\n=================================================================")
    print("  ALL PLAYWRIGHT iOS PWA TESTS PASSED 100%! ✨")
    print("=================================================================\n")

if __name__ == '__main__':
    test_ios_pwa()
