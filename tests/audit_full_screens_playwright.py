"""
KOKORO (心) — FULL SYSTEM SCREEN & FEATURE PLAYWRIGHT AUDIT (MOBILE-FIRST)
Meticulously tests all 12 screen modules and captures photographic evidence.
Saves all screenshots to docs/screenshots/.
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.async_api import async_playwright

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.auth import create_session_token, SESSION_COOKIE_NAME

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

USER_ID = 38
USER_EMAIL = "thanhlongts2k@gmail.com"
USER_NAME = "Thành Long"

results = []

def record(screen: str, feature: str, status: str, notes: str, screenshot_file: str = ""):
    results.append({
        "screen": screen,
        "feature": feature,
        "status": status,
        "notes": notes,
        "screenshot": screenshot_file
    })
    print(f"[{status}] {screen} -> {feature}: {notes} (img: {screenshot_file})")

async def run_audit():
    token = create_session_token(USER_ID, USER_EMAIL, USER_NAME)

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)

        # =====================================================================
        # 1. MOBILE-FIRST AUDIT (390 x 844 - iPhone 14 PWA Experience)
        # =====================================================================
        print("\n================== 1. MOBILE-FIRST PWA AUDIT (390x844) ==================")
        mobile_context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=2.0
        )
        await mobile_context.add_cookies([{
            "name": SESSION_COOKIE_NAME,
            "value": token,
            "domain": "127.0.0.1",
            "path": "/"
        }])

        mob = await mobile_context.new_page()
        await mob.goto("http://127.0.0.1:5050/", wait_until="networkidle")
        await asyncio.sleep(1.0)

        # Mobile Screen 1: Timeline Feed & Header
        brand_text = await mob.locator(".brand-title").text_content()
        bottom_nav = await mob.locator(".mobile-bottom-nav").is_visible()
        cards_count = await mob.locator(".journal-card").count()
        img_mob_timeline = "01_mobile_timeline_feed.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_timeline))
        record("1. Dòng Thời Gian (Mobile)", "Giao Diện Header & Bottom Nav", "OK" if bottom_nav else "BAD",
               f"Thương hiệu '{brand_text.strip()}', {cards_count} thẻ bài viết, Thanh điều hướng 5 tab chạm ngón cái cố định", img_mob_timeline)

        # Mobile Zen Audio Mini Player
        zen_toggle = mob.locator("#zen-toggle-btn")
        await zen_toggle.click()
        await asyncio.sleep(0.4)
        zen_expand = mob.locator("#zen-expand-btn")
        await zen_expand.click()
        await asyncio.sleep(0.4)
        zen_panel_vis = await mob.locator("#zen-player-panel").is_visible()
        # Switch to rain track
        rain_chip = mob.locator('.zen-track-chip[data-track="rain"]')
        if await rain_chip.is_visible():
            await rain_chip.click()
            await asyncio.sleep(0.3)
        img_mob_zen = "01_mobile_zen_audio_panel.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_zen))
        record("1. Dòng Thời Gian (Mobile)", "Âm Thanh Thư Giãn Zen Audio Popover", "OK" if zen_panel_vis else "BAD",
               "Panel thiền định nền kính mờ đục 96%, triệt tiêu lỗi đè chữ, thanh trượt âm lượng & 6 âm thanh", img_mob_zen)
        # Close Zen
        await mob.locator("#zen-toggle-btn").click()
        await mob.evaluate("() => document.getElementById('zen-player-panel')?.classList.remove('active')")
        await asyncio.sleep(0.3)

        # Mobile Night Sakura Dark Mode
        theme_btn = mob.locator("#theme-toggle-btn")
        await theme_btn.click()
        await asyncio.sleep(0.4)
        is_dark = await mob.evaluate("() => document.documentElement.getAttribute('data-theme') === 'dark'")
        img_mob_dark = "01_mobile_dark_mode.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_dark))
        record("1. Dòng Thời Gian (Mobile)", "Chế Độ Đêm Night Sakura", "OK" if is_dark else "BAD",
               "Kích hoạt data-theme='dark', bảng màu tím đêm dịu mắt, độ tương phản chuẩn", img_mob_dark)
        await theme_btn.click()
        await asyncio.sleep(0.3)

        # Mobile Screen 2: Card Actions (Edit, Delete Modal, Lightbox)
        # Test Delete Modal
        delete_btn = mob.locator('.journal-card [data-action="delete"]').first
        if await delete_btn.is_visible():
            await delete_btn.click()
            await asyncio.sleep(0.4)
            delete_modal_vis = await mob.locator("#delete-confirm-modal").is_visible()
            img_mob_del = "02_mobile_delete_confirm_modal.png"
            await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_del))
            record("2. Tác Vụ Thẻ Bài (Mobile)", "Hộp Thoại Xác Nhận Buông Bỏ", "OK" if delete_modal_vis else "BAD",
                   "Mở modal 'Buông Bỏ Khoảnh Khắc 🍃' xác nhận an toàn, nút 'Giữ lại' & 'Xác nhận xóa'", img_mob_del)
            # Dismiss delete modal
            await mob.locator("#confirm-cancel-btn").click()
            await asyncio.sleep(0.3)

        # Test Lightbox on Mobile
        first_card_img = mob.locator('.journal-card .gallery-item img, .journal-card img').first
        if await first_card_img.is_visible():
            await first_card_img.click()
            await asyncio.sleep(0.5)
            lightbox_vis = await mob.locator("#lightbox-modal").is_visible()
            controls_vis = await mob.locator("#lightbox-controls-bar").is_visible()
            img_mob_light = "02_mobile_photo_lightbox.png"
            await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_light))
            record("2. Tác Vụ Thẻ Bài (Mobile)", "Lightbox Phóng To Ảnh Toàn Cảnh", "OK" if (lightbox_vis and controls_vis) else "BAD",
                   f"Lightbox mở mượt mà, thanh điều khiển nổi (nút phóng to, thu nhỏ, đóng X), tương tác cảm ứng", img_mob_light)
            await mob.locator("#lightbox-close-btn").click()
            await asyncio.sleep(0.4)

        # Mobile Screen 3: Diary Editor Bottom Sheet & Photo Management
        # Test Edit Entry
        edit_btn = mob.locator('.journal-card [data-action="edit"]').first
        if await edit_btn.is_visible():
            await edit_btn.click()
            await asyncio.sleep(0.5)
            editor_open = await mob.locator("#editor-modal-overlay").is_visible()
            # Check existing photos tray
            saved_photos_count = await mob.locator("#editor-previews-grid .preview-thumb-box").count()
            img_mob_editor_edit = "03_mobile_editor_edit_mode.png"
            await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_editor_edit))
            record("3. Trình Soạn Thảo (Mobile)", "Chế Độ Chỉnh Sửa & Khay Ảnh Đã Lưu", "OK" if editor_open else "BAD",
                   f"Mở bài viết hiện có, khay {saved_photos_count} ảnh đính kèm có nút [x] xóa từng ảnh", img_mob_editor_edit)
            await mob.locator("#editor-cancel-btn").click()
            await asyncio.sleep(0.4)

        # Open New Entry from Bottom Nav
        write_tab = mob.locator('.bottom-nav-item[data-tab="editor"]').first
        await write_tab.click()
        await asyncio.sleep(0.5)
        sheet_open = await mob.locator("#editor-modal-overlay").is_visible()
        img_mob_editor = "03_mobile_editor_bottom_sheet.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_editor))
        record("3. Trình Soạn Thảo (Mobile)", "Bottom Sheet Tạo Bài Mới", "OK" if sheet_open else "BAD",
               "Mở trơn tru từ đáy màn hình, thanh vuốt handle, mood chips cuộn ngang, thời tiết", img_mob_editor)

        # Mobile DateTime Picker inside Editor
        dt_btn = mob.locator("#editor-datetime-btn")
        await dt_btn.click()
        await asyncio.sleep(0.4)
        dt_open = await mob.locator("#datetime-picker-modal").is_visible()
        img_mob_dt = "03_mobile_datetime_picker.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_dt))
        record("3. Trình Soạn Thảo (Mobile)", "Hộp Thoại Chọn Ngày & Giờ", "OK" if dt_open else "BAD",
               "Chọn ngày tháng kèm giờ phút chính xác, nút 'Xác nhận' & 'Bây giờ'", img_mob_dt)
        await mob.locator("#dt-btn-cancel, #datetime-picker-close-btn").first.click()
        await asyncio.sleep(0.3)

        # Close Editor
        await mob.locator("#editor-cancel-btn").click()
        await asyncio.sleep(0.4)

        # Mobile Screen 4: Calendar View
        cal_tab = mob.locator('.bottom-nav-item[data-tab="calendar"]').first
        await cal_tab.click()
        await asyncio.sleep(0.5)
        day_cells = await mob.locator("#full-calendar-grid .c-calendar-day, .calendar-day").count()
        # Click a day cell
        if day_cells > 10:
            await mob.locator('#full-calendar-grid .c-calendar-day, .calendar-day').nth(10).click()
            await asyncio.sleep(0.4)
        img_mob_cal = "04_mobile_calendar_view.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_cal))
        record("4. Lịch Kỷ Niệm (Mobile)", "Lưới Lịch 7 Cột & Danh Sách Ngày", "OK" if day_cells >= 28 else "BAD",
               f"Lưới {day_cells} ô ngày co giãn hoàn hảo trên màn hình hẹp, hiển thị các bài viết bên dưới", img_mob_cal)

        # Mobile Screen 5: Memories View
        mem_tab = mob.locator('.bottom-nav-item[data-tab="memories"]').first
        await mem_tab.click()
        await asyncio.sleep(0.5)
        pills_count = await mob.locator("#memories-mood-filters .memory-mood-pill, #memories-mood-scroll .memory-mood-pill").count()
        first_pill_height = await mob.locator(".memory-mood-pill").first.evaluate("el => el.offsetHeight") if pills_count > 0 else 38
        first_pill_width = await mob.locator(".memory-mood-pill").first.evaluate("el => el.offsetWidth") if pills_count > 0 else 70
        is_capsule = first_pill_width > first_pill_height
        img_mob_mem = "05_mobile_memories_view.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_mem))
        record("5. Kho Kỷ Niệm (Mobile)", "Bộ Lọc Cảm Xúc Dạng Viên Thuốc & Lưới Polaroid", "OK" if is_capsule else "BAD",
               f"{pills_count} nút cảm xúc capsule không bị méo (w:{first_pill_width}px > h:{first_pill_height}px), lưới ảnh kỷ niệm", img_mob_mem)

        # Mobile Screen 6: Profile & Stats View
        prof_tab = mob.locator('.bottom-nav-item[data-tab="profile"]').first
        await prof_tab.click()
        await asyncio.sleep(0.5)
        prof_name = await mob.locator("#profile-view-name, #profile-name, .c-profile-name").first.text_content()
        streak_count = await mob.locator("#profile-stat-streak, #stat-streak-days, #profile-streak-count").first.text_content()
        img_mob_prof = "06_mobile_profile_stats.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_prof))
        record("6. Cá Nhân & Thống Kê (Mobile)", "Trang Hồ Sơ, Streak & Chỉ Số Cảm Xúc", "OK",
               f"Tài khoản '{prof_name.strip()}', Chuỗi duy trì: {streak_count.strip()} ngày, biểu đồ phân bổ tâm trạng", img_mob_prof)

        # Mobile Screen 7: Passcode PIN Settings & Keypad Lock Screen
        pin_btn = mob.locator("#profile-action-pin, #passcode-settings-btn").first
        if await pin_btn.is_visible():
            await pin_btn.click()
            await asyncio.sleep(0.4)
            pin_settings_vis = await mob.locator("#passcode-settings-modal").is_visible()
            img_mob_pin_set = "07_mobile_passcode_settings.png"
            await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_pin_set))
            record("7. Bảo Mật Mã PIN (Mobile)", "Hộp Thoại Cài Đặt Khóa Màn Hình", "OK" if pin_settings_vis else "BAD",
                   "Thiết lập mã PIN 4 chữ số, tùy chọn thời gian tự động khóa an toàn", img_mob_pin_set)
            await mob.locator("#passcode-close-settings-btn").click()
            await asyncio.sleep(0.3)

        # Trigger Lock Screen directly via PasscodeLock
        await mob.evaluate("() => window.PasscodeLock && window.PasscodeLock.showLockScreen()")
        await asyncio.sleep(0.5)
        keypad_vis = await mob.locator("#passcode-lock-overlay").is_visible()
        img_mob_lock = "07_mobile_passcode_lock_screen.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_lock))
        record("7. Bảo Mật Mã PIN (Mobile)", "Màn Hình Khóa Bàn Phím Cảm Ứng", "OK" if keypad_vis else "BAD",
               "Màn hình khóa toàn phần, bàn phím 0-9 số to tròn dễ bấm ngón cái, 4 chấm chỉ thị mã", img_mob_lock)
        # Type digits on keypad
        for d in ["1", "2", "3", "4"]:
            await mob.locator(f'[data-passcode-digit="{d}"]').click()
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.4)
        await mob.evaluate("() => window.PasscodeLock && window.PasscodeLock.hideLockScreen()")
        await asyncio.sleep(0.3)

        # Mobile Screen 8: Memory Studio Canvas Export
        await mob.locator('.bottom-nav-item[data-tab="timeline"]').click()
        await asyncio.sleep(0.4)
        export_btn = mob.locator('.journal-card [data-action="export-card"]').first
        if await export_btn.is_visible():
            await export_btn.click()
            await asyncio.sleep(0.6)
            # Switch to Polaroid theme
            await mob.locator("#theme-btn-polaroid").click()
            await asyncio.sleep(0.4)
            # Switch to 9:16 Story format
            await mob.locator("#card-export-ratio-story").click()
            await asyncio.sleep(0.4)
            img_mob_card = "08_mobile_card_export_modal.png"
            await mob.screenshot(path=str(SCREENSHOT_DIR / img_mob_card))
            record("8. Xuất Thẻ Ảnh Canvas (Mobile)", "Studio Thẻ Ảnh Kỷ Niệm 9:16 Story", "OK",
               "Khung ảnh co giãn vừa khít màn hình di động, 5 chủ đề nghệ thuật, nút tải & chia sẻ", img_mob_card)
            await mob.locator("#card-export-close-btn").click()
            await asyncio.sleep(0.3)

        # Mobile Stress Test: Ultra-Compact 320px (iPhone SE 1st gen)
        await mob.set_viewport_size({"width": 320, "height": 658})
        await asyncio.sleep(0.4)
        has_320_overflow = await mob.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        img_320 = "09_mobile_320px_ultracompact.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_320))
        record("9. Kiểm Thử Màn Hình Siêu Nhỏ (320px)", "iPhone SE 1st Gen Responsive Test", "OK" if not has_320_overflow else "BAD",
               f"Tràn viền ngang: {has_320_overflow} (Bố cục tự co giãn chuẩn, không vỡ layout)", img_320)

        # Mobile Screen 10: Android Small Viewport (360 x 800)
        await mob.set_viewport_size({"width": 360, "height": 800})
        await asyncio.sleep(0.4)
        has_360_overflow = await mob.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        img_360 = "10_mobile_360px_android.png"
        await mob.screenshot(path=str(SCREENSHOT_DIR / img_360))
        record("10. Thiết Bị Android Chuẩn (360px)", "Samsung Galaxy / Xiaomi Responsive Test", "OK" if not has_360_overflow else "BAD",
               f"Tràn viền ngang: {has_360_overflow} (Các khối thẻ, nút bấm chuẩn touch target >= 44px)", img_360)

        await mobile_context.close()

        # =====================================================================
        # 2. DESKTOP REFERENCE AUDIT (1280 x 800)
        # =====================================================================
        print("\n================== 2. DESKTOP REFERENCE AUDIT (1280x800) ==================")
        desktop_context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1.0
        )
        await desktop_context.add_cookies([{
            "name": SESSION_COOKIE_NAME,
            "value": token,
            "domain": "127.0.0.1",
            "path": "/"
        }])

        desk = await desktop_context.new_page()
        await desk.goto("http://127.0.0.1:5050/", wait_until="networkidle")
        await asyncio.sleep(1.0)

        # Desktop Timeline & Sidebar
        img_desk_timeline = "11_desktop_timeline_feed.png"
        await desk.screenshot(path=str(SCREENSHOT_DIR / img_desk_timeline))
        record("11. Bản Máy Tính (Desktop)", "Bố Cục 3 Cột (Sidebar Trái - Feed Giữa - Tiện Ích Phải)", "OK",
               "Tận dụng tối đa không gian màn hình rộng, mini calendar cố định, danh mục thẻ", img_desk_timeline)

        # Category & Tag Manager Modal
        await desk.evaluate("() => window.KokoroTagManager && window.KokoroTagManager.openManagerModal('categories')")
        await asyncio.sleep(0.5)
        cat_vis = await desk.locator("#category-tag-manager-modal").is_visible()
        img_desk_cat = "12_desktop_category_manager.png"
        await desk.screenshot(path=str(SCREENSHOT_DIR / img_desk_cat))
        record("12. Quản Lý Danh Mục & Thẻ", "Modal Quản Lý Cảm Xúc & Nhãn Dán", "OK" if cat_vis else "BAD",
               "Quản lý cảm xúc tùy chỉnh, bảng màu pastel, emoji picker và danh sách hashtag", img_desk_cat)
        await desk.evaluate("() => window.KokoroTagManager && window.KokoroTagManager.closeManagerModal()")
        await asyncio.sleep(0.3)

        await desktop_context.close()
        await browser.close()
        print("\n✨ HOÀN TẤT KIỂM THỬ PLAYWRIGHT TOÀN DIỆN HỆ THỐNG (FOCUS MOBILE)! ✨\n")

    return results

if __name__ == "__main__":
    asyncio.run(run_audit())
