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
  isLoading: false,

  async init() {
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
        const sereneEl = document.getElementById('stat-serene-percent');

        if (totalEl) totalEl.textContent = res.totalEntries;
        if (streakEl) streakEl.textContent = `${res.streakDays || 1} ngày`;
        if (sereneEl) sereneEl.textContent = `${res.serenePercent}%`;
      }
    } catch (err) {
      console.warn('[KokoroApp] Không thể tải stats:', err);
    }
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

  async deleteEntry(id) {
    if (confirm('Bạn có chắc muốn xóa khoảnh khắc nhật ký này không? 🌸')) {
      try {
        await window.KokoroAPI.deleteEntry(id);
        this.showToast('Đã xóa bài viết thành công 🌸');
        await this.loadEntries();
        await this.loadStats();
      } catch (err) {
        this.showToast('Lỗi khi xóa bài viết: ' + err.message, 'error');
      }
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

    feedEl.querySelectorAll('[data-action="delete"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        this.deleteEntry(id);
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

    const streakEl = document.getElementById('stat-writing-streak');
    if (streakEl) streakEl.textContent = `${Math.min(this.entries.length * 2, 7)} ngày`;

    const sereneCount = this.entries.filter((e) => e.mood === 'serene').length;
    const serenePercentEl = document.getElementById('stat-serene-percent');
    if (serenePercentEl && this.entries.length > 0) {
      serenePercentEl.textContent = `${Math.round((sereneCount / this.entries.length) * 100)}%`;
    }
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
