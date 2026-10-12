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
  currentView: 'timeline',
  calYear: new Date().getFullYear(),
  calMonth: new Date().getMonth(),
  selectedCalDate: new Date().toISOString().split('T')[0],
  activeMemoriesMood: 'all',
  stats: null,

  async init() {
    this.initTheme();

    // Initialize submodules
    if (window.Lightbox) window.Lightbox.init();
    if (window.Editor) window.Editor.init();
    if (window.ZenAudio) window.ZenAudio.init();
    if (window.PasscodeLock) window.PasscodeLock.init();
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

    // Reset Editor form & data model completely to prevent draft / photo leakage
    if (window.Editor) {
      window.Editor.resetForm();
    }

    // Dynamic greeting (Friendly name logic)
    const greetingEl = document.querySelector('#welcome-greeting-title, .welcome-banner-card h1, .timeline-feed h1');
    if (greetingEl) {
      let displayName = 'bạn';
      if (user) {
        if (user.nickname) {
          displayName = user.nickname;
        } else if (user.preferredName || user.preferred_name) {
          displayName = user.preferredName || user.preferred_name;
        } else if (user.name) {
          const cleanName = user.name.replace(/\s*\([^)]*\)/g, '').trim();
          const parts = cleanName.split(/\s+/).filter(Boolean);
          displayName = parts[parts.length - 1] || cleanName || 'bạn';
        }
      }
      greetingEl.textContent = `Chào ${displayName}, hôm nay bạn cảm thấy thế nào? 🌸`;
    }

    if (user) {
      let pinLocked = false;
      if (window.PasscodeLock) {
        window.PasscodeLock.onUserChanged(user.id);
        pinLocked = window.PasscodeLock.isLocked;
      }

      // If PIN lock is active, do NOT load entries into DOM until user enters PIN
      if (pinLocked) {
        this.entries = [];
        this.renderTimeline();
        this.renderCalendar();
        this.renderMemoriesGallery();
        this.renderProfileView();
        this.renderStats();
      } else {
        await this.loadEntries();
        await this.loadStats();
        this.renderTimeline();
        this.renderCalendar();
        this.renderMemoriesGallery();
        this.renderProfileView();
      }
    } else {
      this.entries = [];
      this.renderTimeline();
      this.renderCalendar();
      this.renderMemoriesGallery();
      this.renderProfileView();
      this.renderStats();
    }
  },

  async onPinUnlocked() {
    await this.loadEntries();
    await this.loadStats();
    this.renderTimeline();
    this.renderCalendar();
    this.renderMemoriesGallery();
    this.renderProfileView();
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

    // Event Delegation: Profile Pill & Dropdown Menu Toggle (SSoT)
    document.addEventListener('click', (e) => {
      const pill = e.target.closest('#header-profile-pill, .header-profile-pill, #user-profile-btn, #user-profile-pill');
      const dropdown = document.querySelector('#profile-dropdown-menu, .profile-dropdown-menu');

      if (pill) {
        e.stopPropagation();
        dropdown?.classList.toggle('active');
        dropdown?.classList.toggle('show');
        return;
      }

      if (dropdown && !e.target.closest('#profile-dropdown-menu, .profile-dropdown-menu')) {
        dropdown.classList.remove('active', 'show');
      }
    });

    // Close dropdown after clicking any item inside
    document.addEventListener('click', (e) => {
      if (e.target.closest('#profile-dropdown-menu .dropdown-item')) {
        const dropdown = document.querySelector('#profile-dropdown-menu, .profile-dropdown-menu');
        if (dropdown) {
          setTimeout(() => {
            dropdown.classList.remove('active', 'show');
          }, 150);
        }
      }
    });

    // Mood filter chips in sidebar and mobile scroll
    const moodFilterBtns = document.querySelectorAll('[data-filter-mood]');
    moodFilterBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const mood = e.currentTarget.dataset.filterMood;
        this.setMoodFilter(mood);
      });
    });

    // Multi-View Bottom Navigation (Mobile)
    const navItems = document.querySelectorAll('.bottom-nav-item');
    navItems.forEach((item) => {
      item.addEventListener('click', () => {
        const tab = item.dataset.tab;
        if (tab === 'editor') {
          if (window.Editor) window.Editor.open();
        } else {
          this.switchView(tab);
        }
      });
    });

    // Multi-View Desktop Tab Switcher
    const desktopTabs = document.querySelectorAll('[data-switch-view]');
    desktopTabs.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const v = e.currentTarget.dataset.switchView;
        this.switchView(v);
      });
    });

    // Full Calendar Navigation Handlers
    const calPrevBtn = document.getElementById('full-cal-prev-btn');
    if (calPrevBtn) {
      calPrevBtn.addEventListener('click', () => {
        this.calMonth--;
        if (this.calMonth < 0) {
          this.calMonth = 11;
          this.calYear--;
        }
        this.renderFullCalendar();
      });
    }

    const calNextBtn = document.getElementById('full-cal-next-btn');
    if (calNextBtn) {
      calNextBtn.addEventListener('click', () => {
        this.calMonth++;
        if (this.calMonth > 11) {
          this.calMonth = 0;
          this.calYear++;
        }
        this.renderFullCalendar();
      });
    }

    const calTodayBtn = document.getElementById('full-cal-today-btn');
    if (calTodayBtn) {
      calTodayBtn.addEventListener('click', () => {
        const now = new Date();
        this.calYear = now.getFullYear();
        this.calMonth = now.getMonth();
        this.selectedCalDate = now.toISOString().split('T')[0];
        this.renderFullCalendar();
      });
    }

    const calAddDateBtn = document.getElementById('calendar-add-date-btn');
    if (calAddDateBtn) {
      calAddDateBtn.addEventListener('click', () => {
        if (window.Editor) {
          window.Editor.open();
        }
      });
    }

    // Memories Mood Filter Chips
    const memMoodBtns = document.querySelectorAll('[data-memories-mood]');
    memMoodBtns.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        memMoodBtns.forEach((b) => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.activeMemoriesMood = e.currentTarget.dataset.memoriesMood;
        this.renderMemoriesGallery();
      });
    });

    // Profile Actions Event Handlers
    const profilePinBtn = document.getElementById('profile-action-pin');
    if (profilePinBtn) {
      profilePinBtn.addEventListener('click', () => {
        const sBtn = document.getElementById('passcode-settings-btn');
        if (sBtn) sBtn.click();
      });
    }

    const profileLockNow = document.getElementById('profile-action-lock-now');
    if (profileLockNow) {
      profileLockNow.addEventListener('click', () => {
        const lBtn = document.getElementById('lock-screen-now-btn');
        if (lBtn) lBtn.click();
      });
    }

    const profileThemeBtn = document.getElementById('profile-action-theme');
    if (profileThemeBtn) {
      profileThemeBtn.addEventListener('click', () => {
        const tBtn = document.getElementById('theme-toggle-btn');
        if (tBtn) tBtn.click();
        this.renderProfileView();
      });
    }

    const profileExport = document.getElementById('profile-action-export');
    if (profileExport) {
      profileExport.addEventListener('click', () => {
        const eBtn = document.getElementById('export-backup-btn');
        if (eBtn) eBtn.click();
      });
    }

    const profileImport = document.getElementById('profile-action-import');
    if (profileImport) {
      profileImport.addEventListener('click', () => {
        const iBtn = document.getElementById('import-backup-btn');
        if (iBtn) iBtn.click();
      });
    }

    const profilePwa = document.getElementById('profile-action-pwa');
    if (profilePwa) {
      profilePwa.addEventListener('click', () => {
        const pBtn = document.getElementById('pwa-install-btn');
        if (pBtn) pBtn.click();
      });
    }

    const profileLogout = document.getElementById('profile-action-logout');
    if (profileLogout) {
      profileLogout.addEventListener('click', () => {
        const lBtn = document.getElementById('logout-btn');
        if (lBtn) lBtn.click();
      });
    }

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

    // Passcode Lock Menu & Settings events
    const lockNowBtn = document.getElementById('lock-screen-now-btn');
    if (lockNowBtn) {
      lockNowBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.PasscodeLock) window.PasscodeLock.lockNow();
      });
    }

    const passcodeSettingsBtn = document.getElementById('passcode-settings-btn');
    if (passcodeSettingsBtn) {
      passcodeSettingsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.PasscodeLock) window.PasscodeLock.openSetupModal();
      });
    }

    const closePasscodeSettingsBtn = document.getElementById('passcode-close-settings-btn');
    if (closePasscodeSettingsBtn) {
      closePasscodeSettingsBtn.addEventListener('click', () => {
        if (window.PasscodeLock) window.PasscodeLock.closeSetupModal();
      });
    }

    const passcodeToggleSwitch = document.getElementById('passcode-toggle-switch');
    if (passcodeToggleSwitch) {
      passcodeToggleSwitch.addEventListener('change', (e) => {
        if (!window.PasscodeLock) return;
        if (e.target.checked) {
          window.PasscodeLock.startSetNewPinFlow();
        } else {
          window.PasscodeLock.disablePin();
          window.PasscodeLock.updateSettingsModalState();
          window.PasscodeLock.updateProfileMenuUi();
          this.showToast('Đã tắt khóa bảo mật mã PIN 🌸');
        }
      });
    }

    const passcodeChangeBtn = document.getElementById('passcode-change-btn');
    if (passcodeChangeBtn) {
      passcodeChangeBtn.addEventListener('click', () => {
        if (window.PasscodeLock) window.PasscodeLock.startSetNewPinFlow();
      });
    }

    const passcodeTimeoutSelect = document.getElementById('passcode-timeout-select');
    if (passcodeTimeoutSelect) {
      passcodeTimeoutSelect.addEventListener('change', (e) => {
        if (window.PasscodeLock) {
          localStorage.setItem(`kokoro_pin_timeout_${window.PasscodeLock.currentUserId}`, e.target.value);
          this.showToast('Đã cập nhật thời gian tự động khóa ✨');
        }
      });
    }
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
      if (this.currentView === 'calendar') this.renderFullCalendar();
      if (this.currentView === 'memories') this.renderMemoriesGallery();
      if (this.currentView === 'profile') this.renderProfileView();
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
        this.stats = res;
        const totalEl = document.getElementById('stat-total-entries');
        const streakEl = document.getElementById('stat-writing-streak');
        const photosEl = document.getElementById('stat-photos-count');

        if (totalEl) totalEl.textContent = res.totalEntries;
        if (streakEl) streakEl.textContent = `${res.streakDays || 0} ngày`;
        if (photosEl) photosEl.innerHTML = `<i class="bi bi-camera text-sakura"></i> ${res.totalPhotos || 0} ảnh`;

        this.renderMoodBreakdown(res.moodBreakdown, res.totalEntries);
        if (this.currentView === 'profile') this.renderProfileView();
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

    const dropdownThemeBtn = document.getElementById('dropdown-theme-toggle-btn');
    if (dropdownThemeBtn) {
      dropdownThemeBtn.addEventListener('click', () => {
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
    const dropdownIcon = document.getElementById('dropdown-theme-icon');
    if (dropdownIcon) {
      dropdownIcon.className = theme === 'dark' ? 'bi bi-sun-fill text-warning' : 'bi bi-moon-stars text-sakura';
    }
    const dropdownBadge = document.getElementById('dropdown-theme-badge');
    if (dropdownBadge) {
      dropdownBadge.textContent = theme === 'dark' ? 'Tối' : 'Sáng';
      dropdownBadge.className = theme === 'dark' ? 'badge-pill badge-active' : 'badge-pill badge-inactive';
    }
  },

  openDeleteConfirm(id) {
    this.pendingDeleteId = id;
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
      modal.classList.add('active');
      if (window.lockBodyScroll) window.lockBodyScroll(true);
    }
  },

  closeDeleteConfirm() {
    this.pendingDeleteId = null;
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
      modal.classList.remove('active');
      if (window.lockBodyScroll) window.lockBodyScroll(false);
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
    this.attachCardActions(feedEl);
  },

  /**
   * Attach card actions (lightbox, edit, delete, pin, tag filter) to any entry list container
   */
  attachCardActions(container) {
    if (!container) return;

    // Attach listeners for image clicks (Lightbox) & card buttons
    container.querySelectorAll('.gallery-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        const fullSrc = item.dataset.fullSrc;
        const img = item.querySelector('img');
        if (window.Lightbox) {
          window.Lightbox.open(fullSrc || (img ? img.src : ''), img ? img.alt : '');
        }
      });
    });

    container.querySelectorAll('[data-action="edit"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        const entry = this.entries.find((item) => item.id === id);
        if (entry && window.Editor) {
          window.Editor.open(entry);
        }
      });
    });

    container.querySelectorAll('[data-action="delete"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        this.openDeleteConfirm(id);
      });
    });

    container.querySelectorAll('[data-action="pin"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        this.togglePin(id);
      });
    });

    container.querySelectorAll('.tag-pill').forEach((tagBtn) => {
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
        <div class="card-header entry-card-header">
          <div class="card-meta card-meta-left">
            <span class="mood-pill mood-${entry.mood}">${entry.moodLabel || entry.mood}</span>
            <span class="card-meta-dot">&bull;</span>
            <span class="card-meta-time entry-date"><i class="bi bi-clock"></i> ${entry.displayDate || entry.entryDate}</span>
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
   * Router View Switcher
   * @param {'timeline'|'calendar'|'memories'|'profile'} viewName
   */
  switchView(viewName) {
    if (!['timeline', 'calendar', 'memories', 'profile'].includes(viewName)) return;
    this.currentView = viewName;

    // 1. Toggle active class on view containers
    document.querySelectorAll('.c-view').forEach((el) => el.classList.remove('active'));
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) targetView.classList.add('active');

    // 2. Update Mobile Bottom Nav active state
    document.querySelectorAll('.bottom-nav-item').forEach((item) => {
      if (item.dataset.tab === viewName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // 3. Update Desktop View Switcher active state
    document.querySelectorAll('[data-switch-view]').forEach((btn) => {
      if (btn.dataset.switchView === viewName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 4. Render corresponding view content
    if (viewName === 'timeline') {
      this.renderTimeline();
    } else if (viewName === 'calendar') {
      this.renderFullCalendar();
    } else if (viewName === 'memories') {
      this.renderMemoriesGallery();
    } else if (viewName === 'profile') {
      this.renderProfileView();
    }

    // 5. Toggle mobile mood chips visibility (Mobile ONLY <= 768px):
    // Never show mobile horizontal scroll chips on Desktop/Tablet
    const mobileMoodChips = document.getElementById('mobile-mood-chips');
    if (mobileMoodChips) {
      if (window.innerWidth <= 768 && (viewName === 'timeline' || viewName === 'memories')) {
        mobileMoodChips.style.display = 'flex';
      } else {
        mobileMoodChips.style.display = 'none';
      }
    }

    // 6. Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  /**
   * View 2: Render Interactive Full Month Calendar with Mood Dots & Day's Entries
   */
  renderFullCalendar() {
    const gridEl = document.getElementById('full-calendar-grid');
    if (!gridEl) return;

    const currentYear = this.calYear;
    const currentMonth = this.calMonth;

    // Month Title
    const monthTitleEl = document.getElementById('full-cal-month-title');
    if (monthTitleEl) {
      const monthNames = [
        'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
      ];
      monthTitleEl.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    }

    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay(); // 0: Sun
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    // Map dates to moods array
    const dateToMoods = {};
    this.entries.forEach((e) => {
      if (e.entryDate) {
        if (!dateToMoods[e.entryDate]) dateToMoods[e.entryDate] = [];
        if (e.mood && !dateToMoods[e.entryDate].includes(e.mood)) {
          dateToMoods[e.entryDate].push(e.mood);
        }
      }
    });

    let html = `
      <div class="c-calendar-weekday">CN</div>
      <div class="c-calendar-weekday">T2</div>
      <div class="c-calendar-weekday">T3</div>
      <div class="c-calendar-weekday">T4</div>
      <div class="c-calendar-weekday">T5</div>
      <div class="c-calendar-weekday">T6</div>
      <div class="c-calendar-weekday">T7</div>
    `;

    // Empty spaces before first day
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<div class="c-calendar-day empty"></div>`;
    }

    const moodColorMap = {
      serene: 'var(--mood-serene)',
      cozy: 'var(--mood-cozy)',
      reflective: 'var(--mood-reflective)',
      grateful: 'var(--mood-grateful)',
      energetic: 'var(--mood-energetic)',
      melancholy: 'var(--mood-melancholy)'
    };

    // Days in Month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = dateStr === todayStr;
      const isSelected = dateStr === this.selectedCalDate;
      const dayMoods = dateToMoods[dateStr] || [];
      const hasEntries = dayMoods.length > 0;

      let dotsHtml = '';
      if (hasEntries) {
        dotsHtml = dayMoods
          .slice(0, 4)
          .map((m) => `<span class="c-calendar-dot" style="background: ${moodColorMap[m] || 'var(--sakura-400)'};"></span>`)
          .join('');
      }

      html += `
        <div class="c-calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''} ${hasEntries ? 'has-entry' : ''}" 
             data-full-date="${dateStr}">
          <span class="c-calendar-day-num">${day}</span>
          <div class="c-calendar-dots">${dotsHtml}</div>
        </div>
      `;
    }

    gridEl.innerHTML = html;

    // Attach click listeners to calendar day cells
    gridEl.querySelectorAll('.c-calendar-day[data-full-date]').forEach((cell) => {
      cell.addEventListener('click', (e) => {
        const d = e.currentTarget.dataset.fullDate;
        this.selectedCalDate = d;
        this.renderFullCalendar();
      });
    });

    // Render entries for selected date
    this.renderSelectedDateEntries();
  },

  /**
   * Render list of entries for selected calendar date
   */
  renderSelectedDateEntries() {
    const listEl = document.getElementById('calendar-day-entries-list');
    const headingEl = document.getElementById('calendar-selected-date-heading');
    if (!listEl) return;

    if (headingEl && this.selectedCalDate) {
      const [y, m, d] = this.selectedCalDate.split('-');
      headingEl.textContent = `Khoảnh khắc ngày ${d}/${m}/${y} 🌸`;
    }

    const matchedEntries = this.entries.filter((e) => e.entryDate === this.selectedCalDate);

    if (matchedEntries.length === 0) {
      listEl.innerHTML = `
        <div class="glass-panel" style="padding: 32px 20px; text-align: center; border-radius: var(--radius-lg);">
          <div style="font-size: 32px; margin-bottom: 8px;">🍃</div>
          <div style="font-size: 14.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Chưa có khoảnh khắc nào trong ngày này</div>
          <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 16px;">Lắng đọng tâm trí và ghi lại những điều nhẹ nhàng của bạn nhé.</div>
          <button class="c-btn c-btn--primary" onclick="if(window.Editor){ window.Editor.open(); }">
            <i class="bi bi-pencil-square"></i> + Ghi nhật ký cho ngày này
          </button>
        </div>
      `;
      return;
    }

    listEl.innerHTML = matchedEntries.map((e) => this.buildEntryCardHtml(e)).join('');
    this.attachCardActions(listEl);
  },

  /**
   * View 3: Render Memories Photo Gallery Grid with Mood Filter & Lightbox Integration
   */
  renderMemoriesGallery() {
    const gridEl = document.getElementById('memories-photo-grid');
    const badgeEl = document.getElementById('memories-total-badge');
    if (!gridEl) return;

    // Collect all photos across all entries
    const allPhotos = [];
    this.entries.forEach((e) => {
      if (e.photos && e.photos.length > 0) {
        e.photos.forEach((p) => {
          allPhotos.push({
            ...p,
            entryId: e.id,
            entryTitle: e.title,
            entryDate: e.entryDate,
            displayDate: e.displayDate || e.entryDate,
            mood: e.mood,
            moodLabel: e.moodLabel || e.mood
          });
        });
      }
    });

    // Filter by active memories mood
    let filteredPhotos = allPhotos;
    if (this.activeMemoriesMood && this.activeMemoriesMood !== 'all') {
      filteredPhotos = allPhotos.filter((p) => p.mood === this.activeMemoriesMood);
    }

    if (badgeEl) {
      badgeEl.textContent = `📸 ${filteredPhotos.length} ảnh`;
    }

    if (filteredPhotos.length === 0) {
      gridEl.innerHTML = `
        <div class="glass-panel" style="padding: 44px 20px; text-align: center; grid-column: 1 / -1; border-radius: var(--radius-lg);">
          <div style="font-size: 38px; margin-bottom: 8px;">📷</div>
          <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Chưa có hình ảnh kỷ niệm nào</div>
          <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 18px;">Hãy đính kèm hình ảnh vào các bài viết nhật ký để lưu giữ kỷ niệm tại đây nhé! 🌸</div>
          <button class="c-btn c-btn--primary" onclick="if(window.Editor){ window.Editor.open(); }">
            <i class="bi bi-plus-lg"></i> Viết bài & Thêm ảnh
          </button>
        </div>
      `;
      return;
    }

    gridEl.innerHTML = filteredPhotos
      .map((p) => {
        const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
        const fullUrl = window.KokoroAPI.resolveMediaUrl(p.url);
        return `
          <div class="c-memory-item" data-full-src="${fullUrl}" data-title="${p.entryTitle || ''}" data-date="${p.displayDate || ''}">
            <img src="${thumbUrl}" alt="${p.name || 'Memory Photo'}" loading="lazy" />
            <div class="c-memory-overlay">
              <span class="c-memory-title">${p.entryTitle || 'Khoảnh khắc'}</span>
              <span class="c-memory-meta"><i class="bi bi-clock"></i> ${p.displayDate} &bull; ${p.moodLabel}</span>
            </div>
          </div>
        `;
      })
      .join('');

    // Attach click listener to open Fullscreen Lightbox
    gridEl.querySelectorAll('.c-memory-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        const fullSrc = e.currentTarget.dataset.fullSrc;
        const title = e.currentTarget.dataset.title;
        const date = e.currentTarget.dataset.date;
        if (window.Lightbox) {
          window.Lightbox.open(fullSrc, `${title} (${date})`);
        }
      });
    });
  },

  /**
   * View 4: Render Profile View & Management Utilities
   */
  renderProfileView() {
    const user = window.KokoroAuth ? window.KokoroAuth.currentUser : null;

    // 1. User Header
    const avatarEl = document.getElementById('profile-view-avatar');
    const nameEl = document.getElementById('profile-view-name');
    const emailEl = document.getElementById('profile-view-email');

    if (avatarEl) avatarEl.src = user ? user.avatar_url || './icons/sakura.svg' : './icons/sakura.svg';
    if (nameEl) nameEl.textContent = user ? user.name : 'Khách vãng lai';
    if (emailEl) emailEl.textContent = user ? user.email : 'chua_dang_nhap@kokoro.me';

    // 2. Metrics & Stats
    const entriesCountEl = document.getElementById('profile-stat-entries');
    const streakEl = document.getElementById('profile-stat-streak');
    const photosCountEl = document.getElementById('profile-stat-photos');

    let totalPhotos = 0;
    this.entries.forEach((e) => {
      if (e.photos) totalPhotos += e.photos.length;
    });

    if (entriesCountEl) entriesCountEl.textContent = this.entries.length;
    if (streakEl) streakEl.textContent = `${this.stats ? this.stats.streakDays || 0 : 0} ngày`;
    if (photosCountEl) photosCountEl.textContent = totalPhotos;

    // 3. Mood distribution breakdown
    if (this.stats && this.stats.moodBreakdown) {
      const breakdown = this.stats.moodBreakdown;
      ['serene', 'cozy', 'reflective', 'grateful', 'energetic'].forEach((m) => {
        const info = breakdown[m] || { percent: 0 };
        const barEl = document.getElementById(`profile-bar-${m}`);
        const legEl = document.getElementById(`profile-leg-${m}`);
        if (barEl) barEl.style.width = `${info.percent}%`;
        if (legEl) legEl.textContent = `${Math.round(info.percent)}%`;
      });
    }

    // 4. Passcode PIN Status Badge
    const pinBadge = document.getElementById('profile-action-pin-badge');
    if (pinBadge) {
      const isPinSet = window.PasscodeLock && window.PasscodeLock.isPasscodeSetForUser && window.PasscodeLock.isPasscodeSetForUser();
      pinBadge.textContent = isPinSet ? 'Đang bật' : 'Chưa bật';
      pinBadge.className = isPinSet ? 'badge-pill badge-active' : 'badge-pill badge-inactive';
    }

    // 5. Theme Label
    const themeLabel = document.getElementById('profile-theme-label');
    if (themeLabel) {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      themeLabel.textContent = isDark ? 'Tối (Night Sakura)' : 'Sáng';
    }

    // 6. Show PWA Install item if available
    const pwaAction = document.getElementById('profile-action-pwa');
    const headerPwaBtn = document.getElementById('pwa-install-btn');
    if (pwaAction && headerPwaBtn && headerPwaBtn.style.display !== 'none') {
      pwaAction.style.display = 'flex';
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
