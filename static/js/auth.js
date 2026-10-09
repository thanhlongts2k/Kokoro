/**
 * KOKORO (心) — CLIENT AUTHENTICATION & SESSION MANAGER
 * Manages Google Identity Services (GIS), Mock Dev Switcher,
 * Session State, Header Profile UI, and Welcome Login Overlay.
 */

const KokoroAuth = {
  currentUser: null,
  config: null,
  mockUsers: [],

  async init() {
    this.setupDropdownListeners();

    try {
      // 1. Fetch public auth settings
      const cfgRes = await window.KokoroAPI.getAuthConfig();
      if (cfgRes && cfgRes.status === 'success') {
        this.config = cfgRes;
      }
    } catch (e) {
      console.warn('[KokoroAuth] Không thể tải auth config:', e);
    }

    // 2. Fetch mock users if mock_auth is active
    if (this.config && this.config.mock_auth) {
      try {
        const mockRes = await window.KokoroAPI.getMockUsers();
        if (mockRes && mockRes.status === 'success') {
          this.mockUsers = mockRes.users || [];
          this.renderMockUsersUI();
        }
      } catch (e) {
        console.warn('[KokoroAuth] Không thể tải danh sách mock users:', e);
      }
    }

    // 3. Initialize Google Identity Services (GIS)
    this.initGoogleIdentity();

    // 4. Check existing session
    const user = await this.checkSession();
    return user;
  },

  setupDropdownListeners() {
    const pill = document.getElementById('user-profile-pill');
    const dropdown = document.getElementById('profile-dropdown-menu');
    const logoutBtn = document.getElementById('logout-btn');
    const loginHeaderBtn = document.getElementById('header-login-btn');

    if (pill && dropdown) {
      pill.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
      });

      // Click outside to close
      document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !pill.contains(e.target)) {
          dropdown.classList.remove('active');
        }
      });
    }

    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => this.logout());
    }

    if (loginHeaderBtn) {
      loginHeaderBtn.addEventListener('click', () => this.showLoginModal());
    }
  },

  initGoogleIdentity() {
    if (!this.config || !this.config.google_client_id) return;

    // Retry checking GIS library availability if still loading
    const tryInitGIS = () => {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: this.config.google_client_id,
            callback: (res) => this.handleGoogleCredential(res),
            auto_select: false
          });

          const btnContainer = document.getElementById('google-signin-btn');
          if (btnContainer) {
            window.google.accounts.id.renderButton(btnContainer, {
              theme: 'outline',
              size: 'large',
              shape: 'pill',
              text: 'continue_with',
              logo_alignment: 'left',
              width: 280
            });
          }
        } catch (err) {
          console.warn('[KokoroAuth] GIS init error:', err);
        }
      } else {
        setTimeout(tryInitGIS, 250);
      }
    };

    tryInitGIS();
  },

  async handleGoogleCredential(response) {
    if (!response || !response.credential) return;
    try {
      const res = await window.KokoroAPI.googleLogin(response.credential);
      if (res && res.status === 'success') {
        if (window.KokoroApp) {
          window.KokoroApp.showToast(`Chào mừng ${res.user.name} đến với Kokoro! 🌸`);
        }
        await this.handleLoginSuccess(res.user);
      }
    } catch (err) {
      if (window.KokoroApp) {
        window.KokoroApp.showToast(err.message || 'Xác thực Google thất bại', 'error');
      }
    }
  },

  async checkSession() {
    try {
      const res = await window.KokoroAPI.getCurrentUser();
      if (res && res.authenticated && res.user) {
        this.currentUser = res.user;
        this.updateHeaderUI(res.user);
        this.hideLoginModal();
        return res.user;
      }
    } catch (e) {
      console.warn('[KokoroAuth] Session check failed:', e);
    }

    // Unauthenticated
    this.currentUser = null;
    this.updateHeaderUI(null);
    this.showLoginModal();
    return null;
  },

  updateHeaderUI(user) {
    const profileContainer = document.getElementById('user-profile-container');
    const loginBtn = document.getElementById('header-login-btn');
    const avatarEl = document.getElementById('header-avatar');
    const nameEl = document.getElementById('header-user-name');
    const dropdownName = document.getElementById('dropdown-name');
    const dropdownEmail = document.getElementById('dropdown-email');

    if (user) {
      if (profileContainer) profileContainer.style.display = 'block';
      if (loginBtn) loginBtn.style.display = 'none';

      if (avatarEl) avatarEl.src = user.avatar_url || './icons/sakura.svg';
      if (nameEl) nameEl.textContent = user.name || 'Người dùng';
      if (dropdownName) dropdownName.textContent = user.name || '';
      if (dropdownEmail) dropdownEmail.textContent = user.email || '';
    } else {
      if (profileContainer) profileContainer.style.display = 'none';
      if (loginBtn) loginBtn.style.display = 'inline-flex';
    }
  },

  renderMockUsersUI() {
    if (!this.mockUsers || this.mockUsers.length === 0) return;

    // 1. In Profile Dropdown
    const switcher = document.getElementById('mock-account-switcher');
    const divider = document.getElementById('mock-account-divider');
    const listEl = document.getElementById('mock-users-list');

    if (switcher && listEl) {
      switcher.style.display = 'block';
      if (divider) divider.style.display = 'block';
      listEl.innerHTML = '';

      this.mockUsers.forEach((u) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'dropdown-item';
        item.style.padding = '6px 8px';
        item.style.borderRadius = '6px';
        item.innerHTML = `
          <img src="${u.avatar_url}" style="width: 22px; height: 22px; border-radius: 50%; object-fit: cover;" />
          <span style="font-size: 12px; font-weight: 600;">${u.name}</span>
        `;
        item.addEventListener('click', () => this.switchUser(u.id));
        listEl.appendChild(item);
      });
    }

    // 2. In Login Modal
    const quickSection = document.getElementById('login-quick-dev-section');
    if (quickSection) {
      quickSection.innerHTML = '';
      this.mockUsers.forEach((u) => {
        const chip = document.createElement('div');
        chip.className = 'dev-user-chip';
        chip.innerHTML = `
          <img src="${u.avatar_url}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />
          <div style="flex: 1;">
            <div style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${u.name}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${u.email}</div>
          </div>
          <i class="bi bi-chevron-right text-sakura" style="font-size: 12px;"></i>
        `;
        chip.addEventListener('click', () => this.switchUser(u.id));
        quickSection.appendChild(chip);
      });
    }
  },

  async switchUser(userId) {
    try {
      const res = await window.KokoroAPI.mockLogin(userId);
      if (res && res.status === 'success') {
        if (window.KokoroApp) {
          window.KokoroApp.showToast(`Đã chuyển sang tài khoản ${res.user.name} ✨`);
        }
        await this.handleLoginSuccess(res.user);
      }
    } catch (err) {
      if (window.KokoroApp) {
        window.KokoroApp.showToast('Lỗi chuyển đổi tài khoản: ' + err.message, 'error');
      }
    }
  },

  async handleLoginSuccess(user) {
    this.currentUser = user;
    this.updateHeaderUI(user);
    this.hideLoginModal();

    const dropdown = document.getElementById('profile-dropdown-menu');
    if (dropdown) dropdown.classList.remove('active');

    if (window.KokoroApp) {
      await window.KokoroApp.onUserChanged(user);
    }
  },

  async logout() {
    try {
      await window.KokoroAPI.logout();
      if (window.KokoroApp) {
        window.KokoroApp.showToast('Đã đăng xuất khỏi Kokoro 🌸');
      }
    } catch (e) {
      console.warn('[KokoroAuth] Logout error:', e);
    }

    this.currentUser = null;
    this.updateHeaderUI(null);
    const dropdown = document.getElementById('profile-dropdown-menu');
    if (dropdown) dropdown.classList.remove('active');

    this.showLoginModal();

    if (window.KokoroApp) {
      await window.KokoroApp.onUserChanged(null);
    }
  },

  showLoginModal() {
    const overlay = document.getElementById('login-modal-overlay');
    if (overlay) {
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  },

  hideLoginModal() {
    const overlay = document.getElementById('login-modal-overlay');
    if (overlay) {
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
};

window.KokoroAuth = KokoroAuth;
