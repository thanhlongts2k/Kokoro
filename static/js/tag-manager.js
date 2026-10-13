/**
 * KOKORO (心) — TAG MANAGEMENT MODULE
 * Architecture: Clean Component, decoupled from editor & app coordinators.
 * Features: Tag normalization, editor quick suggestion chips, sidebar popular tags widget.
 */

/**
 * Global Soft Sakura Dialog Engine (SSoT for Async Modals)
 * Provides Promise-based confirm() and prompt() dialogs with zero native browser popups.
 */
window.KokoroDialog = {
  confirm({
    title = 'Xác nhận 🌸',
    message = '',
    confirmText = 'Đồng ý',
    cancelText = 'Hủy bỏ',
    isDanger = false,
    icon = 'bi-flower1'
  } = {}) {
    return new Promise((resolve) => {
      const modal = document.getElementById('generic-confirm-modal');
      const titleEl = document.getElementById('generic-confirm-title');
      const msgEl = document.getElementById('generic-confirm-message');
      const okBtn = document.getElementById('generic-confirm-ok-btn');
      const cancelBtn = document.getElementById('generic-confirm-cancel-btn');
      const iconEl = document.getElementById('generic-confirm-icon');

      if (!modal) {
        resolve(window.confirm(message));
        return;
      }

      if (titleEl) titleEl.textContent = title;
      if (msgEl) msgEl.textContent = message;
      if (iconEl) iconEl.className = `bi ${icon}`;
      if (okBtn) {
        okBtn.innerHTML = isDanger ? `<i class="bi bi-trash3"></i> ${confirmText}` : `<i class="bi bi-check-lg"></i> ${confirmText}`;
        if (isDanger) {
          okBtn.style.background = 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)';
        } else {
          okBtn.style.background = '';
        }
      }
      if (cancelBtn) cancelBtn.textContent = cancelText;

      const onKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onCancel();
        }
      };

      const cleanup = () => {
        modal.classList.remove('active');
        if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(false);
        okBtn.removeEventListener('click', onOk);
        cancelBtn.removeEventListener('click', onCancel);
        modal.removeEventListener('click', onBackdrop);
        window.removeEventListener('keydown', onKeyDown);
      };

      const onOk = () => {
        cleanup();
        resolve(true);
      };

      const onCancel = () => {
        cleanup();
        resolve(false);
      };

      const onBackdrop = (e) => {
        if (e.target === modal) {
          cleanup();
          resolve(false);
        }
      };

      okBtn.addEventListener('click', onOk);
      cancelBtn.addEventListener('click', onCancel);
      modal.addEventListener('click', onBackdrop);
      window.addEventListener('keydown', onKeyDown);

      if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(true);
      modal.classList.add('active');
      cancelBtn?.focus();
    });
  },

  prompt({
    title = 'Nhập thông tin ✨',
    message = '',
    defaultValue = '',
    placeholder = 'Nhập nội dung...',
    label = 'Tên:',
    extraValue = '',
    extraLabel = 'Biểu tượng icon:',
    showExtra = false,
    confirmText = 'Xác nhận',
    cancelText = 'Hủy bỏ'
  } = {}) {
    return new Promise((resolve) => {
      const modal = document.getElementById('generic-prompt-modal');
      const titleEl = document.getElementById('generic-prompt-title');
      const msgEl = document.getElementById('generic-prompt-message');
      const labelEl = document.getElementById('generic-prompt-label');
      const inputEl = document.getElementById('generic-prompt-input');
      const extraGroup = document.getElementById('generic-prompt-extra-group');
      const extraLabelEl = document.getElementById('generic-prompt-extra-label');
      const extraInputEl = document.getElementById('generic-prompt-extra-input');
      const okBtn = document.getElementById('generic-prompt-ok-btn');
      const cancelBtn = document.getElementById('generic-prompt-cancel-btn');

      if (!modal) {
        const val = window.prompt(title, defaultValue);
        resolve(val !== null ? { value: val, extra: extraValue } : null);
        return;
      }

      if (titleEl) titleEl.textContent = title;
      if (msgEl) {
        msgEl.textContent = message;
        msgEl.style.display = message ? 'block' : 'none';
      }
      if (labelEl) labelEl.textContent = label;
      if (inputEl) {
        inputEl.value = defaultValue;
        inputEl.placeholder = placeholder;
      }
      if (extraGroup) {
        extraGroup.style.display = showExtra ? 'block' : 'none';
        if (extraLabelEl) extraLabelEl.textContent = extraLabel;
        if (extraInputEl) extraInputEl.value = extraValue;
      }
      if (okBtn) okBtn.innerHTML = `<i class="bi bi-check2"></i> ${confirmText}`;
      if (cancelBtn) cancelBtn.textContent = cancelText;

      const onKeyDown = (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onCancel();
        }
      };

      const cleanup = () => {
        modal.classList.remove('active');
        if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(false);
        okBtn.removeEventListener('click', onOk);
        cancelBtn.removeEventListener('click', onCancel);
        modal.removeEventListener('click', onBackdrop);
        window.removeEventListener('keydown', onKeyDown);
        if (inputEl) inputEl.removeEventListener('keydown', onKey);
      };

      const onOk = () => {
        const val = inputEl ? inputEl.value.trim() : '';
        const extra = (showExtra && extraInputEl) ? extraInputEl.value.trim() : '';
        cleanup();
        resolve({ value: val, extra });
      };

      const onCancel = () => {
        cleanup();
        resolve(null);
      };

      const onBackdrop = (e) => {
        if (e.target === modal) {
          cleanup();
          resolve(null);
        }
      };

      const onKey = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onOk();
        }
      };

      okBtn.addEventListener('click', onOk);
      cancelBtn.addEventListener('click', onCancel);
      modal.addEventListener('click', onBackdrop);
      window.addEventListener('keydown', onKeyDown);
      if (inputEl) inputEl.addEventListener('keydown', onKey);

      if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(true);
      modal.classList.add('active');
      setTimeout(() => {
        if (inputEl) {
          inputEl.focus();
          inputEl.select();
        }
      }, 50);
    });
  }
};

const KokoroTagManager = (() => {
  let cachedTags = [];

  const notify = (msg, type = 'info') => {
    if (window.KokoroApp && typeof window.KokoroApp.showToast === 'function') {
      window.KokoroApp.showToast(msg, type);
    } else if (window.KokoroToast && typeof window.KokoroToast.show === 'function') {
      window.KokoroToast.show(msg, type);
    }
  };

  /**
   * Parse space-separated tags from input string into normalized array
   * @param {string} inputVal
   * @returns {string[]}
   */
  const parseTagsFromInput = (inputVal) => {
    if (!inputVal) return [];
    return String(inputVal)
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .map((t) => (t.startsWith('#') ? t : `#${t}`).toLowerCase());
  };

  /**
   * Ensure a tag has a leading #
   * @param {string} tag
   * @returns {string}
   */
  const normalizeTag = (tag) => {
    if (!tag) return '';
    const clean = String(tag).trim();
    return clean.startsWith('#') ? clean : `#${clean}`;
  };

  /**
   * Toggle a tag inside the input element value
   * @param {HTMLInputElement} inputEl
   * @param {string} tagWithHash
   */
  const toggleTagInInput = (inputEl, tagWithHash) => {
    if (!inputEl) return;
    const currentRaw = inputEl.value.trim();
    let tags = currentRaw ? currentRaw.split(/\s+/).filter(Boolean) : [];
    const targetNormalized = normalizeTag(tagWithHash);
    const targetLower = targetNormalized.toLowerCase();
    const existingIndex = tags.findIndex((t) => normalizeTag(t).toLowerCase() === targetLower);

    if (existingIndex >= 0) {
      tags.splice(existingIndex, 1);
    } else {
      tags.push(targetNormalized);
    }

    inputEl.value = tags.join(' ');
  };

  /**
   * Synchronize .selected class on quick chips based on input value
   * @param {HTMLElement} containerEl
   * @param {HTMLInputElement} inputEl
   */
  const updateSuggestedChipsSelection = (containerEl, inputEl) => {
    if (!containerEl || !inputEl) return;
    const selected = parseTagsFromInput(inputEl.value);
    const chips = containerEl.querySelectorAll('.tag-quick-chip');
    chips.forEach((chip) => {
      const tag = (chip.dataset.tag || '').toLowerCase();
      chip.classList.toggle('selected', selected.includes(tag));
    });
  };

  /**
   * Fetch user tags from API and render Quick Chips in the Editor modal
   * @param {HTMLElement} containerEl
   * @param {HTMLInputElement} inputEl
   * @param {Function} onTagChangedCallback
   */
  const loadSuggestedChips = async (containerEl, inputEl, onTagChangedCallback) => {
    if (!containerEl) return;
    try {
      if (!window.KokoroAPI) return;
      const res = await window.KokoroAPI.getTags();
      if (res && res.status === 'success' && Array.isArray(res.tags)) {
        cachedTags = res.tags;
        if (cachedTags.length === 0) {
          containerEl.innerHTML = '';
          return;
        }

        const currentSelected = parseTagsFromInput(inputEl ? inputEl.value : '');
        containerEl.innerHTML = cachedTags.map((t) => {
          const cleanName = normalizeTag(t.name);
          const safeCleanName = window.escapeHtml(cleanName);
          const isSelected = currentSelected.includes(cleanName.toLowerCase());
          return `
            <span class="tag-quick-chip ${isSelected ? 'selected' : ''}" data-tag="${safeCleanName}" title="Gắn thẻ ${safeCleanName} (${t.usage_count} bài viết)">
              ${safeCleanName} <span class="tag-quick-chip-count">(${t.usage_count})</span>
            </span>
          `;
        }).join('');

        containerEl.querySelectorAll('.tag-quick-chip').forEach((chip) => {
          chip.addEventListener('click', (e) => {
            e.preventDefault();
            const tag = chip.dataset.tag;
            if (tag) {
              toggleTagInInput(inputEl, tag);
              updateSuggestedChipsSelection(containerEl, inputEl);
              if (typeof onTagChangedCallback === 'function') {
                onTagChangedCallback();
              }
            }
            if (e.currentTarget && typeof e.currentTarget.blur === 'function') {
              e.currentTarget.blur();
            }
          });
        });
      }
    } catch (err) {
      console.warn('[KokoroTagManager] Không thể tải gợi ý thẻ:', err);
    }
  };

  /**
   * Public helper to synchronize chip selection states based on input text
   * @param {HTMLElement} containerEl
   * @param {HTMLInputElement} inputEl
   */
  const syncChipStates = (containerEl, inputEl) => {
    updateSuggestedChipsSelection(containerEl, inputEl);
  };

  /**
   * Fetch and render dynamic Popular Tags widget in Desktop Sidebar
   * @param {HTMLElement} containerEl
   * @param {string|null} activeFilter
   * @param {Function} onSelectTagCallback
   */
  const loadPopularTags = async (containerEl, activeFilter, onSelectTagCallback) => {
    if (!containerEl) return;
    try {
      if (!window.KokoroAPI) return;
      const res = await window.KokoroAPI.getTags();
      if (res && res.status === 'success' && Array.isArray(res.tags)) {
        cachedTags = res.tags;
        if (cachedTags.length === 0) {
          containerEl.innerHTML = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Chưa có thẻ chủ đề nào 🍃</span>`;
          return;
        }

        containerEl.innerHTML = cachedTags.map((t) => {
          const cleanName = normalizeTag(t.name);
          const safeCleanName = window.escapeHtml(cleanName);
          const isActive = activeFilter && activeFilter.toLowerCase() === cleanName.toLowerCase();
          return `
            <span class="tag-pill ${isActive ? 'active' : ''}" data-tag="${safeCleanName}" title="Lọc theo thẻ ${safeCleanName} (${t.usage_count} bài viết)">
              ${safeCleanName} <span class="tag-count">(${t.usage_count})</span>
            </span>
          `;
        }).join('');

        containerEl.querySelectorAll('.tag-pill').forEach((pill) => {
          pill.addEventListener('click', (e) => {
            e.preventDefault();
            const tag = pill.dataset.tag;
            if (tag && typeof onSelectTagCallback === 'function') {
              onSelectTagCallback(tag);
            }
          });
        });
      }
    } catch (err) {
      console.warn('[KokoroTagManager] Không thể tải danh sách thẻ chủ đề:', err);
    }
  };

  // =========================================================================
  // CATEGORY & TAG MANAGER MODAL (V1.5.5)
  // =========================================================================
  // =========================================================================
  // CATEGORY & TAG MANAGER MODAL (V1.6.0)
  // =========================================================================
  let modalEl = null;
  let tabCategoriesBtn = null;
  let tabTagsBtn = null;
  let contentCategoriesEl = null;
  let contentTagsEl = null;
  let categoriesListContainer = null;
  let tagsListContainer = null;
  let totalTagsLabel = null;
  let cleanupOrphansBtn = null;
  let currentActiveTab = 'categories';

  // Category creation form state
  let selectedCategoryEmoji = '🌸';
  let selectedCategoryColor = '#ec4899';
  const AVAILABLE_EMOJIS = ['🌸', '☕', '🌙', '🍵', '⚡', '🥰', '🌈', '🌧️', '🌿', '💼', '💌', '✈️', '📚', '🏠', '💰', '🎨', '🎵', '🧘', '🍳', '⭐'];

  const initModal = () => {
    modalEl = document.getElementById('category-tag-manager-modal');
    if (!modalEl) return;

    tabCategoriesBtn = document.getElementById('tab-btn-cat-categories');
    tabTagsBtn = document.getElementById('tab-btn-cat-tags');
    contentCategoriesEl = document.getElementById('cat-tab-content-categories');
    contentTagsEl = document.getElementById('cat-tab-content-tags');
    categoriesListContainer = document.getElementById('cat-categories-list-container');
    tagsListContainer = document.getElementById('cat-tags-list-container');
    totalTagsLabel = document.getElementById('cat-total-tags-label');
    cleanupOrphansBtn = document.getElementById('cat-cleanup-orphans-btn');

    const closeBtn = document.getElementById('cat-tag-modal-close');
    const doneBtn = document.getElementById('cat-tag-modal-btn-done');

    if (closeBtn) closeBtn.addEventListener('click', () => closeManagerModal());
    if (doneBtn) doneBtn.addEventListener('click', () => closeManagerModal());

    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) closeManagerModal();
    });

    if (tabCategoriesBtn) {
      tabCategoriesBtn.addEventListener('click', () => switchTab('categories'));
    }
    if (tabTagsBtn) {
      tabTagsBtn.addEventListener('click', () => switchTab('tags'));
    }

    // Setup Category Creation Controls
    setupCategoryFormControls();

    // Setup Tag Creation Controls
    setupTagFormControls();

    if (cleanupOrphansBtn) {
      cleanupOrphansBtn.addEventListener('click', async () => {
        const ok = await window.KokoroDialog.confirm({
          title: 'Dọn Dẹp Thẻ Mồ Côi 🍃',
          message: 'Bạn có chắc muốn dọn dẹp toàn bộ các thẻ chưa gắn với bài viết nào (0 bài)?',
          confirmText: 'Dọn dẹp ngay',
          isDanger: true,
          icon: 'bi-stars'
        });
        if (!ok) return;

        try {
          const res = await window.KokoroAPI.cleanupOrphanTags();
          if (res && res.status === 'success') {
            notify(res.message || 'Đã dọn dẹp thẻ mồ côi thành công! 🌸', 'success');
            await renderTagsTab();
            if (window.KokoroApp) await window.KokoroApp.loadPopularTags();
          }
        } catch (err) {
          notify('Lỗi dọn dẹp: ' + err.message, 'error');
        }
      });
    }

    // Attach to profile view trigger button
    const profileBtn = document.getElementById('profile-action-category-tags');
    if (profileBtn) {
      profileBtn.addEventListener('click', () => openManagerModal('categories'));
    }
  };

  const setupCategoryFormControls = () => {
    const emojiBtn = document.getElementById('cat-create-emoji-btn');
    const emojiPopover = document.getElementById('cat-emoji-popover');
    const selectedEmojiSpan = document.getElementById('cat-create-selected-emoji');
    const nameInput = document.getElementById('cat-create-name-input');
    const submitBtn = document.getElementById('cat-create-submit-btn');
    const colorSwatches = document.querySelectorAll('.cat-color-swatch');

    // Populate Emoji Popover Grid
    if (emojiPopover) {
      emojiPopover.innerHTML = AVAILABLE_EMOJIS.map(
        (em) => `<button type="button" class="btn-glass" data-emoji="${em}" style="font-size: 20px; padding: 6px; border-radius: var(--radius-sm); border: none; cursor: pointer;">${em}</button>`
      ).join('');

      emojiPopover.querySelectorAll('[data-emoji]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          selectedCategoryEmoji = btn.dataset.emoji;
          if (selectedEmojiSpan) selectedEmojiSpan.textContent = selectedCategoryEmoji;
          emojiPopover.style.display = 'none';
        });
      });
    }

    if (emojiBtn && emojiPopover) {
      emojiBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isShown = emojiPopover.style.display === 'grid';
        emojiPopover.style.display = isShown ? 'none' : 'grid';
      });

      document.addEventListener('click', (e) => {
        if (!emojiBtn.contains(e.target) && !emojiPopover.contains(e.target)) {
          emojiPopover.style.display = 'none';
        }
      });
    }

    // Color Swatches
    colorSwatches.forEach((swatch) => {
      swatch.addEventListener('click', () => {
        colorSwatches.forEach((s) => {
          s.classList.remove('active');
          s.style.outline = 'none';
          s.style.border = 'none';
          s.style.width = '20px';
          s.style.height = '20px';
        });
        swatch.classList.add('active');
        swatch.style.width = '22px';
        swatch.style.height = '22px';
        swatch.style.border = '2px solid #fff';
        swatch.style.outline = `2px solid ${swatch.dataset.color}`;
        selectedCategoryColor = swatch.dataset.color;
      });
    });

    // Create Category Handler
    const handleCreateCategory = async () => {
      if (!nameInput) return;
      const rawName = nameInput.value.trim();
      if (!rawName) {
        notify('Vui lòng nhập tên danh mục 🌸', 'warning');
        nameInput.focus();
        return;
      }

      try {
        const payload = {
          name: rawName,
          icon: selectedCategoryEmoji || '🌸',
          color: selectedCategoryColor || '#ec4899'
        };
        const res = await window.KokoroAPI.createCategory(payload);
        if (res && res.status === 'success') {
          nameInput.value = '';
          notify(`Đã tạo danh mục "${rawName}" thành công! 🌸`, 'success');
          await renderCategoriesTab();
          if (window.Editor && typeof window.Editor.loadCategories === 'function') {
            await window.Editor.loadCategories();
          }
          if (window.KokoroApp && typeof window.KokoroApp.loadCategories === 'function') {
            await window.KokoroApp.loadCategories();
          }
        }
      } catch (err) {
        notify('Lỗi tạo danh mục: ' + err.message, 'error');
      }
    };

    if (submitBtn) {
      submitBtn.addEventListener('click', handleCreateCategory);
    }
    if (nameInput) {
      nameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleCreateCategory();
        }
      });
    }
  };

  const setupTagFormControls = () => {
    const tagNameInput = document.getElementById('tag-create-name-input');
    const tagSubmitBtn = document.getElementById('tag-create-submit-btn');

    const handleCreateTag = async () => {
      if (!tagNameInput) return;
      const rawName = tagNameInput.value.trim();
      if (!rawName) {
        notify('Vui lòng nhập tên thẻ 🏷️', 'warning');
        tagNameInput.focus();
        return;
      }

      try {
        const res = await window.KokoroAPI.createTag(rawName);
        if (res && res.status === 'success') {
          tagNameInput.value = '';
          notify(res.message || `Đã tạo thẻ thành công! 🏷️`, 'success');
          await renderTagsTab();
          if (window.KokoroApp) await window.KokoroApp.loadPopularTags();
        }
      } catch (err) {
        notify('Lỗi tạo thẻ: ' + err.message, 'error');
      }
    };

    if (tagSubmitBtn) {
      tagSubmitBtn.addEventListener('click', handleCreateTag);
    }
    if (tagNameInput) {
      tagNameInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleCreateTag();
        }
      });
    }
  };

  const switchTab = (tab) => {
    currentActiveTab = tab;
    if (tab === 'categories') {
      if (tabCategoriesBtn) tabCategoriesBtn.classList.add('active');
      if (tabTagsBtn) tabTagsBtn.classList.remove('active');
      if (contentCategoriesEl) contentCategoriesEl.style.display = 'flex';
      if (contentTagsEl) contentTagsEl.style.display = 'none';
      renderCategoriesTab();
    } else {
      if (tabCategoriesBtn) tabCategoriesBtn.classList.remove('active');
      if (tabTagsBtn) tabTagsBtn.classList.add('active');
      if (contentCategoriesEl) contentCategoriesEl.style.display = 'none';
      if (contentTagsEl) contentTagsEl.style.display = 'flex';
      renderTagsTab();
    }
  };

  const renderCategoriesTab = async () => {
    if (!categoriesListContainer) return;
    try {
      categoriesListContainer.innerHTML = `<div style="text-align: center; padding: 20px; font-size: 12px; color: var(--text-muted);">Đang tải danh mục... ✨</div>`;
      const res = await window.KokoroAPI.getCategories();
      const categories = (res && res.status === 'success' && Array.isArray(res.categories)) ? res.categories : [];

      if (categories.length === 0) {
        categoriesListContainer.innerHTML = `
          <div style="text-align: center; padding: 30px; font-size: 12.5px; color: var(--text-muted);">
            📁 Chưa có danh mục nào.<br>Tạo danh mục mới ở ô bên trên để bắt đầu sắp xếp bài viết nhé!
          </div>
        `;
        return;
      }

      categoriesListContainer.innerHTML = categories.map((cat) => {
        const safeName = window.escapeHtml(cat.name);
        const safeIcon = window.escapeHtml(cat.icon || '📁');
        const safeColor = window.escapeHtml(cat.color || '#ec4899');
        const usageCount = cat.usage_count || 0;

        return `
          <div class="glass-panel" style="padding: 10px 14px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
              <span class="category-badge-pill" style="--cat-color: ${safeColor}; font-size: 13px; padding: 4px 12px;">
                <span>${safeIcon}</span>
                <span>${safeName}</span>
              </span>
              <span style="font-size: 12px; color: var(--text-muted); white-space: nowrap;">
                ${usageCount} bài viết
              </span>
            </div>
            <div style="display: flex; gap: 6px; flex-shrink: 0;">
              <button type="button" class="action-icon-btn btn-edit-category" data-cat-id="${cat.id}" data-cat-name="${safeName}" data-cat-icon="${safeIcon}" data-cat-color="${safeColor}" style="width: 30px; height: 30px;" title="Chỉnh sửa danh mục">
                <i class="bi bi-pencil" style="font-size: 12px;"></i>
              </button>
              <button type="button" class="action-icon-btn btn-delete-category text-danger" data-cat-id="${cat.id}" data-cat-name="${safeName}" style="width: 30px; height: 30px;" title="Xóa danh mục">
                <i class="bi bi-trash" style="font-size: 12px;"></i>
              </button>
            </div>
          </div>
        `;
      }).join('');

      // Edit Category Handler
      categoriesListContainer.querySelectorAll('.btn-edit-category').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          const catId = e.currentTarget.dataset.catId;
          const oldName = e.currentTarget.dataset.catName;
          const oldIcon = e.currentTarget.dataset.catIcon;
          const oldColor = e.currentTarget.dataset.catColor;

          const promptResult = await window.KokoroDialog.prompt({
            title: 'Chỉnh Sửa Danh Mục ✨',
            message: `Cập nhật thông tin cho danh mục "${oldName}":`,
            defaultValue: oldName,
            placeholder: 'Tên danh mục...',
            label: 'Tên danh mục:',
            showExtra: true,
            extraValue: oldIcon,
            extraLabel: 'Biểu tượng icon:',
            confirmText: 'Lưu thay đổi'
          });
          if (!promptResult) return;

          const trimmedName = promptResult.value.trim();
          if (!trimmedName) {
            notify('Tên danh mục không được để trống.', 'warning');
            return;
          }
          const newIcon = promptResult.extra.trim() || oldIcon;

          try {
            const updateRes = await window.KokoroAPI.updateCategory(catId, {
              name: trimmedName,
              icon: newIcon,
              color: oldColor
            });
            if (updateRes && updateRes.status === 'success') {
              notify(`Đã cập nhật danh mục "${trimmedName}" ✨`, 'success');
              await renderCategoriesTab();
              if (window.Editor && typeof window.Editor.loadCategories === 'function') {
                await window.Editor.loadCategories();
              }
              if (window.KokoroApp && typeof window.KokoroApp.loadCategories === 'function') {
                await window.KokoroApp.loadCategories();
              }
              if (window.KokoroApp) await window.KokoroApp.loadEntries();
            }
          } catch (err) {
            notify('Lỗi cập nhật danh mục: ' + err.message, 'error');
          }
        });
      });

      // Delete Category Handler
      categoriesListContainer.querySelectorAll('.btn-delete-category').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          const catId = e.currentTarget.dataset.catId;
          const catName = e.currentTarget.dataset.catName;
          const ok = await window.KokoroDialog.confirm({
            title: 'Xóa Danh Mục 🌸',
            message: `Bạn có chắc muốn xóa danh mục "${catName}"?\n(Lưu ý: Các bài viết thuộc danh mục này sẽ tự động chuyển về trạng thái Chưa phân loại, bài viết của bạn sẽ được an toàn tuyệt đối).`,
            confirmText: 'Xác nhận xóa',
            isDanger: true,
            icon: 'bi-folder-x'
          });
          if (!ok) return;

          try {
            const delRes = await window.KokoroAPI.deleteCategory(catId);
            if (delRes && delRes.status === 'success') {
              notify(`Đã xóa danh mục "${catName}" thành công 🌸`, 'success');
              await renderCategoriesTab();
              if (window.Editor && typeof window.Editor.loadCategories === 'function') {
                await window.Editor.loadCategories();
              }
              if (window.KokoroApp && typeof window.KokoroApp.loadCategories === 'function') {
                await window.KokoroApp.loadCategories();
              }
              if (window.KokoroApp) await window.KokoroApp.loadEntries();
            }
          } catch (err) {
            notify('Lỗi xóa danh mục: ' + err.message, 'error');
          }
        });
      });

    } catch (e) {
      categoriesListContainer.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center;">Chưa thể tải dữ liệu danh mục.</div>`;
    }
  };

  const renderTagsTab = async () => {
    if (!tagsListContainer) return;
    try {
      tagsListContainer.innerHTML = `<div style="text-align: center; padding: 20px; font-size: 12px; color: var(--text-muted);">Đang tải danh sách thẻ... ✨</div>`;
      const res = await window.KokoroAPI.getTags();
      const tags = (res && res.status === 'success' && Array.isArray(res.tags)) ? res.tags : [];

      if (totalTagsLabel) {
        totalTagsLabel.textContent = `Tổng cộng: ${tags.length} thẻ`;
      }

      if (tags.length === 0) {
        tagsListContainer.innerHTML = `
          <div style="text-align: center; padding: 30px; font-size: 12.5px; color: var(--text-muted);">
            🍃 Bạn chưa có thẻ chủ đề nào.<br>Tạo thẻ mới ở ô bên trên để bắt đầu gắn nhãn bài viết nhé!
          </div>
        `;
        return;
      }

      tagsListContainer.innerHTML = tags.map((t) => {
        const cleanName = normalizeTag(t.name);
        const safeCleanName = window.escapeHtml(cleanName);
        return `
          <div class="glass-panel" style="padding: 10px 14px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
              <span class="tag-quick-chip selected" style="margin: 0; pointer-events: none;">${safeCleanName}</span>
              <span style="font-size: 11.5px; color: var(--text-muted); white-space: nowrap;">${t.usage_count} bài viết</span>
            </div>
            <div style="display: flex; gap: 6px; flex-shrink: 0;">
              <button type="button" class="action-icon-btn btn-rename-tag" data-tag-id="${t.id}" data-tag-name="${safeCleanName}" style="width: 30px; height: 30px;" title="Đổi tên thẻ">
                <i class="bi bi-pencil" style="font-size: 12px;"></i>
              </button>
              <button type="button" class="action-icon-btn btn-delete-tag text-danger" data-tag-id="${t.id}" data-tag-name="${safeCleanName}" style="width: 30px; height: 30px;" title="Xóa thẻ">
                <i class="bi bi-trash" style="font-size: 12px;"></i>
              </button>
            </div>
          </div>
        `;
      }).join('');

      // Rename tag handler
      tagsListContainer.querySelectorAll('.btn-rename-tag').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          const tagId = e.currentTarget.dataset.tagId;
          const oldName = e.currentTarget.dataset.tagName;
          const promptResult = await window.KokoroDialog.prompt({
            title: 'Đổi Tên Thẻ 🏷️',
            message: `Nhập tên mới cho thẻ ${oldName}:`,
            defaultValue: oldName.replace(/^#/, ''),
            placeholder: 'Tên thẻ mới...',
            label: 'Tên thẻ:',
            confirmText: 'Lưu tên mới'
          });
          if (!promptResult) return;

          const trimmed = promptResult.value.trim();
          if (!trimmed) {
            notify('Tên thẻ không được để trống.', 'warning');
            return;
          }

          try {
            const updateRes = await window.KokoroAPI.updateTag(tagId, trimmed);
            if (updateRes && updateRes.status === 'success') {
              notify(`Đã đổi tên thẻ thành #${trimmed.replace(/^#/, '')} ✨`, 'success');
              await renderTagsTab();
              if (window.KokoroApp) {
                await window.KokoroApp.loadEntries();
                await window.KokoroApp.loadPopularTags();
              }
            }
          } catch (err) {
            notify('Lỗi đổi tên thẻ: ' + err.message, 'error');
          }
        });
      });

      // Delete tag handler
      tagsListContainer.querySelectorAll('.btn-delete-tag').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          const tagId = e.currentTarget.dataset.tagId;
          const tagName = e.currentTarget.dataset.tagName;
          const ok = await window.KokoroDialog.confirm({
            title: 'Gỡ Bỏ Thẻ 🏷️',
            message: `Bạn có chắc muốn xóa thẻ ${tagName}? Thẻ sẽ được gỡ khỏi các bài viết liên quan.`,
            confirmText: 'Xác nhận xóa',
            isDanger: true,
            icon: 'bi-tag'
          });
          if (!ok) return;

          try {
            const delRes = await window.KokoroAPI.deleteTag(tagId);
            if (delRes && delRes.status === 'success') {
              notify(`Đã xóa thẻ ${tagName} thành công 🌸`, 'success');
              await renderTagsTab();
              if (window.KokoroApp) {
                await window.KokoroApp.loadEntries();
                await window.KokoroApp.loadPopularTags();
              }
            }
          } catch (err) {
            notify('Lỗi xóa thẻ: ' + err.message, 'error');
          }
        });
      });
    } catch (e) {
      tagsListContainer.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center;">Không thể tải danh sách thẻ.</div>`;
    }
  };

  const openManagerModal = (tab = 'categories') => {
    if (!modalEl) initModal();
    if (!modalEl) return;
    modalEl.style.display = 'flex';
    modalEl.classList.add('active'); // Bắt buộc thêm class active để mở pointer-events: auto
    if (window.lockBodyScroll) window.lockBodyScroll(true);
    switchTab(tab);
  };

  const closeManagerModal = () => {
    if (modalEl) {
      modalEl.style.display = 'none';
      modalEl.classList.remove('active'); // Gỡ bỏ class active
    }
    if (window.lockBodyScroll) window.lockBodyScroll(false);
  };

  return {
    initModal,
    openManagerModal,
    closeManagerModal,
    renderCategoriesTab,
    renderTagsTab,
    parseTagsFromInput,
    normalizeTag,
    toggleTagInInput,
    syncChipStates,
    updateSuggestedChipsSelection,
    loadSuggestedChips,
    loadPopularTags
  };
})();

window.KokoroTagManager = KokoroTagManager;

