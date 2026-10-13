import os
import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_mobile_editor():
    print("=================================================================")
    print("  KOKORO (心) — PLAYWRIGHT MOBILE OVERFLOW & MEDIA UI VERIFICATION")
    print("=================================================================")

    screenshot_dir = os.path.dirname(os.path.abspath(__file__))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for width, height in [(390, 844), (375, 812)]:
            print(f"\n--- Testing Mobile Viewport: {width}x{height} ---")
            context = browser.new_context(
                viewport={"width": width, "height": height},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            )
            page = context.new_page()

            page.goto("http://127.0.0.1:5050/", wait_until="networkidle")
            time.sleep(1)

            # Log in as user 1
            page.evaluate("""async () => {
                if (window.KokoroAPI) {
                    const res = await window.KokoroAPI.mockLogin(1);
                    if (window.KokoroAuth) {
                        await window.KokoroAuth.handleLoginSuccess(res.user);
                    }
                }
            }""")
            time.sleep(1)

            # Ensure there is an entry with photos
            entry_info = page.evaluate("""async () => {
                const res = await window.KokoroAPI.getEntries();
                let entryWithPhotos = res.entries.find(e => e.photos && e.photos.length >= 2);
                if (!entryWithPhotos) {
                    // Create one with 2 dummy photos using 1x1 base64 png
                    const pngBlob = await (await fetch('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')).blob();
                    const fd = new FormData();
                    fd.append('title', 'Nhat ky voi 2 anh kiem thu');
                    fd.append('content', 'Noi dung de kiem thu modal va xoa anh');
                    fd.append('mood', 'serene');
                    fd.append('photos', pngBlob, 'test1.png');
                    fd.append('photos', pngBlob, 'test2.png');
                    const created = await window.KokoroAPI.createEntry(fd);
                    const ref = await window.KokoroAPI.getEntries();
                    entryWithPhotos = ref.entries.find(e => e.id === created.entry_id);
                }
                return entryWithPhotos;
            }""")

            print(f"  -> Found entry with photos: ID={entry_info['id']}, Photos count={len(entry_info['photos'])}")

            # Open Editor in Edit Mode
            page.evaluate(f"""() => {{
                const entry = window.KokoroApp.entries.find(e => e.id === {entry_info['id']});
                window.Editor.open(entry);
            }}""")
            time.sleep(0.8)

            # Verify Modal is active
            dialog = page.locator("#editor-dialog")
            assert dialog.is_visible(), "Editor dialog must be visible!"

            # Check 1: Zero Horizontal Overflow
            overflow_metrics = page.evaluate("""() => {
                const doc = document.documentElement;
                const body = document.body;
                const dialog = document.getElementById('editor-dialog');
                const overlay = document.getElementById('editor-modal-overlay');
                const winW = window.innerWidth;

                return {
                    winW: winW,
                    docScrollW: doc.scrollWidth,
                    bodyScrollW: body.scrollWidth,
                    dialogScrollW: dialog.scrollWidth,
                    overlayScrollW: overlay.scrollWidth,
                    dialogClientW: dialog.clientWidth,
                    scrollX: window.scrollX,
                    hasDocOverflow: doc.scrollWidth > winW,
                    hasBodyOverflow: body.scrollWidth > winW,
                    hasDialogOverflow: dialog.scrollWidth > winW
                };
            }""")

            print(f"  -> Overflow metrics: {overflow_metrics}")
            assert not overflow_metrics["hasDocOverflow"], f"Document overflowed: {overflow_metrics['docScrollW']} > {overflow_metrics['winW']}"
            assert not overflow_metrics["hasBodyOverflow"], f"Body overflowed: {overflow_metrics['bodyScrollW']} > {overflow_metrics['winW']}"
            assert not overflow_metrics["hasDialogOverflow"], f"Dialog overflowed: {overflow_metrics['dialogScrollW']} > {overflow_metrics['winW']}"
            print(f"  -> PASS: ZERO Horizontal Overflow on {width}x{height}! (scrollWidth <= innerWidth)")

            # Check 2: Inspect Thumbnail Boxes and Remove Buttons
            thumbs_count = page.locator("#editor-previews-grid .preview-thumb-box").count()
            print(f"  -> Thumbs rendered in grid: {thumbs_count}")
            assert thumbs_count >= 2, f"Expected at least 2 thumbnails, got {thumbs_count}"

            remove_btns = page.locator("#editor-previews-grid .preview-remove-btn")
            btn_count = remove_btns.count()
            assert btn_count == thumbs_count, f"Every thumb must have a remove button! Found {btn_count} for {thumbs_count} thumbs"

            # Check button size
            first_btn_box = remove_btns.first.bounding_box()
            assert first_btn_box["width"] >= 26 and first_btn_box["height"] >= 26, f"Remove button too small: {first_btn_box}"
            print(f"  -> PASS: Remove button size is prominent ({first_btn_box['width']:.1f}x{first_btn_box['height']:.1f}px)!")

            # Check badges
            badges_count = page.locator("#editor-previews-grid .preview-saved-badge").count()
            assert badges_count == thumbs_count, f"Every saved thumb must have badge! Found {badges_count}"
            print("  -> PASS: Saved badges properly displayed on existing photos!")

            # Take screenshot before deletion
            sc_path = os.path.join(screenshot_dir, f"mobile_editor_{width}_verified.png")
            page.screenshot(path=sc_path, full_page=False)
            print(f"  -> PASS: Captured verified screenshot at: {sc_path}")

            # Check 3: Click delete button on first thumbnail
            initial_deleted_count = page.evaluate("() => window.Editor.deletedPhotoIds.length")
            assert initial_deleted_count == 0

            print("  -> Clicking remove button on first existing photo...")
            remove_btns.first.click()
            time.sleep(0.5)

            new_thumbs_count = page.locator("#editor-previews-grid .preview-thumb-box").count()
            assert new_thumbs_count == thumbs_count - 1, f"Expected {thumbs_count - 1} thumbs after deletion, got {new_thumbs_count}"

            updated_deleted_ids = page.evaluate("() => window.Editor.deletedPhotoIds")
            assert len(updated_deleted_ids) == 1, f"Expected 1 ID in deletedPhotoIds, got {updated_deleted_ids}"
            print(f"  -> PASS: Thumbnail removed from UI and ID {updated_deleted_ids[0]} tracked in deletedPhotoIds!")

            # Close editor
            page.locator("#editor-close-btn").click()
            time.sleep(0.5)
            context.close()

        browser.close()

    print("\n=================================================================")
    print("  TAT CA TEST PLAYWRIGHT MOBILE GIAO DIEN & ANH: PASS 100%! 🌸✨")
    print("=================================================================")

if __name__ == "__main__":
    test_mobile_editor()
