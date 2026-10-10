/**
 * KOKORO (心) — MAIN APPLICATION COORDINATOR
 * Connects PostgreSQL database via KokoroAPI REST Client,
 * manages responsive view lifecycle, filtering, and Soft Sakura pastel toasts.
 */

const KokoroApp = {
  entries: [],
  activeMoodFilter: 'all',
  activeTagFilter: null,
  activeDateFilter: null,
  searchQuery: '',
  pendingDeleteId: null,
  isLoading: false,

  async init() {
    this.initTheme();

    // Initialize submodules
    if (window.Lightbox) window.Lightbox.init();
    if (window.Editor) window.Editor.init();
    if (window.PWA) window.PWA.init();

    this.setupEventListeners();

    // Initialize Auth & Session
    let user = null;
    if (window.KokoroAuth) {
      user = await window.KokoroAuth.init();
    }

    if (user) {
      await this.onUserChanged(user);
    }
  },

  async onUserChanged(user) {
    this.activeMoodFilter = 'all';
    this.activeTagFilter = null;
    this.activeDateFilter = null;

    // Dynamic greeting
    const greetingEl = document.querySelector('.timeline-feed h1');
    if (greetingEl) {
      const firstName = user ? user.name.split(' ')[0] : 'bạn';
      greetingEl.textContent = `Chào ${firstName}, hôm nay bạn cảm thấy thế nào? 🌸`;
    }

    if (user) {
      await this.loadEntries();
      await this.loadStats();
    } else {
      this.entries = [];
      this.renderTimeline();
      this.renderCalendar();
      this.renderStats();
    }
  },

  setupEventListeners() {
    // FAB Open Editor
    const fabBtn = document.getElementById('fab-create-btn');
    if (fabBtn) {
      fabBtn.addEventListener('click', () => {
        if (window.Editor) window.Editor.open();
      });
    }

    // Header "+ Viết bài" button on desktop
    const headerAddBtn = document.getElementById('header-add-entry-btn');
    if (headerAddBtn) {
      headerAddBtn.addEventListener('click', () => {
        if (window.Editor) window.Editor.open();
      });
    }

    // Mood filter chips in sidebar and mobile scroll
    const moodFilterBtns = document.querySelectorAll('[data-filter-mood]');
    moodFilterBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const mood = e.currentTarget.dataset.filterMood;
        this.setMoodFilter(mood);
      });
    });

    // Mobile Bottom Nav items
    const navItems = document.querySelectorAll('.bottom-nav-item');
    navItems.forEach((item) => {
      item.addEventListener('click', () => {
        navItems.forEach((n) => n.classList.remove('active'));
        item.classList.add('active');
        const tab = item.dataset.tab;
        if (tab === 'editor') {
          if (window.Editor) window.Editor.open();
        } else if (tab === 'timeline') {
          this.clearFilters();
        }
      });
    });

    // Network status & auto-sync offline queue
    window.addEventListener('online', async () => {
      this.showToast('Đã kết nối Internet trở lại! Đang kiểm tra dữ liệu ngoại tuyến... ✨');
      try {
        const synced = await window.KokoroAPI.syncOfflineQueue();
        if (synced > 0) {
          this.showToast(`Đã đồng bộ ${synced} bài viết ngoại tuyến thành công! 🌸`);
          await this.loadEntries();
          await this.loadStats();
        }
      } catch (e) {
        console.warn('[KokoroApp] Lỗi đồng bộ khi online:', e);
      }
    });

    window.addEventListener('offline', () => {
      this.showToast('Bạn đang ở chế độ ngoại tuyến (Offline). Các bài viết sẽ được lưu an toàn 🍃', 'warning');
    });

    // Backup Export Button in Profile Dropdown
    const exportBtn = document.getElementById('export-backup-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          this.showToast('Đang trích xuất và tải bản sao lưu nhật ký... 🌸');
          await window.KokoroAPI.exportEntries();
          this.showToast('Đã tải bản sao lưu JSON thành công! ✨');
        } catch (err) {
          this.showToast('Lỗi tải bản sao lưu: ' + err.message, 'error');
        }
      });
    }

    // Backup Import Button in Profile Dropdown
    const importBtn = document.getElementById('import-backup-btn');
    const backupFileInput = document.getElementById('backup-file-input');
    if (importBtn && backupFileInput) {
      importBtn.addEventListener('click', (e) => {
        e.preventDefault();
        backupFileInput.value = '';
        backupFileInput.click();
      });

      backupFileInput.addEventListener('change', async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        try {
          this.showToast('Đang khôi phục dữ liệu từ tệp sao lưu... 🌸');
          const result = await window.KokoroAPI.importEntries(file);
          this.showToast(result.message || 'Khôi phục nhật ký thành công! ✨');
          await this.loadEntries();
          await this.loadStats();
        } catch (err) {
          this.showToast('Lỗi khôi phục dữ liệu: ' + err.message, 'error');
        }
      });
    }

    // Live Search input (Debounce 300ms)
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    let searchDebounceTimer = null;

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (searchClearBtn) {
          searchClearBtn.style.display = val.length > 0 ? 'inline-flex' : 'none';
        }
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
          this.searchQuery = val.trim();
          this.loadEntries();
        }, 300);
      });
    }

    if (searchClearBtn && searchInput) {
      searchClearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchClearBtn.style.display = 'none';
        this.searchQuery = '';
        this.loadEntries();
        searchInput.focus();
      });
    }

    // Custom Delete Confirm Modal events
    const cancelDeleteBtn = document.getElementById('confirm-cancel-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    const deleteModal = document.getElementById('delete-confirm-modal');
    if (cancelDeleteBtn) {
      cancelDeleteBtn.addEventListener('click', () => this.closeDeleteConfirm());
    }
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', () => this.executeDelete());
    }
    if (deleteModal) {
      deleteModal.addEventListener('click', (e) => {
        if (e.target === deleteModal) this.closeDeleteConfirm();
      });
    }

    // Escape key listener for confirm modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.pendingDeleteId) {
        this.closeDeleteConfirm();
      }
    });
  },

  /**
   * Fetch entries from PostgreSQL API with currently applied filters
   */
  async loadEntries() {
    this.isLoading = true;
    try {
      const filters = {};
      if (this.activeMoodFilter && this.activeMoodFilter !== 'all') {
        filters.mood = this.activeMoodFilter;
      }
      if (this.activeTagFilter) {
        filters.tag = this.activeTagFilter;
      }
      if (this.searchQuery) {
        filters.search = this.searchQuery;
      }

      const res = await window.KokoroAPI.getEntries(filters);
      if (res && res.status === 'success') {
        this.entries = res.entries || [];
      } else {
        this.entries = [];
      }
    } catch (err) {
      console.warn('[KokoroApp] Lỗi tải dữ liệu từ API:', err);
      if (err.message && (err.message.includes('401') || err.message.includes('đăng nhập'))) {
        if (window.KokoroAuth) window.KokoroAuth.showLoginModal();
      }
      this.entries = [];
    } finally {
      this.isLoading = false;
      this.renderTimeline();
      this.renderCalendar();
      this.renderStats();
    }
  },

  /**
   * Fetch summary statistics from database
   */
  async loadStats() {
    try {
      const res = await window.KokoroAPI.getStats();
      if (res && res.status === 'success') {
        const totalEl = document.getElementById('stat-total-entries');
        const streakEl = document.getElementById('stat-writing-streak');
        const photosEl = document.getElementById('stat-photos-count');

        if (totalEl) totalEl.textContent = res.totalEntries;
        if (streakEl) streakEl.textContent = `${res.streakDays || 0} ngày`;
        if (photosEl) photosEl.innerHTML = `<i class="bi bi-camera text-sakura"></i> ${res.totalPhotos || 0} ảnh`;

        this.renderMoodBreakdown(res.moodBreakdown, res.totalEntries);
      }
    } catch (err) {
      console.warn('[KokoroApp] Không thể tải stats:', err);
    }
  },

  renderMoodBreakdown(breakdown, total) {
    const multiBar = document.getElementById('stat-mood-multibar');
    if (!multiBar) return;

    if (!total || total === 0) {
      multiBar.innerHTML = `<div class="mood-segment segment-serene" style="width: 100%; opacity: 0.3;" title="Chưa có dữ liệu"></div>`;
      ['serene', 'cozy', 'reflective', 'grateful', 'energetic'].forEach((m) => {
        const el = document.getElementById(`leg-${m}`);
        if (el) el.textContent = '0%';
      });
      return;
    }

    const moods = [
      { key: 'serene', cls: 'segment-serene', label: 'Thanh bình' },
      { key: 'cozy', cls: 'segment-cozy', label: 'Ấm áp' },
      { key: 'reflective', cls: 'segment-reflective', label: 'Chiêm nghiệm' },
      { key: 'grateful', cls: 'segment-grateful', label: 'Biết ơn' },
      { key: 'energetic', cls: 'segment-energetic', label: 'Năng lượng' },
    ];

    let html = '';
    moods.forEach((m) => {
      const info = breakdown && breakdown[m.key] ? breakdown[m.key] : { percent: 0, count: 0 };
      const pct = info.percent || 0;
      if (pct > 0) {
        html += `<div class="mood-segment ${m.cls}" style="width: ${pct}%;" title="${m.label}: ${pct}% (${info.count} bài)"></div>`;
      }
      const el = document.getElementById(`leg-${m.key}`);
      if (el) el.textContent = `${Math.round(pct)}%`;
    });

    multiBar.innerHTML = html || `<div class="mood-segment segment-serene" style="width: 100%;"></div>`;
  },

  async setMoodFilter(mood) {
    this.activeMoodFilter = mood;
    this.activeTagFilter = null;
    this.activeDateFilter = null;

    // Update active style on filter buttons
    document.querySelectorAll('[data-filter-mood]').forEach((btn) => {
      if (btn.dataset.filterMood === mood) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    await this.loadEntries();
  },

  async setTagFilter(tag) {
    if (this.activeTagFilter === tag) {
      this.activeTagFilter = null;
    } else {
      this.activeTagFilter = tag;
    }
    await this.loadEntries();
  },

  setDateFilter(dateStr) {
    if (this.activeDateFilter === dateStr) {
      this.activeDateFilter = null;
    } else {
      this.activeDateFilter = dateStr;
    }
    this.renderTimeline();
  },

  async clearFilters() {
    this.activeMoodFilter = 'all';
    this.activeTagFilter = null;
    this.activeDateFilter = null;
    document.querySelectorAll('[data-filter-mood]').forEach((b) => b.classList.remove('active'));
    const allBtn = document.querySelector('[data-filter-mood="all"]');
    if (allBtn) allBtn.classList.add('active');
    await this.loadEntries();
  },

  initTheme() {
    const savedTheme = localStorage.getItem('kokoro_theme') || 'light';
    this.applyTheme(savedTheme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
      });
    }
  },

  applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('kokoro_theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('kokoro_theme', 'light');
    }
    const icon = document.getElementById('theme-toggle-icon');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill text-warning' : 'bi bi-moon-stars-fill text-sakura';
    }
  },

  openDeleteConfirm(id) {
    this.pendingDeleteId = id;
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
      modal.classList.add('active');
    }
  },

  closeDeleteConfirm() {
    this.pendingDeleteId = null;
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
      modal.classList.remove('active');
    }
  },

  async executeDelete() {
    if (!this.pendingDeleteId) return;
    const id = this.pendingDeleteId;
    this.closeDeleteConfirm();
    try {
      await window.KokoroAPI.deleteEntry(id);
      this.showToast('Đã buông bỏ khoảnh khắc nhật ký 🌸');
      await this.loadEntries();
      await this.loadStats();
    } catch (err) {
      this.showToast('Lỗi khi xóa bài viết: ' + err.message, 'error');
    }
  },

  async togglePin(id) {
    try {
      const res = await window.KokoroAPI.togglePin(id);
      const msg = res.is_pinned ? 'Đã ghim bài viết lên đầu ✨' : 'Đã bỏ ghim bài viết';
      this.showToast(msg);
      await this.loadEntries();
    } catch (err) {
      this.showToast('Lỗi khi ghim bài viết: ' + err.message, 'error');
    }
  },

  getFilteredEntries() {
    // If a date filter is selected via calendar, filter in-memory
    if (this.activeDateFilter) {
      return this.entries.filter((e) => e.entryDate === this.activeDateFilter);
    }
    return this.entries;
  },

  renderTimeline() {
    const feedEl = document.getElementById('timeline-feed-container');
    if (!feedEl) return;

    if (this.isLoading) {
      feedEl.innerHTML = `
        <div class="glass-panel text-center" style="padding: 48px 24px;">
          <span class="btn-spinner" style="width: 24px; height: 24px; border-width: 3px; border-color: rgba(244, 114, 182, 0.3); border-top-color: var(--sakura-500);"></span>
          <p style="font-size: 13px; color: var(--text-muted); margin-top: 12px;">Đang tải nhật ký từ máy chủ...</p>
        </div>
      `;
      return;
    }

    const filtered = this.getFilteredEntries();

    if (filtered.length === 0) {
      feedEl.innerHTML = `
        <div class="glass-panel text-center" style="padding: 48px 24px;">
          <div style="font-size: 42px; margin-bottom: 12px;">🌸</div>
          <h3 style="font-size: 17px; font-weight: 800; margin: 0 0 6px 0; color: var(--text-primary);">Chưa có nhật ký nào ở chế độ lọc này</h3>
          <p style="font-size: 13px; color: var(--text-muted); margin: 0 0 16px 0;">Hãy bấm nút bên dưới để ghi lại khoảnh khắc đầu tiên nhé!</p>
          <button class="btn-sakura" onclick="window.Editor && window.Editor.open()">+ Ghi nhật ký mới</button>
        </div>
      `;
      return;
    }

    feedEl.innerHTML = filtered.map((entry) => this.buildEntryCardHtml(entry)).join('');

    // Attach listeners for image clicks (Lightbox) & card buttons
    feedEl.querySelectorAll('.gallery-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        const fullSrc = item.dataset.fullSrc;
        const img = item.querySelector('img');
        if (window.Lightbox) {
          window.Lightbox.open(fullSrc || (img ? img.src : ''), img ? img.alt : '');
        }
      });
    });

    feedEl.querySelectorAll('[data-action="edit"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        const entry = this.entries.find((item) => item.id === id);
        if (entry && window.Editor) {
          window.Editor.open(entry);
        }
      });
    });

    feedEl.querySelectorAll('[data-action="delete"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        this.openDeleteConfirm(id);
      });
    });

    feedEl.querySelectorAll('[data-action="pin"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        this.togglePin(id);
      });
    });

    feedEl.querySelectorAll('.tag-pill').forEach((tagBtn) => {
      tagBtn.addEventListener('click', (e) => {
        const tag = e.currentTarget.dataset.tag;
        this.setTagFilter(tag);
      });
    });
  },

  buildEntryCardHtml(entry) {
    const photosCount = entry.photos ? entry.photos.length : 0;
    let photosGridHtml = '';

    if (photosCount > 0) {
      const countAttr = photosCount >= 4 ? 'more' : String(photosCount);
      let itemsHtml = '';

      if (photosCount <= 3) {
        itemsHtml = entry.photos
          .map((p, idx) => {
            const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
            const fullUrl = window.KokoroAPI.resolveMediaUrl(p.url);
            return `
              <div class="gallery-item" data-full-src="${fullUrl}">
                <img src="${thumbUrl}" alt="${p.name || 'Photo ' + (idx + 1)}" loading="lazy" />
              </div>
            `;
          })
          .join('');
      } else {
        // 4+ photos: first 3 + 4th with overlay badge
        const displayPhotos = entry.photos.slice(0, 4);
        itemsHtml = displayPhotos
          .map((p, idx) => {
            const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
            const fullUrl = window.KokoroAPI.resolveMediaUrl(p.url);
            const isLast = idx === 3 && photosCount > 4;
            const extraCount = photosCount - 4;
            return `
              <div class="gallery-item" data-full-src="${fullUrl}">
                <img src="${thumbUrl}" alt="${p.name || 'Photo ' + (idx + 1)}" loading="lazy" />
                ${isLast ? `<div class="gallery-more-overlay">+${extraCount} ảnh</div>` : ''}
              </div>
            `;
          })
          .join('');
      }

      photosGridHtml = `
        <div class="photo-gallery-grid" data-count="${countAttr}">
          ${itemsHtml}
        </div>
      `;
    }

    const tagsHtml = (entry.tags || [])
      .map(
        (t) => `
        <span class="tag-pill ${this.activeTagFilter === t ? 'active' : ''}" data-tag="${t}">${t}</span>
      `
      )
      .join('');

    return `
      <article class="glass-panel journal-card glass-card-interactive" id="entry-${entry.id}">
        <div class="card-header">
          <div class="card-meta">
            <span class="mood-pill mood-${entry.mood}">${entry.moodLabel || entry.mood}</span>
            <span>&bull;</span>
            <span><i class="bi bi-clock"></i> ${entry.displayDate || entry.entryDate}</span>
            ${entry.isPinned ? `<span style="color: var(--sakura-500); margin-left: 4px;" title="Đã ghim"><i class="bi bi-pin-angle-fill"></i></span>` : ''}
          </div>
          <div class="card-actions">
            <button class="action-icon-btn" data-action="pin" data-id="${entry.id}" title="${entry.isPinned ? 'Bỏ ghim' : 'Ghim bài'}">
              <i class="bi ${entry.isPinned ? 'bi-pin-fill text-sakura' : 'bi-pin'}"></i>
            </button>
            <button class="action-icon-btn" data-action="edit" data-id="${entry.id}" title="Chỉnh sửa bài">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="action-icon-btn" data-action="delete" data-id="${entry.id}" title="Xóa bài">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </div>

        <h2 class="card-title">${entry.title}</h2>
        <p class="card-content">${entry.content}</p>

        ${photosGridHtml}

        <div class="card-footer">
          <div class="card-tags-list">
            ${tagsHtml}
          </div>
          <div style="font-size: 12px; color: var(--text-muted);">
            <i class="bi bi-heart text-sakura" style="margin-right: 4px;"></i> Kokoro Journal
          </div>
        </div>
      </article>
    `;
  },

  renderCalendar() {
    const gridEl = document.getElementById('mini-calendar-grid');
    if (!gridEl) return;

    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth(); // 0-indexed

    // Set month title
    const monthTitleEl = document.getElementById('cal-month-title');
    if (monthTitleEl) {
      const monthNames = [
        'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
      ];
      monthTitleEl.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    }

    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay(); // 0: Sun
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    // Map of dates with entries in this month
    const datesWithEntries = new Set(
      this.entries.map((e) => e.entryDate)
    );

    let html = `
      <div class="cal-day-label">CN</div>
      <div class="cal-day-label">T2</div>
      <div class="cal-day-label">T3</div>
      <div class="cal-day-label">T4</div>
      <div class="cal-day-label">T5</div>
      <div class="cal-day-label">T6</div>
      <div class="cal-day-label">T7</div>
    `;

    // Empty spaces before first day
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<div class="cal-day-cell empty"></div>`;
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = day === today.getDate();
      const hasEntry = datesWithEntries.has(dateStr);
      const isSelected = this.activeDateFilter === dateStr;

      html += `
        <div class="cal-day-cell ${isToday ? 'today' : ''} ${hasEntry ? 'has-entry' : ''} ${isSelected ? 'selected' : ''}" 
             data-date="${dateStr}">
          <span>${day}</span>
        </div>
      `;
    }

    gridEl.innerHTML = html;

    // Attach click listeners to calendar days
    gridEl.querySelectorAll('.cal-day-cell[data-date]').forEach((cell) => {
      cell.addEventListener('click', (e) => {
        const d = e.currentTarget.dataset.date;
        this.setDateFilter(d);
        this.renderCalendar();
      });
    });
  },

  renderStats() {
    const countEl = document.getElementById('stat-total-entries');
    if (countEl) countEl.textContent = this.entries.length;

    const total = this.entries.length;
    const moodCounts = { serene: 0, cozy: 0, reflective: 0, grateful: 0, energetic: 0 };
    this.entries.forEach((e) => {
      if (e.mood && moodCounts.hasOwnProperty(e.mood)) {
        moodCounts[e.mood]++;
      }
    });

    const breakdown = {};
    for (const [m, count] of Object.entries(moodCounts)) {
      breakdown[m] = {
        count,
        percent: total > 0 ? (count / total) * 100 : 0
      };
    }

    this.renderMoodBreakdown(breakdown, total);
  },

  /**
   * Delicate Soft Sakura Toast Notification
   * @param {string} message 
   * @param {'success'|'error'|'warning'} type 
   */
  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-item';

    let icon = '🌸';
    if (type === 'error') icon = '⚠️';
    if (type === 'success') icon = '✨';

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    // Auto dismiss after 3.2s
    setTimeout(() => {
      toast.classList.add('hide');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 350);
    }, 3200);
  }
};

window.KokoroApp = KokoroApp;

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  KokoroApp.init();
});
