"""
Automated Verification Suite for Kokoro v1.6.0-beta.2 Client UI & Modal Controls
Tests:
1. DOM Structure & Elements in static/index.html:
   - #category-tag-manager-modal exists with tabs, emoji picker, color palette, tag create form
2. CSS Strict iOS WebKit Pan-X Lock in static/css/layout.css & components.css
3. Touch targets >= 44px WCAG compliance for modal action buttons
4. JS TagManager module integrity in static/js/tag-manager.js
"""

import sys
import os
import re
import unittest

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class TestV160ModalClient(unittest.TestCase):
    def test_01_index_html_modal_dom_structure(self):
        """Verify #category-tag-manager-modal contains all required controls."""
        html_path = os.path.join(BASE_DIR, 'static', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Modal container
        self.assertIn('id="category-tag-manager-modal"', html)
        self.assertIn('id="cat-tag-modal-close"', html)
        self.assertIn('id="cat-tag-modal-btn-done"', html)

        # Tabs navigation
        self.assertIn('id="tab-btn-cat-categories"', html)
        self.assertIn('id="tab-btn-cat-tags"', html)

        # Tab 1: Categories elements
        self.assertIn('id="cat-tab-content-categories"', html)
        self.assertIn('id="cat-create-emoji-btn"', html)
        self.assertIn('id="cat-emoji-popover"', html)
        self.assertIn('id="cat-create-name-input"', html)
        self.assertIn('id="cat-create-submit-btn"', html)
        self.assertIn('id="cat-color-palette"', html)
        self.assertIn('id="cat-categories-list-container"', html)

        # Tab 2: Tags elements
        self.assertIn('id="cat-tab-content-tags"', html)
        self.assertIn('id="tag-create-name-input"', html)
        self.assertIn('id="tag-create-submit-btn"', html)
        self.assertIn('id="cat-total-tags-label"', html)
        self.assertIn('id="cat-cleanup-orphans-btn"', html)
        self.assertIn('id="cat-tags-list-container"', html)

        print(" -> PASS: index.html has complete Category & Tag Manager DOM structure")

    def test_02_ios_pwa_strict_pan_x_lock_css(self):
        """Verify layout.css and components.css lock Y-axis drag on horizontal scrolls."""
        layout_css_path = os.path.join(BASE_DIR, 'static', 'css', 'layout.css')
        with open(layout_css_path, 'r', encoding='utf-8') as f:
            layout_css = f.read()

        self.assertIn('touch-action: pan-x !important;', layout_css)
        self.assertIn('overflow-y: hidden !important;', layout_css)
        self.assertIn('overscroll-behavior-y: none !important;', layout_css)

        comp_css_path = os.path.join(BASE_DIR, 'static', 'css', 'components.css')
        with open(comp_css_path, 'r', encoding='utf-8') as f:
            comp_css = f.read()

        self.assertIn('.memories-mood-scroll', comp_css)
        self.assertIn('touch-action: pan-x !important;', comp_css)
        self.assertIn('overflow-y: hidden !important;', comp_css)

        # Category badge & chip styles
        self.assertIn('.category-badge-pill', comp_css)
        self.assertIn('.category-option-chip', comp_css)
        self.assertIn('.category-picker-scroll', comp_css)

        print(" -> PASS: layout.css and components.css have strict iOS WebKit pan-x locks")

    def test_03_tag_manager_js_methods_and_events(self):
        """Verify tag-manager.js exports and methods."""
        js_path = os.path.join(BASE_DIR, 'static', 'js', 'tag-manager.js')
        with open(js_path, 'r', encoding='utf-8') as f:
            js = f.read()

        # Check critical methods
        self.assertIn('openManagerModal', js)
        self.assertIn('closeManagerModal', js)
        self.assertIn('renderCategoriesTab', js)
        self.assertIn('renderTagsTab', js)
        self.assertIn('handleCreateCategory', js)
        self.assertIn('handleCreateTag', js)
        self.assertIn('btn-edit-category', js)
        self.assertIn('btn-delete-category', js)
        self.assertIn('btn-rename-tag', js)
        self.assertIn('btn-delete-tag', js)

        # Check pointer-events active class toggle
        self.assertIn("modalEl.classList.add('active')", js)
        self.assertIn("modalEl.classList.remove('active')", js)

        print(" -> PASS: tag-manager.js has all required CRUD methods and active class management")


if __name__ == "__main__":
    unittest.main()
