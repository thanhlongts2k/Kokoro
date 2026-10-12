/**
 * KOKORO (心) — TAG MANAGEMENT MODULE
 * Architecture: Clean Component, decoupled from editor & app coordinators.
 * Features: Tag normalization, editor quick suggestion chips, sidebar popular tags widget.
 */

const KokoroTagManager = (() => {
  let cachedTags = [];

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
          const isSelected = currentSelected.includes(cleanName.toLowerCase());
          return `
            <span class="tag-quick-chip ${isSelected ? 'selected' : ''}" data-tag="${cleanName}" title="Gắn thẻ ${cleanName} (${t.usage_count} bài viết)">
              ${cleanName} <span class="tag-quick-chip-count">(${t.usage_count})</span>
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
          const isActive = activeFilter && activeFilter.toLowerCase() === cleanName.toLowerCase();
          return `
            <span class="tag-pill ${isActive ? 'active' : ''}" data-tag="${cleanName}" title="Lọc theo thẻ ${cleanName} (${t.usage_count} bài viết)">
              ${cleanName} <span class="tag-count">(${t.usage_count})</span>
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
  let modalEl = null;
  let tabMoodsBtn = null;
  let tabTagsBtn = null;
  let contentMoodsEl = null;
  let contentTagsEl = null;
  let moodsListContainer = null;
  let tagsListContainer = null;
  let totalTagsLabel = null;
  let cleanupOrphansBtn = null;
  let currentActiveTab = 'moods';

  const initModal = () => {
    modalEl = document.getElementById('category-tag-manager-modal');
    if (!modalEl) return;

    tabMoodsBtn = document.getElementById('tab-btn-cat-moods');
    tabTagsBtn = document.getElementById('tab-btn-cat-tags');
    contentMoodsEl = document.getElementById('cat-tab-content-moods');
    contentTagsEl = document.getElementById('cat-tab-content-tags');
    moodsListContainer = document.getElementById('cat-moods-list-container');
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

    if (tabMoodsBtn) {
      tabMoodsBtn.addEventListener('click', () => switchTab('moods'));
    }
    if (tabTagsBtn) {
      tabTagsBtn.addEventListener('click', () => switchTab('tags'));
    }

    if (cleanupOrphansBtn) {
      cleanupOrphansBtn.addEventListener('click', async () => {
        if (!confirm('Bạn có chắc muốn dọn dẹp toàn bộ các thẻ chưa gắn với bài viết nào (0 bài)?')) return;
        try {
          const res = await window.KokoroAPI.cleanupOrphanTags();
          if (res && res.status === 'success') {
            if (window.KokoroApp && window.KokoroApp.showToast) {
              window.KokoroApp.showToast(res.message || 'Đã dọn dẹp thẻ mồ côi thành công! 🌸');
            }
            await renderTagsTab();
            if (window.KokoroApp) await window.KokoroApp.loadPopularTags();
          }
        } catch (err) {
          if (window.KokoroApp && window.KokoroApp.showToast) {
            window.KokoroApp.showToast('Lỗi dọn dẹp: ' + err.message, 'error');
          }
        }
      });
    }

    // Attach to profile view trigger button
    const profileBtn = document.getElementById('profile-action-category-tags');
    if (profileBtn) {
      profileBtn.addEventListener('click', () => openManagerModal('moods'));
    }
  };

  const switchTab = (tab) => {
    currentActiveTab = tab;
    if (tab === 'moods') {
      if (tabMoodsBtn) tabMoodsBtn.classList.add('active');
      if (tabTagsBtn) tabTagsBtn.classList.remove('active');
      if (contentMoodsEl) contentMoodsEl.style.display = 'flex';
      if (contentTagsEl) contentTagsEl.style.display = 'none';
      renderMoodsTab();
    } else {
      if (tabMoodsBtn) tabMoodsBtn.classList.remove('active');
      if (tabTagsBtn) tabTagsBtn.classList.add('active');
      if (contentMoodsEl) contentMoodsEl.style.display = 'none';
      if (contentTagsEl) contentTagsEl.style.display = 'flex';
      renderTagsTab();
    }
  };

  const renderMoodsTab = async () => {
    if (!moodsListContainer) return;
    try {
      const stats = (window.KokoroApp && window.KokoroApp.stats) ? window.KokoroApp.stats : await window.KokoroAPI.getStats();
      const breakdown = (stats && stats.moodBreakdown) || {};
      const total = (stats && stats.totalEntries) || 0;

      const moods = [
        { key: 'serene', icon: '🌸', name: 'Thanh bình', color: 'var(--mood-serene)' },
        { key: 'cozy', icon: '☕', name: 'Ấm áp', color: 'var(--mood-cozy)' },
        { key: 'reflective', icon: '🌙', name: 'Chiêm nghiệm', color: 'var(--mood-reflective)' },
        { key: 'grateful', icon: '🍵', name: 'Biết ơn', color: 'var(--mood-grateful)' },
        { key: 'energetic', icon: '⚡', name: 'Năng lượng', color: 'var(--mood-energetic)' },
      ];

      moodsListContainer.innerHTML = moods.map((m) => {
        const info = breakdown[m.key] || { count: 0, percent: 0 };
        const count = info.count || 0;
        const pct = info.percent || 0;
        return `
          <div class="glass-panel" style="padding: 12px 16px; border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; color: var(--text-primary); font-size: 13.5px;">
                <span>${m.icon}</span>
                <span>${m.name}</span>
              </div>
              <div style="font-size: 12px; font-weight: 700; color: var(--text-secondary);">
                ${count} bài viết <span style="opacity: 0.6; margin-left: 4px;">(${Math.round(pct)}%)</span>
              </div>
            </div>
            <div style="height: 6px; border-radius: 3px; background: rgba(148, 163, 184, 0.15); overflow: hidden;">
              <div style="height: 100%; width: ${pct}%; background: ${m.color}; border-radius: 3px; transition: width 0.4s ease;"></div>
            </div>
          </div>
        `;
      }).join('');
    } catch (e) {
      moodsListContainer.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center;">Chưa thể tải dữ liệu thống kê tâm trạng.</div>`;
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
            🍃 Bạn chưa có thẻ chủ đề nào.<br>Thêm thẻ vào bài viết (ví dụ: #sakura, #coffee) để quản lý tại đây nhé!
          </div>
        `;
        return;
      }

      tagsListContainer.innerHTML = tags.map((t) => {
        const cleanName = normalizeTag(t.name);
        return `
          <div class="glass-panel" style="padding: 10px 14px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
              <span class="tag-quick-chip selected" style="margin: 0; pointer-events: none;">${cleanName}</span>
              <span style="font-size: 11.5px; color: var(--text-muted); white-space: nowrap;">${t.usage_count} bài viết</span>
            </div>
            <div style="display: flex; gap: 6px; flex-shrink: 0;">
              <button type="button" class="action-icon-btn btn-rename-tag" data-tag-id="${t.id}" data-tag-name="${cleanName}" style="width: 30px; height: 30px;" title="Đổi tên thẻ">
                <i class="bi bi-pencil" style="font-size: 12px;"></i>
              </button>
              <button type="button" class="action-icon-btn btn-delete-tag text-danger" data-tag-id="${t.id}" data-tag-name="${cleanName}" style="width: 30px; height: 30px;" title="Xóa thẻ">
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
          const newName = prompt(`Nhập tên mới cho thẻ ${oldName}:`, oldName.replace(/^#/, ''));
          if (newName === null) return;
          const trimmed = newName.trim();
          if (!trimmed) {
            alert('Tên thẻ không được để trống.');
            return;
          }

          try {
            const updateRes = await window.KokoroAPI.updateTag(tagId, trimmed);
            if (updateRes && updateRes.status === 'success') {
              if (window.KokoroApp && window.KokoroApp.showToast) {
                window.KokoroApp.showToast(`Đã đổi tên thẻ thành #${trimmed.replace(/^#/, '')} ✨`);
              }
              await renderTagsTab();
              if (window.KokoroApp) {
                await window.KokoroApp.loadEntries();
                await window.KokoroApp.loadPopularTags();
              }
            }
          } catch (err) {
            alert('Lỗi đổi tên thẻ: ' + err.message);
          }
        });
      });

      // Delete tag handler
      tagsListContainer.querySelectorAll('.btn-delete-tag').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          const tagId = e.currentTarget.dataset.tagId;
          const tagName = e.currentTarget.dataset.tagName;
          if (!confirm(`Bạn có chắc muốn xóa thẻ ${tagName}? Thẻ sẽ được gỡ khỏi các bài viết liên quan.`)) return;

          try {
            const delRes = await window.KokoroAPI.deleteTag(tagId);
            if (delRes && delRes.status === 'success') {
              if (window.KokoroApp && window.KokoroApp.showToast) {
                window.KokoroApp.showToast(`Đã xóa thẻ ${tagName} thành công 🌸`);
              }
              await renderTagsTab();
              if (window.KokoroApp) {
                await window.KokoroApp.loadEntries();
                await window.KokoroApp.loadPopularTags();
              }
            }
          } catch (err) {
            alert('Lỗi xóa thẻ: ' + err.message);
          }
        });
      });
    } catch (e) {
      tagsListContainer.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center;">Không thể tải danh sách thẻ.</div>`;
    }
  };

  const openManagerModal = (tab = 'moods') => {
    if (!modalEl) initModal();
    if (!modalEl) return;
    modalEl.style.display = 'flex';
    switchTab(tab);
  };

  const closeManagerModal = () => {
    if (modalEl) modalEl.style.display = 'none';
  };

  return {
    initModal,
    openManagerModal,
    closeManagerModal,
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
