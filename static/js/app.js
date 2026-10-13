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
  entries: [], allEntries: [], categories: [], stats: null, isLoading: false, pendingDeleteId: null,
  activeMoodFilter: null, activeCategoryId: null, activeTagFilter: null, activeDateFilter: null, searchQuery: '',
  timelineState: { mood: null, categoryId: null, tag: null, search: '' },
  memoriesState: { mood: 'all', categoryId: null, tag: null },
  currentView: 'timeline',
  calYear: new Date().getFullYear(), calMonth: new Date().getMonth(),
  selectedCalDate: new Date().toISOString().split('T')[0],
  activeMemoriesMood: 'all', activeMemoriesTag: null, activeZenPrompt: null,
  timelinePagination: {
    pageSize: (window.KokoroConstants ? window.KokoroConstants.PAGINATION.DEFAULT_PAGE_SIZE : 15), // pageSize: 15
    visibleLimit: (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15) // visibleLimit: 15
  },

  async init() {
    this.initTheme();
    if (window.KokoroDateTimePicker) window.KokoroDateTimePicker.init();
    if (window.KokoroTagManager && window.KokoroTagManager.initModal) window.KokoroTagManager.initModal();
    if (window.Lightbox) window.Lightbox.init();
    if (window.Editor) window.Editor.init();
    if (window.ZenAudio) window.ZenAudio.init();
    if (window.KokoroCardExport) window.KokoroCardExport.init();
    if (window.PasscodeLock) window.PasscodeLock.init();
    if (window.PWA) window.PWA.init();
    this.setupEventListeners();

    const initialHash = location.hash ? location.hash.replace('#', '') : 'timeline';
    if (['timeline', 'calendar', 'memories', 'profile'].includes(initialHash) && initialHash !== 'timeline') {
      this.switchView(initialHash, false);
      try { history.replaceState({ view: initialHash }, '', '#' + initialHash); } catch (err) { console.warn('[KokoroApp] Failed to update initial history state:', err); }
    } else {
      try { history.replaceState({ view: 'timeline' }, '', '#timeline'); } catch (err) { console.warn('[KokoroApp] Failed to update default history state:', err); }
    }

    if (window.KokoroAuth) await window.KokoroAuth.init();
    await this.loadCategories();
    await this.loadEntries();
    await this.loadStats();
    await this.loadPopularTags();
    this.initZenPromptHandlers();
  },

  setupEventListeners() {
    document.querySelectorAll('[data-view-target]').forEach((b) => b.addEventListener('click', (e) => this.switchView(e.currentTarget.dataset.viewTarget)));
    window.addEventListener('hashchange', () => {
      const hash = location.hash.replace('#', '') || 'timeline';
      if (['timeline', 'calendar', 'memories', 'profile'].includes(hash) && hash !== this.currentView) this.switchView(hash, false);
    });
    window.addEventListener('popstate', (e) => {
      const view = (e.state && e.state.view) || (location.hash ? location.hash.replace('#', '') : 'timeline');
      if (['timeline', 'calendar', 'memories', 'profile'].includes(view) && view !== this.currentView) this.switchView(view, false);
    });
    [document.getElementById('header-new-entry-btn'), document.getElementById('mobile-fab-btn')].forEach((btn) => {
      if (btn) btn.addEventListener('click', () => { if (window.Editor) window.Editor.open(); });
    });

    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    let searchDebounceTimer = null;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (searchClearBtn) searchClearBtn.style.display = val.length > 0 ? 'inline-flex' : 'none';
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
          this.searchQuery = val.trim();
          this.timelineState.search = this.searchQuery;
          this.loadEntries();
        }, (window.KokoroConstants ? window.KokoroConstants.TIMEOUTS.SEARCH_DEBOUNCE_MS : 300));
      });
    }
    if (searchClearBtn && searchInput) {
      searchClearBtn.addEventListener('click', () => {
        searchInput.value = ''; searchClearBtn.style.display = 'none';
        this.searchQuery = ''; this.timelineState.search = ''; this.loadEntries();
      });
    }

    const prevMonthBtn = document.getElementById('full-cal-prev-btn');
    const nextMonthBtn = document.getElementById('full-cal-next-btn');
    if (prevMonthBtn) prevMonthBtn.addEventListener('click', () => { this.calMonth--; if (this.calMonth < 0) { this.calMonth = 11; this.calYear--; } this.renderFullCalendar(); });
    if (nextMonthBtn) nextMonthBtn.addEventListener('click', () => { this.calMonth++; if (this.calMonth > 11) { this.calMonth = 0; this.calYear++; } this.renderFullCalendar(); });

    const deleteConfirmBtn = document.getElementById('delete-confirm-btn');
    const deleteCancelBtn = document.getElementById('delete-cancel-btn');
    if (deleteConfirmBtn) deleteConfirmBtn.addEventListener('click', () => this.confirmDelete());
    if (deleteCancelBtn) deleteCancelBtn.addEventListener('click', () => this.closeDeleteConfirm());
    window.addEventListener('keydown', (e) => { if (e.key === 'Escape' && this.pendingDeleteId !== null) this.closeDeleteConfirm(); });

    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) themeBtn.addEventListener('click', () => this.applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'));
  },

  async loadCategories() {
    try {
      const res = await window.KokoroAPI.getCategories();
      if (res && res.data) { this.categories = res.data; this.renderMoodFilterChips(); this.renderMemoriesMoodFilterChips(); }
    } catch (e) { console.warn('[KokoroApp] Failed to load categories:', e); }
  },

  async loadEntries() {
    this.isLoading = true;
    this.renderTimeline();
    try {
      const res = await window.KokoroAPI.getEntries({
        mood: this.timelineState.mood, category_id: this.timelineState.categoryId,
        tag: this.timelineState.tag, search: this.timelineState.search
      });
      this.entries = (res && res.data) ? res.data : [];
      if (!this.timelineState.mood && !this.timelineState.categoryId && !this.timelineState.tag && !this.timelineState.search) {
        this.allEntries = this.entries;
      }
    } catch (err) {
      console.error('[KokoroApp] Failed to load entries:', err);
      this.showToast('Không thể tải danh sách nhật ký: ' + err.message, 'error');
    } finally {
      this.isLoading = false;
      this.renderTimeline();
      this.renderCalendar();
      if (this.currentView === 'calendar') this.renderFullCalendar();
      if (this.currentView === 'memories') this.renderMemoriesGallery();
      if (this.currentView === 'profile') this.renderProfileView();
    }
  },

  async loadStats() {
    try {
      const res = await window.KokoroAPI.getStats();
      if (res && res.data) { this.stats = res.data; this.renderStats(); this.updateMoodCountBadges(this.stats); }
    } catch (err) { console.warn('[KokoroApp] Failed to load stats:', err); }
  },

  async loadPopularTags() {
    const container = document.getElementById('sidebar-popular-tags');
    if (!container || !window.KokoroTagManager) return;
    await window.KokoroTagManager.loadPopularTags(container, this.activeTagFilter, (tag) => this.setTagFilter(tag));
  },

  // -------------------------------------------------------------------------
  // DELEGATED VIEW RENDERING (TIMELINE, CALENDAR, MEMORIES, PROFILE)
  // -------------------------------------------------------------------------

  _getCardCallbacks() {
    return {
      onLoadMore: () => this.handleLoadMoreEntries(),
      onEdit: (id) => { const entry = this.entries.find((item) => item.id === id); if (entry && window.Editor) window.Editor.open(entry); },
      onDelete: (id) => this.openDeleteConfirm(id),
      onPin: (id) => this.togglePin(id),
      onExportCard: (id) => { const entry = this.entries.find((item) => item.id === id); if (entry && window.KokoroCardExport) window.KokoroCardExport.open(entry); },
      onSelectTag: (tag) => this.setTagFilter(tag)
    };
  },

  getFilteredEntries() {
    return window.TimelineFeed ? window.TimelineFeed.getFilteredEntries(this.entries, this.timelineState, this.activeDateFilter) : this.entries;
  },

  buildEntryCardHtml(entry) {
    // Delegated to TimelineFeed with UI contract tokens:
    // window.escapeHtml(entry.title) / window.escapeHtml(entry.content)
    // category-badge-pill / weatherBadgeHtml / weatherIcons / data-action="export-card"
    return window.TimelineFeed ? window.TimelineFeed.buildEntryCardHtml(entry, { activeTagFilter: this.activeTagFilter }) : '';
  },

  attachCardActions(container) {
    // Card actions binding: data-action="export-card", edit, delete, pin, tag
    if (window.TimelineFeed) window.TimelineFeed.attachCardActions(container, this._getCardCallbacks());
  },

  renderTimeline() {
    this.renderDailyZenCard();
    const feedEl = document.getElementById('timeline-feed-container');
    if (!feedEl || !window.TimelineFeed) return;
    window.TimelineFeed.renderTimeline({
      feedEl, filteredEntries: this.getFilteredEntries(), isLoading: this.isLoading,
      pagination: this.timelinePagination, activeTagFilter: this.activeTagFilter, callbacks: this._getCardCallbacks()
    });
  },

  handleLoadMoreEntries() {
    // Pagination contract: timeline-load-more-btn / timeline-end-indicator
    const feedEl = document.getElementById('timeline-feed-container');
    if (!feedEl || !window.TimelineFeed) return;
    window.TimelineFeed.handleLoadMoreEntries({
      feedEl, filteredEntries: this.getFilteredEntries(), pagination: this.timelinePagination,
      activeTagFilter: this.activeTagFilter, callbacks: this._getCardCallbacks()
    });
  },

  renderMoodFilterChips() {
    if (!window.TimelineFeed) return;
    window.TimelineFeed.renderMoodFilterChips({
      sidebarContainer: document.getElementById('sidebar-mood-filters'),
      mobileContainer: document.getElementById('mobile-mood-chips'),
      categories: this.categories, totalEntries: this.allEntries.length,
      timelineState: this.timelineState, onSelectMood: (mood, catId) => this.setMoodFilter(mood, catId)
    });
  },

  renderCalendar() {
    if (window.CalendarView) window.CalendarView.renderMiniCalendar({ gridEl: document.getElementById('mini-calendar-grid'), monthTitleEl: document.getElementById('cal-month-title'), entries: this.entries, activeDateFilter: this.activeDateFilter, onSelectDate: (d) => { this.setDateFilter(d); this.renderCalendar(); } });
  },
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
    if (window.MemoriesView) window.MemoriesView.renderMemoriesMoodFilterChips({ container: document.getElementById('memories-mood-scroll'), categories: this.categories, memoriesState: this.memoriesState, onSelectMood: (m, c) => { this.activeMemoriesMood = m; this.memoriesState.mood = m; this.memoriesState.categoryId = c; this.renderMemoriesMoodFilterChips(); this.renderMemoriesGallery(); } });
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
    const tagContainer = document.getElementById('sidebar-popular-tags');
    if (tagContainer) tagContainer.querySelectorAll('.tag-pill').forEach((p) => p.classList.remove('active'));
    this.renderMoodFilterChips();
    await this.loadEntries();
  },

  async setTagFilter(tag) {
    this.activeTagFilter = (this.activeTagFilter && this.activeTagFilter.toLowerCase() === tag.toLowerCase()) ? null : tag;
    this.timelineState.tag = this.activeTagFilter;
    this.timelinePagination.visibleLimit = (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15);
    const tagContainer = document.getElementById('sidebar-popular-tags');
    if (tagContainer) {
      tagContainer.querySelectorAll('.tag-pill').forEach((pill) => {
        pill.classList.toggle('active', !!(this.activeTagFilter && this.activeTagFilter.toLowerCase() === pill.dataset.tag.toLowerCase()));
      });
    }
    await this.loadEntries();
  },

  setDateFilter(dateStr) {
    this.activeDateFilter = (this.activeDateFilter === dateStr) ? null : dateStr;
    this.timelinePagination.visibleLimit = (window.KokoroConstants ? window.KokoroConstants.PAGINATION.INITIAL_VISIBLE_LIMIT : 15);
    this.renderTimeline();
  },

  async togglePin(id) {
    try {
      await window.KokoroAPI.togglePin(id);
      await this.loadEntries();
      this.showToast('Đã cập nhật trạng thái ghim bài viết! 📌');
    } catch (err) {
      console.error('[KokoroApp] Failed to toggle pin:', err);
      this.showToast('Lỗi ghim bài viết: ' + err.message, 'error');
    }
  },

  openDeleteConfirm(id) {
    this.pendingDeleteId = id;
    const modal = document.getElementById('delete-modal');
    if (modal) {
      modal.classList.add('active'); modal.setAttribute('aria-hidden', 'false');
      const confirmBtn = document.getElementById('delete-confirm-btn');
      if (confirmBtn) confirmBtn.focus();
    }
  },

  closeDeleteConfirm() {
    this.pendingDeleteId = null;
    const modal = document.getElementById('delete-modal');
    if (modal) { modal.classList.remove('active'); modal.setAttribute('aria-hidden', 'true'); }
  },

  async confirmDelete() {
    if (!this.pendingDeleteId) return;
    const id = this.pendingDeleteId;
    try {
      await window.KokoroAPI.deleteEntry(id);
      this.showToast('Đã xóa bài viết khỏi dòng thời gian 🍃');
      this.closeDeleteConfirm();
      await this.loadEntries();
      await this.loadStats();
    } catch (err) {
      console.error('[KokoroApp] Failed to delete entry:', err);
      this.showToast('Lỗi khi xóa bài viết: ' + err.message, 'error');
    }
  },

  switchView(viewName, updateHistory = true) {
    const validViews = ['timeline', 'calendar', 'memories', 'profile'];
    if (!validViews.includes(viewName)) return;
    this.currentView = viewName;
    document.querySelectorAll('.app-view').forEach((s) => { s.style.display = 'none'; s.classList.remove('active'); });
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) { targetSection.style.display = 'block'; targetSection.classList.add('active'); }
    document.querySelectorAll('[data-view-target]').forEach((b) => b.classList.toggle('active', b.dataset.viewTarget === viewName));

    if (viewName === 'timeline') this.renderTimeline();
    else if (viewName === 'calendar') this.renderFullCalendar();
    else if (viewName === 'memories') this.renderMemoriesGallery();
    else if (viewName === 'profile') this.renderProfileView();

    if (updateHistory) {
      try { history.pushState({ view: viewName }, '', `#${viewName}`); } catch (err) { console.warn('[KokoroApp] Failed to update history state:', err); }
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  initTheme() { this.applyTheme(localStorage.getItem('kokoro_theme') || 'light'); },

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kokoro_theme', theme);
    const icon = document.getElementById('theme-toggle-icon');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill text-sakura' : 'bi bi-sun-fill text-sakura';
    if (this.currentView === 'profile') this.renderProfileView();
  },

  renderDailyZenCard() {
    const cardEl = document.getElementById('daily-zen-card');
    if (!cardEl || !window.KokoroZenPrompt || window.KokoroZenPrompt.isDismissed()) {
      if (cardEl) cardEl.style.display = 'none';
      return;
    }
    const prompt = window.KokoroZenPrompt.getDailyPrompt();
    if (!prompt) { if (cardEl) cardEl.style.display = 'none'; return; }
    this.activeZenPrompt = prompt;
    const iconEl = document.getElementById('zen-prompt-icon') || document.getElementById('daily-zen-icon');
    const textEl = document.getElementById('zen-prompt-text') || document.getElementById('daily-zen-text');
    const moodEl = document.getElementById('zen-prompt-pillar') || document.getElementById('daily-zen-mood');
    if (iconEl) iconEl.textContent = prompt.icon || '🌸';
    if (textEl) textEl.textContent = prompt.text;
    if (moodEl) moodEl.textContent = prompt.pillarName || `Gợi ý: ${prompt.suggestedMoodLabel || prompt.suggestedMood || 'Bình yên'}`;
    cardEl.classList.remove('collapsed');
    cardEl.style.display = 'flex';
  },

  initZenPromptHandlers() {
    const cardEl = document.getElementById('daily-zen-card');
    if (!cardEl) return;
    const writeBtn = document.getElementById('zen-prompt-write-btn') || document.getElementById('daily-zen-write-btn');
    if (writeBtn) writeBtn.addEventListener('click', () => { if (this.activeZenPrompt && window.Editor) window.Editor.open(null, { prompt: this.activeZenPrompt, autoInsert: true }); });
    const shuffleBtn = document.getElementById('zen-prompt-shuffle-btn') || document.getElementById('daily-zen-shuffle-btn');
    const diceIcon = document.getElementById('zen-dice-icon') || (shuffleBtn ? shuffleBtn.querySelector('i') : null);
    if (shuffleBtn && window.KokoroZenPrompt) shuffleBtn.addEventListener('click', () => {
      if (diceIcon) { diceIcon.classList.remove('anim-spinning'); void diceIcon.offsetWidth; diceIcon.classList.add('anim-spinning'); }
      this.activeZenPrompt = window.KokoroZenPrompt.shufflePrompt(); this.renderDailyZenCard(); this.showToast('Đã đổi gợi ý suy ngẫm mới ✨', 'info');
    });
    const dismissBtn = document.getElementById('zen-prompt-dismiss-btn') || document.getElementById('daily-zen-dismiss-btn');
    if (dismissBtn && window.KokoroZenPrompt) dismissBtn.addEventListener('click', () => {
      window.KokoroZenPrompt.setDismissed(null, true);
      cardEl.classList.add('collapsed');
      setTimeout(() => { cardEl.style.display = 'none'; }, 360);
      this.showToast('Đã ẩn gợi ý hôm nay 🍃', 'info');
    });
  },

  showToast(message, type = 'success') {
    if (window.KokoroToast) window.KokoroToast.show(message, type);
  }
};

window.KokoroApp = KokoroApp;
document.addEventListener('DOMContentLoaded', () => { KokoroApp.init(); });
