/**
 * KOKORO (心) — APPLICATION COORDINATOR & BOOTSTRAPPER (v1.6.5)
 * Central orchestrator for view routing, state synchronization, and event dispatching.
 * Delegates rendering to specialized components:
 * - TimelineFeed (timeline-feed.js)
 * - CalendarView (calendar-view.js)
 * - MemoriesView (memories-view.js)
 * - ProfileStats (profile-stats.js)
 * Complies with AGENTS.md: Modular Layered Architecture (< 400 lines).
 */

const KokoroApp = {
  entries: [], allEntries: [], categories: [], stats: null, isLoading: false, pendingDeleteId: null, isOffline: !navigator.onLine,
  activeMoodFilter: null, activeCategoryId: null, activeTagFilter: null, activeDateFilter: null, searchQuery: '',
  timelineState: { mood: null, categoryId: null, tag: null, search: '' },
  memoriesState: { mood: 'all', categoryId: null, tag: null },
  currentView: 'timeline',
  calYear: new Date().getFullYear(), calMonth: new Date().getMonth(),
  selectedCalDate: new Date().toISOString().split('T')[0],
  activeMemoriesMood: 'all', activeMemoriesTag: null, activeZenPrompt: null,
  timelinePagination: {
    pageSize: (window.KokoroConstants ? window.KokoroConstants.PAGINATION.DEFAULT_PAGE_SIZE : 15),
    visibleLimit: (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15)
  },

  async init() {
    this.initTheme();
    [window.KokoroDateTimePicker, window.Lightbox, window.Editor, window.ZenAudio, window.PasscodeLock, window.PWA].forEach(m => m?.init?.());
    if (window.KokoroCardExport) window.KokoroCardExport.init();
    if (window.KokoroTagManager?.initModal) window.KokoroTagManager.initModal();
    this.setupEventListeners(); this.setupNetworkListeners();

    const initialHash = location.hash ? location.hash.replace('#', '') : 'timeline';
    if (['timeline', 'calendar', 'memories', 'profile'].includes(initialHash) && initialHash !== 'timeline') {
      this.switchView(initialHash, false);
      try { history.replaceState({ view: initialHash }, '', '#' + initialHash); } catch (err) {}
    } else { try { history.replaceState({ view: 'timeline' }, '', '#timeline'); } catch (err) {} }

    if (window.KokoroAuth) await window.KokoroAuth.init();
    if (window.KokoroAuth?.currentUser) {
      await Promise.all([this.loadCategories(), this.loadEntries(), this.loadStats(), this.loadPopularTags()]);
    } else {
      this.renderTimeline();
    }
    this.initZenPromptHandlers();
  },

  async onUserChanged(user) {
    if (!user) {
      this.entries = []; this.allEntries = []; this.stats = null; this.categories = [];
      const tagsContainer = document.getElementById('sidebar-popular-tags');
      if (tagsContainer) tagsContainer.innerHTML = '';
      if (window.KokoroTimelineFeed?.render) window.KokoroTimelineFeed.render([]);
      else this.renderTimeline();
      this.renderCalendar();
      if (this.currentView === 'profile') this.renderProfileView();
      return;
    }
    await Promise.all([this.loadCategories(), this.loadEntries(), this.loadStats(), this.loadPopularTags()]);
    if (this.currentView === 'profile') this.renderProfileView();
  },

  async updateOfflineBanner(show) {
    this.isOffline = Boolean(show);
    const banner = document.getElementById('offline-status-banner'), badge = document.getElementById('offline-queue-badge'), countEl = document.getElementById('offline-queue-count');
    if (show) {
      if (banner) banner.classList.add('active');
      if (window.KokoroAPI?.getOfflineEntries) {
        window.KokoroAPI.getOfflineEntries().then(p => {
          if (badge && countEl) { const c = p?.length || 0; countEl.textContent = c; badge.style.display = c > 0 ? 'inline-flex' : 'none'; }
        }).catch(() => {});
      }
    } else if (banner) banner.classList.remove('active');
  },
  setupNetworkListeners() {
    window.addEventListener('offline', () => { this.updateOfflineBanner(true); });
    window.addEventListener('online', async () => {
      this.updateOfflineBanner(false);
      this.showToast('Đã khôi phục kết nối mạng 🌸 Đang đồng bộ...', 'info');
      if (window.KokoroAPI?.syncOfflineQueue) {
        try {
          const synced = await window.KokoroAPI.syncOfflineQueue();
          if (synced > 0) this.showToast(`Đã đồng bộ thành công ${synced} bài viết ngoại tuyến! ✨`);
        } catch (e) { console.warn('[KokoroApp] Sync error:', e); }
      }
      await this.loadCategories(); await this.loadEntries(); await this.loadStats(); await this.loadPopularTags();
    });
    if (!navigator.onLine) this.updateOfflineBanner(true);
  },

  setupEventListeners() {
    document.querySelectorAll('[data-switch-view], [data-view-target]').forEach((b) => b.addEventListener('click', (e) => {
      const v = e.currentTarget.dataset.switchView || e.currentTarget.dataset.viewTarget;
      if (v) this.switchView(v);
    }));
    document.querySelectorAll('.bottom-nav-item').forEach((b) => b.addEventListener('click', (e) => {
      const tab = e.currentTarget.dataset.tab;
      if (tab === 'editor') { if (window.Editor) window.Editor.open(); } else if (tab) this.switchView(tab);
    }));

    document.addEventListener('click', (e) => {
      const pill = e.target.closest('#header-profile-pill, .header-profile-pill, #user-profile-pill');
      const dropdown = document.getElementById('profile-dropdown-menu');
      if (pill) { e.stopPropagation(); if (dropdown) dropdown.classList.toggle('active'); return; }
      if (dropdown && !e.target.closest('#profile-dropdown-menu')) dropdown.classList.remove('active');
      const item = e.target.closest('#profile-dropdown-menu .dropdown-item, #profile-dropdown-menu .dropdown-header');
      if (item && dropdown) {
        setTimeout(() => dropdown.classList.remove('active'), 150);
        if (item.classList.contains('dropdown-header') || item.dataset.switchView === 'profile') this.switchView('profile');
      }
    });

    const bind = (ids, fn) => ids.forEach((id) => { const el = document.getElementById(id); if (el) el.addEventListener('click', fn); });
    bind(['header-add-entry-btn', 'fab-create-btn', 'header-new-entry-btn', 'mobile-fab-btn'], () => { if (window.Editor) window.Editor.open(); });
    bind(['lock-screen-now-btn', 'profile-action-lock-now'], (e) => { e.preventDefault(); if (window.PasscodeLock) window.PasscodeLock.lockNow(); });
    bind(['passcode-settings-btn', 'profile-action-pin'], (e) => { e.preventDefault(); if (window.PasscodeLock) window.PasscodeLock.openSetupModal(); });
    bind(['passcode-close-settings-btn'], () => { if (window.PasscodeLock) window.PasscodeLock.closeSetupModal(); });
    bind(['profile-action-category-tags'], () => { if (window.KokoroTagManager && window.KokoroTagManager.openCategoryModal) window.KokoroTagManager.openCategoryModal(); });
    bind(['profile-action-theme', 'dropdown-theme-toggle-btn', 'theme-toggle-btn'], () => this.toggleTheme());
    bind(['profile-action-logout'], () => { if (window.KokoroAuth) window.KokoroAuth.logout(); });
    bind(['profile-action-pwa', 'pwa-install-menu-item'], () => { const p = document.getElementById('pwa-install-btn'); if (p) p.click(); });
    bind(['export-backup-btn', 'profile-action-export'], (e) => { e.preventDefault(); this.exportBackup(); });
    bind(['import-backup-btn', 'profile-action-import'], (e) => { e.preventDefault(); if (backupInput) { backupInput.value = ''; backupInput.click(); } });
    bind(['profile-action-cleanup-media'], async (e) => { e.preventDefault(); if (window.ProfileStats) await window.ProfileStats.cleanupOrphanedMedia(this); });
    if (backupInput) backupInput.addEventListener('change', async (e) => { const f = e.target.files && e.target.files[0]; if (f) await this.importBackup(f); });

    const handleRoute = () => { const h = (location.hash || '#timeline').replace('#', ''); if (['timeline', 'calendar', 'memories', 'profile'].includes(h) && h !== this.currentView) this.switchView(h, false); };
    window.addEventListener('hashchange', handleRoute); window.addEventListener('popstate', handleRoute);

    const searchInput = document.getElementById('search-input'), searchClearBtn = document.getElementById('search-clear-btn');
    let searchDebounceTimer = null;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value; if (searchClearBtn) searchClearBtn.style.display = val.length > 0 ? 'inline-flex' : 'none';
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => { this.searchQuery = val.trim(); this.timelineState.search = this.searchQuery; this.loadEntries(); }, (window.KokoroConstants ? window.KokoroConstants.TIMEOUTS.SEARCH_DEBOUNCE_MS : 300));
      });
    }
    if (searchClearBtn && searchInput) searchClearBtn.addEventListener('click', () => { searchInput.value = ''; searchClearBtn.style.display = 'none'; this.searchQuery = ''; this.timelineState.search = ''; this.loadEntries(); });

    const prevMonthBtn = document.getElementById('full-cal-prev-btn'), nextMonthBtn = document.getElementById('full-cal-next-btn');
    if (prevMonthBtn) prevMonthBtn.addEventListener('click', () => { this.calMonth--; if (this.calMonth < 0) { this.calMonth = 11; this.calYear--; } this.renderFullCalendar(); });
    if (nextMonthBtn) nextMonthBtn.addEventListener('click', () => { this.calMonth++; if (this.calMonth > 11) { this.calMonth = 0; this.calYear++; } this.renderFullCalendar(); });

    const delOk = document.getElementById('confirm-delete-btn') || document.getElementById('delete-confirm-btn');
    const delCancel = document.getElementById('confirm-cancel-btn') || document.getElementById('delete-cancel-btn');
    const delModal = document.getElementById('delete-confirm-modal') || document.getElementById('delete-modal');
    if (delOk) delOk.addEventListener('click', () => this.confirmDelete());
    if (delCancel) delCancel.addEventListener('click', () => this.closeDeleteConfirm());
    if (delModal) delModal.addEventListener('click', (e) => { if (e.target === delModal) this.closeDeleteConfirm(); });
    window.addEventListener('keydown', (e) => { if (e.key === 'Escape' && this.pendingDeleteId !== null) this.closeDeleteConfirm(); });
  },

  async loadCategories() {
    if (window.KokoroAuth && !window.KokoroAuth.currentUser) { this.categories = []; return; }
    try {
      const res = await window.KokoroAPI.getCategories();
      const cats = (res && (res.categories || res.data)) ? (res.categories || res.data) : [];
      if (cats) { this.categories = cats; this.renderMoodFilterChips(); this.renderMemoriesMoodFilterChips(); }
    } catch (e) { console.warn('[KokoroApp] Failed to load categories:', e); }
  },

  async loadEntries() {
    if (window.KokoroAuth && !window.KokoroAuth.currentUser) {
      this.entries = []; this.allEntries = []; this.isLoading = false; this.renderTimeline(); return;
    }
    this.isLoading = true; this.renderTimeline();
    try {
      const res = await window.KokoroAPI.getEntries({
        mood: this.timelineState.mood, category_id: this.timelineState.categoryId,
        tag: this.timelineState.tag, search: this.timelineState.search
      });
      this.entries = (res?.entries || res?.data) || [];
      if (!this.timelineState.mood && !this.timelineState.categoryId && !this.timelineState.tag && !this.timelineState.search) this.allEntries = this.entries;
      if (res?._isOffline) this.updateOfflineBanner(true);
    } catch (err) {
      console.error('[KokoroApp] Failed to load entries:', err);
      if (!navigator.onLine || err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) this.updateOfflineBanner(true);
      else this.showToast('Không thể tải danh sách nhật ký: ' + err.message, 'error');
    } finally {
      this.isLoading = false; this.renderTimeline(); this.renderCalendar();
      if (this.currentView === 'calendar') this.renderFullCalendar();
      if (this.currentView === 'memories') this.renderMemoriesGallery();
      if (this.currentView === 'profile') this.renderProfileView();
    }
  },

  async loadStats() {
    if (window.KokoroAuth && !window.KokoroAuth.currentUser) { this.stats = null; return; }
    try {
      const res = await window.KokoroAPI.getStats();
      const st = res && (res.data || (res.totalEntries !== undefined ? res : null));
      if (st) { this.stats = st; this.renderStats(); this.updateMoodCountBadges(this.stats); }
    } catch (err) { console.warn('[KokoroApp] Failed to load stats:', err); }
  },

  async loadPopularTags() {
    const container = document.getElementById('sidebar-popular-tags');
    if (!container) return;
    if (window.KokoroAuth && !window.KokoroAuth.currentUser) { container.innerHTML = ''; return; }
    if (window.KokoroTagManager) await window.KokoroTagManager.loadPopularTags(container, this.activeTagFilter, (tag) => this.setTagFilter(tag));
  },

  // -------------------------------------------------------------------------
  // DELEGATED VIEW RENDERING (TIMELINE, CALENDAR, MEMORIES, PROFILE)
  // -------------------------------------------------------------------------

  _getCardCallbacks() {
    return {
      onLoadMore: () => this.handleLoadMoreEntries(),
      onEdit: (id) => { const e = (this.entries && this.entries.find((i) => i.id === id)) || (this.allEntries && this.allEntries.find((i) => i.id === id)); if (e && window.Editor) window.Editor.open(e); },
      onDelete: (id) => this.openDeleteConfirm(id),
      onPin: (id) => this.togglePin(id),
      onExportCard: (id) => { const entry = (this.entries && this.entries.find((i) => i.id === id)) || (this.allEntries && this.allEntries.find((i) => i.id === id)); if (entry && window.KokoroCardExport) window.KokoroCardExport.open(entry); },
      onSelectTag: (tag) => this.setTagFilter(tag)
    };
  },

  getFilteredEntries() {
    return window.TimelineFeed ? window.TimelineFeed.getFilteredEntries(this.entries, this.timelineState, this.activeDateFilter) : this.entries;
  },

  buildEntryCardHtml(entry) {
    // Contracts: window.escapeHtml(entry.title) / window.escapeHtml(entry.content) / category-badge-pill / weatherBadgeHtml / weatherIcons / data-action="export-card"
    return window.TimelineFeed ? window.TimelineFeed.buildEntryCardHtml(entry, { activeTagFilter: this.activeTagFilter }) : '';
  },

  attachCardActions(container) {
    if (window.TimelineFeed) window.TimelineFeed.attachCardActions(container, this._getCardCallbacks());
  },

  renderTimeline() {
    this.renderDailyZenCard();
    const feedEl = document.getElementById('timeline-feed-container');
    if (feedEl && window.TimelineFeed) window.TimelineFeed.renderTimeline({ feedEl, filteredEntries: this.getFilteredEntries(), isLoading: this.isLoading, pagination: this.timelinePagination, activeTagFilter: this.activeTagFilter, callbacks: this._getCardCallbacks() });
  },

  handleLoadMoreEntries() {
    // Contracts: timeline-load-more-btn / timeline-end-indicator
    const feedEl = document.getElementById('timeline-feed-container');
    if (feedEl && window.TimelineFeed) window.TimelineFeed.handleLoadMoreEntries({ feedEl, filteredEntries: this.getFilteredEntries(), pagination: this.timelinePagination, activeTagFilter: this.activeTagFilter, callbacks: this._getCardCallbacks() });
  },

  renderMoodFilterChips() { if (window.TimelineFeed) window.TimelineFeed.renderMoodFilterChips({ sidebarContainer: document.getElementById('sidebar-mood-filters'), mobileContainer: document.getElementById('mobile-mood-chips'), categories: this.categories, totalEntries: this.allEntries.length, timelineState: this.timelineState, onSelectMood: (m, c) => this.setMoodFilter(m, c) }); },
  renderCalendar() { if (window.CalendarView) window.CalendarView.renderMiniCalendar({ gridEl: document.getElementById('mini-calendar-grid'), monthTitleEl: document.getElementById('cal-month-title'), entries: this.entries, activeDateFilter: this.activeDateFilter, onSelectDate: (d) => { this.setDateFilter(d); this.renderCalendar(); } }); },
  renderFullCalendar() {
    if (!window.CalendarView) return;
    window.CalendarView.renderFullCalendar({ gridEl: document.getElementById('full-calendar-grid'), monthTitleEl: document.getElementById('full-cal-month-title'), entries: this.entries, calYear: this.calYear, calMonth: this.calMonth, selectedCalDate: this.selectedCalDate, onSelectDate: (d) => { this.selectedCalDate = d; this.renderFullCalendar(); } });
    this.renderSelectedDateEntries();
  },
  renderSelectedDateEntries() {
    if (window.CalendarView) window.CalendarView.renderSelectedDateEntries({ listEl: document.getElementById('calendar-day-entries-list'), headingEl: document.getElementById('calendar-selected-date-heading'), entries: this.entries, selectedCalDate: this.selectedCalDate, cardBuilder: (e) => this.buildEntryCardHtml(e), attachCardActions: (el) => this.attachCardActions(el) });
  },
  renderMemoriesGallery() {
    if (window.MemoriesView) window.MemoriesView.renderMemoriesGallery({ gridEl: document.getElementById('memories-photo-grid'), badgeEl: document.getElementById('memories-total-badge'), tagScrollEl: document.getElementById('memories-tag-chips'), entries: (this.allEntries && this.allEntries.length > 0) ? this.allEntries : this.entries, memoriesState: this.memoriesState, activeMemoriesMood: this.activeMemoriesMood, onSelectTag: (t) => { this.memoriesState.tag = (this.memoriesState.tag === t) ? null : t; this.renderMemoriesGallery(); }, onPhotoClick: (s, t) => { if (window.Lightbox) window.Lightbox.open(s, t); } });
  },
  renderMemoriesMoodFilterChips() {
    if (window.MemoriesView) window.MemoriesView.renderMemoriesMoodFilterChips({ container: document.getElementById('memories-mood-scroll') || document.getElementById('memories-mood-filters'), categories: this.categories, memoriesState: this.memoriesState, onSelectMood: (m, c) => { this.activeMemoriesMood = m; this.memoriesState.mood = m; this.memoriesState.categoryId = c; this.renderMemoriesMoodFilterChips(); this.renderMemoriesGallery(); } });
  },
  updateMemoriesMoodBadges() { if (window.MemoriesView) window.MemoriesView.updateMemoriesMoodBadges(this.allEntries || this.entries, this.memoriesState); },
  renderProfileView() { if (window.ProfileStats) window.ProfileStats.renderProfileView({ user: window.KokoroAuth ? window.KokoroAuth.currentUser : null, entries: this.entries, stats: this.stats }); },
  renderStats() { if (window.ProfileStats) window.ProfileStats.renderStats({ entries: this.entries, stats: this.stats }); },
  renderMoodBreakdown(breakdown, total) { if (window.ProfileStats) window.ProfileStats.renderMoodBreakdown(breakdown, total); },
  updateMoodCountBadges(stats) { if (window.ProfileStats) window.ProfileStats.updateMoodCountBadges({ stats: stats || this.stats, entries: this.allEntries || this.entries, categories: this.categories }); },
  renderCategoryBadges(stats) { this.updateMoodCountBadges(stats); },

  // -------------------------------------------------------------------------
  // FILTERS & ACTIONS
  // -------------------------------------------------------------------------

  async setMoodFilter(mood, categoryId = null) {
    this.activeMoodFilter = mood; this.activeCategoryId = categoryId;
    this.timelineState.mood = mood; this.timelineState.categoryId = categoryId;
    this.activeTagFilter = null; this.timelineState.tag = null; this.activeDateFilter = null;
    this.timelinePagination.visibleLimit = (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15);
    const tc = document.getElementById('sidebar-popular-tags');
    if (tc) tc.querySelectorAll('.tag-pill').forEach((p) => p.classList.remove('active'));
    this.renderMoodFilterChips(); await this.loadEntries();
  },

  async setTagFilter(tag) {
    this.activeTagFilter = (this.activeTagFilter && this.activeTagFilter.toLowerCase() === tag.toLowerCase()) ? null : tag;
    this.timelineState.tag = this.activeTagFilter;
    this.timelinePagination.visibleLimit = (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15);
    const tc = document.getElementById('sidebar-popular-tags');
    if (tc) tc.querySelectorAll('.tag-pill').forEach((p) => p.classList.toggle('active', !!(this.activeTagFilter && this.activeTagFilter.toLowerCase() === p.dataset.tag.toLowerCase())));
    await this.loadEntries();
  },

  setDateFilter(dateStr) {
    this.activeDateFilter = (this.activeDateFilter === dateStr) ? null : dateStr;
    this.timelinePagination.visibleLimit = (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15);
    this.renderTimeline();
  },

  async togglePin(id) {
    try {
      await window.KokoroAPI.togglePin(id); await this.loadEntries();
      this.showToast('Đã cập nhật trạng thái ghim bài viết! 📌');
    } catch (err) { this.showToast('Lỗi ghim bài viết: ' + err.message, 'error'); }
  },
  openDeleteConfirm(id) {
    this.pendingDeleteId = id; const modal = document.getElementById('delete-confirm-modal') || document.getElementById('delete-modal');
    if (modal) { modal.classList.add('active'); modal.setAttribute('aria-hidden', 'false'); if (window.lockBodyScroll) window.lockBodyScroll(true); const b = document.getElementById('confirm-delete-btn') || document.getElementById('delete-confirm-btn'); if (b) b.focus(); }
  },
  closeDeleteConfirm() {
    this.pendingDeleteId = null; const modal = document.getElementById('delete-confirm-modal') || document.getElementById('delete-modal');
    if (modal) { modal.classList.remove('active'); modal.setAttribute('aria-hidden', 'true'); if (window.lockBodyScroll) window.lockBodyScroll(false); }
  },
  async confirmDelete() {
    if (!this.pendingDeleteId) return;
    try {
      await window.KokoroAPI.deleteEntry(this.pendingDeleteId);
      this.showToast('Đã xóa bài viết khỏi dòng thời gian 🍃');
      this.closeDeleteConfirm(); await this.loadEntries(); await this.loadStats();
    } catch (err) { this.showToast('Lỗi khi xóa bài viết: ' + err.message, 'error'); }
  },

  switchView(viewName, updateHistory = true) {
    if (!['timeline', 'calendar', 'memories', 'profile'].includes(viewName)) return;
    this.currentView = viewName;
    document.querySelectorAll('.c-view, .app-view').forEach((s) => { s.style.display = 'none'; s.classList.remove('active'); });
    const target = document.getElementById(`view-${viewName}`);
    if (target) { target.style.display = 'block'; target.classList.add('active'); }
    document.querySelectorAll('[data-switch-view]').forEach((b) => b.classList.toggle('active', b.dataset.switchView === viewName));
    document.querySelectorAll('.bottom-nav-item').forEach((b) => b.classList.toggle('active', b.dataset.tab === viewName));
    document.querySelectorAll('[data-view-target]').forEach((b) => b.classList.toggle('active', b.dataset.viewTarget === viewName));
    if (viewName === 'timeline') this.renderTimeline();
    else if (viewName === 'calendar') this.renderFullCalendar();
    else if (viewName === 'memories') this.renderMemoriesGallery();
    else if (viewName === 'profile') this.renderProfileView();
    if (updateHistory) { try { history.pushState({ view: viewName }, '', `#${viewName}`); } catch (err) {} }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  initTheme() { this.applyTheme(localStorage.getItem('kokoro_theme') || 'light'); },
  toggleTheme() { this.applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'); },
  async exportBackup() {
    try {
      this.showToast('Đang trích xuất bản sao lưu nhật ký... 🌸'); await window.KokoroAPI.exportEntries(); this.showToast('Đã tải bản sao lưu JSON thành công! ✨');
    } catch (err) { this.showToast('Lỗi tải bản sao lưu: ' + err.message, 'error'); }
  },
  async importBackup(file) {
    try {
      this.showToast('Đang khôi phục dữ liệu từ file... 🌸'); const res = await window.KokoroAPI.importEntries(file);
      this.showToast(res.message || 'Khôi phục dữ liệu thành công! ✨'); await this.loadCategories(); await this.loadEntries(); await this.loadStats();
    } catch (err) { this.showToast('Lỗi khôi phục: ' + err.message, 'error'); }
  },
  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kokoro_theme', theme);
    const icon = document.getElementById('theme-toggle-icon');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill text-sakura' : 'bi bi-sun-fill text-sakura';
    if (this.currentView === 'profile') this.renderProfileView();
  },

  renderDailyZenCard() {
    const cardEl = document.getElementById('daily-zen-card');
    if (!cardEl || !window.KokoroZenPrompt || window.KokoroZenPrompt.isDismissed()) { if (cardEl) cardEl.style.display = 'none'; return; }
    const prompt = window.KokoroZenPrompt.getDailyPrompt();
    if (!prompt) { if (cardEl) cardEl.style.display = 'none'; return; }
    this.activeZenPrompt = prompt;
    const iconEl = document.getElementById('zen-prompt-icon') || document.getElementById('daily-zen-icon'), textEl = document.getElementById('zen-prompt-text') || document.getElementById('daily-zen-text'), moodEl = document.getElementById('zen-prompt-pillar') || document.getElementById('daily-zen-mood');
    if (iconEl) iconEl.textContent = prompt.icon || '🌸';
    if (textEl) textEl.textContent = prompt.text;
    if (moodEl) moodEl.textContent = prompt.pillarName || `Gợi ý: ${prompt.suggestedMoodLabel || prompt.suggestedMood || 'Bình yên'}`;
    cardEl.classList.remove('collapsed'); cardEl.style.display = 'flex';
  },

  initZenPromptHandlers() {
    const cardEl = document.getElementById('daily-zen-card');
    if (!cardEl) return;
    const writeBtn = document.getElementById('zen-prompt-write-btn') || document.getElementById('daily-zen-write-btn');
    if (writeBtn) writeBtn.addEventListener('click', () => { if (this.activeZenPrompt && window.Editor) window.Editor.open(null, { prompt: this.activeZenPrompt, autoInsert: true }); });
    const shuffleBtn = document.getElementById('zen-prompt-shuffle-btn') || document.getElementById('daily-zen-shuffle-btn'), diceIcon = document.getElementById('zen-dice-icon') || (shuffleBtn?.querySelector('i'));
    if (shuffleBtn && window.KokoroZenPrompt) shuffleBtn.addEventListener('click', () => {
      if (diceIcon) { diceIcon.classList.remove('anim-spinning'); void diceIcon.offsetWidth; diceIcon.classList.add('anim-spinning'); }
      const p = window.KokoroZenPrompt, curId = this.activeZenPrompt?.id || null;
      if (typeof p.shufflePrompt === 'function') this.activeZenPrompt = p.shufflePrompt(curId);
      else if (typeof p.getRandomPrompt === 'function') this.activeZenPrompt = p.getRandomPrompt(curId);
      else if (typeof p.renderNewPrompt === 'function') this.activeZenPrompt = p.renderNewPrompt(curId);
      this.renderDailyZenCard(); this.showToast('Đã đổi gợi ý suy ngẫm mới ✨', 'info');
    });
    const dismissBtn = document.getElementById('zen-prompt-dismiss-btn') || document.getElementById('daily-zen-dismiss-btn');
    if (dismissBtn && window.KokoroZenPrompt) dismissBtn.addEventListener('click', () => {
      window.KokoroZenPrompt.setDismissed(null, true); cardEl.classList.add('collapsed');
      setTimeout(() => { cardEl.style.display = 'none'; }, 360); this.showToast('Đã ẩn gợi ý hôm nay 🍃', 'info');
    });
  },

  showToast(message, type = 'success') { if (window.KokoroToast) window.KokoroToast.show(message, type); }
};

window.KokoroApp = KokoroApp;
document.addEventListener('DOMContentLoaded', () => { KokoroApp.init(); });
