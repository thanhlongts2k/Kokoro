/**
 * KOKORO (心) — PASSCODE LOCK CONTROLLER
 * Client-Side Privacy Screen & Inactivity Auto-Lock
 * Cryptographic Security: WebCrypto SHA-256 + 128-bit Salt
 */

const PasscodeLock = {
  currentUserId: 1,
  inputPin: '',
  setupStep: null, // null | 'enter_new' | 'confirm_new' | 'verify_old'
  tempNewPin: '',
  failedAttempts: 0,
  lockoutTimer: null,
  inactivityTimer: null,
  lastActivityTime: Date.now(),
  isLocked: false,

  async init(userId = 1) {
    this.currentUserId = userId;
    this.bindEvents();
    this.startInactivityWatcher();

    // Check if passcode is enabled for this user
    if (this.isEnabled()) {
      const isUnlockedThisSession = sessionStorage.getItem(`kokoro_unlocked_${this.currentUserId}`) === 'true';
      if (!isUnlockedThisSession) {
        this.showLockScreen();
      }
    }
  },

  onUserChanged(userId) {
    this.currentUserId = userId;
    this.inputPin = '';
    this.setupStep = null;
    if (this.isEnabled()) {
      const isUnlockedThisSession = sessionStorage.getItem(`kokoro_unlocked_${this.currentUserId}`) === 'true';
      if (!isUnlockedThisSession) {
        this.showLockScreen();
      } else {
        this.hideLockScreen();
      }
    } else {
      this.hideLockScreen();
    }
    this.updateProfileMenuUi();
  },

  isEnabled() {
    return localStorage.getItem(`kokoro_pin_enabled_${this.currentUserId}`) === 'true';
  },

  getInactivityTimeoutMinutes() {
    const val = localStorage.getItem(`kokoro_pin_timeout_${this.currentUserId}`);
    return val !== null ? parseInt(val, 10) : 5; // default 5 minutes
  },

  // --------------------------------------------------------------------------
  // CRYPTOGRAPHY HELPERS (WebCrypto SHA-256 + Salt)
  // --------------------------------------------------------------------------
  async hashPin(pin, saltHex) {
    const enc = new TextEncoder();
    const data = enc.encode(pin + saltHex);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  },

  generateSalt() {
    const saltBytes = new Uint8Array(16);
    window.crypto.getRandomValues(saltBytes);
    return Array.from(saltBytes).map((b) => b.toString(16).padStart(2, '0')).join('');
  },

  async verifyPin(pin) {
    const storedHash = localStorage.getItem(`kokoro_pin_hash_${this.currentUserId}`);
    const storedSalt = localStorage.getItem(`kokoro_pin_salt_${this.currentUserId}`);
    if (!storedHash || !storedSalt) return false;
    const computedHash = await this.hashPin(pin, storedSalt);
    return computedHash === storedHash;
  },

  async saveNewPin(pin) {
    const salt = this.generateSalt();
    const hash = await this.hashPin(pin, salt);
    localStorage.setItem(`kokoro_pin_hash_${this.currentUserId}`, hash);
    localStorage.setItem(`kokoro_pin_salt_${this.currentUserId}`, salt);
    localStorage.setItem(`kokoro_pin_enabled_${this.currentUserId}`, 'true');
    sessionStorage.setItem(`kokoro_unlocked_${this.currentUserId}`, 'true');
  },

  disablePin() {
    localStorage.removeItem(`kokoro_pin_hash_${this.currentUserId}`);
    localStorage.removeItem(`kokoro_pin_salt_${this.currentUserId}`);
    localStorage.setItem(`kokoro_pin_enabled_${this.currentUserId}`, 'false');
    sessionStorage.removeItem(`kokoro_unlocked_${this.currentUserId}`);
  },

  // --------------------------------------------------------------------------
  // LOCK SCREEN UI CONTROLS
  // --------------------------------------------------------------------------
  showLockScreen() {
    this.isLocked = true;
    this.inputPin = '';
    const overlay = document.getElementById('passcode-lock-overlay');
    if (!overlay) return;

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    this.updateDots();

    const titleEl = document.getElementById('passcode-title');
    const subtitleEl = document.getElementById('passcode-subtitle');
    if (titleEl) titleEl.textContent = 'Mở Khóa Nhật Ký 🌸';
    if (subtitleEl) subtitleEl.textContent = 'Vui lòng nhập mã PIN 4 số của bạn';
  },

  hideLockScreen() {
    this.isLocked = false;
    this.inputPin = '';
    const overlay = document.getElementById('passcode-lock-overlay');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
  },

  lockNow() {
    if (!this.isEnabled()) {
      if (window.KokoroApp) {
        window.KokoroApp.showToast('Bạn chưa thiết lập mã PIN bảo mật. Vui lòng cài đặt trước nhé! 🌸', 'info');
      }
      this.openSetupModal();
      return;
    }
    sessionStorage.removeItem(`kokoro_unlocked_${this.currentUserId}`);
    this.showLockScreen();
    if (window.KokoroApp) {
      window.KokoroApp.showToast('Đã khóa màn hình bảo vệ nhật ký! 🍃', 'info');
    }
  },

  updateDots() {
    const dots = document.querySelectorAll('#passcode-dots .pin-dot');
    dots.forEach((dot, idx) => {
      if (idx < this.inputPin.length) {
        dot.classList.add('filled');
      } else {
        dot.classList.remove('filled');
      }
    });
  },

  shakeKeypad(errorMsg = 'Mã PIN không chính xác') {
    const container = document.getElementById('passcode-card');
    const subtitleEl = document.getElementById('passcode-subtitle');
    if (subtitleEl) {
      subtitleEl.textContent = errorMsg;
      subtitleEl.style.color = '#f43f5e';
    }

    if (container) {
      container.classList.add('shake');
      setTimeout(() => container.classList.remove('shake'), 400);
    }

    this.inputPin = '';
    this.updateDots();

    setTimeout(() => {
      if (subtitleEl && !this.lockoutTimer) {
        subtitleEl.textContent = 'Vui lòng nhập mã PIN 4 số của bạn';
        subtitleEl.style.color = 'var(--text-secondary)';
      }
    }, 1800);
  },

  handleDigit(digit) {
    if (this.lockoutTimer) return;
    if (this.inputPin.length >= 4) return;

    this.inputPin += String(digit);
    this.updateDots();

    if (this.inputPin.length === 4) {
      setTimeout(() => this.processCompletePin(), 120);
    }
  },

  handleBackspace() {
    if (this.lockoutTimer) return;
    if (this.inputPin.length > 0) {
      this.inputPin = this.inputPin.slice(0, -1);
      this.updateDots();
    }
  },

  async processCompletePin() {
    const entered = this.inputPin;

    // Normal unlock mode
    if (this.isLocked) {
      const isValid = await this.verifyPin(entered);
      if (isValid) {
        this.failedAttempts = 0;
        sessionStorage.setItem(`kokoro_unlocked_${this.currentUserId}`, 'true');
        this.hideLockScreen();
        if (window.KokoroApp) {
          window.KokoroApp.showToast('Đã mở khóa nhật ký thành công! 🌸✨');
        }
      } else {
        this.failedAttempts++;
        if (this.failedAttempts >= 5) {
          this.startLockout(30);
        } else {
          this.shakeKeypad(`Mã PIN không đúng (Lần ${this.failedAttempts}/5)`);
        }
      }
      return;
    }

    // Modal Setup Mode
    if (this.setupStep) {
      this.handleSetupPinInput(entered);
    }
  },

  startLockout(seconds) {
    let remain = seconds;
    const subtitleEl = document.getElementById('passcode-subtitle');
    if (subtitleEl) {
      subtitleEl.textContent = `Sai quá nhiều lần. Vui lòng chờ ${remain}s...`;
      subtitleEl.style.color = '#f43f5e';
    }

    this.inputPin = '';
    this.updateDots();

    this.lockoutTimer = setInterval(() => {
      remain--;
      if (remain <= 0) {
        clearInterval(this.lockoutTimer);
        this.lockoutTimer = null;
        this.failedAttempts = 0;
        if (subtitleEl) {
          subtitleEl.textContent = 'Vui lòng nhập mã PIN 4 số của bạn';
          subtitleEl.style.color = 'var(--text-secondary)';
        }
      } else {
        if (subtitleEl) {
          subtitleEl.textContent = `Sai quá nhiều lần. Vui lòng chờ ${remain}s...`;
        }
      }
    }, 1000);
  },

  // --------------------------------------------------------------------------
  // SETUP MODAL WORKFLOW
  // --------------------------------------------------------------------------
  openSetupModal() {
    const modal = document.getElementById('passcode-settings-modal');
    if (!modal) return;

    this.updateSettingsModalState();
    modal.classList.add('active');
  },

  closeSetupModal() {
    const modal = document.getElementById('passcode-settings-modal');
    if (modal) modal.classList.remove('active');
  },

  updateSettingsModalState() {
    const isCurrentlyEnabled = this.isEnabled();
    const toggle = document.getElementById('passcode-toggle-switch');
    const changePinBtn = document.getElementById('passcode-change-btn');
    const timeoutSelect = document.getElementById('passcode-timeout-select');

    if (toggle) toggle.checked = isCurrentlyEnabled;
    if (changePinBtn) changePinBtn.style.display = isCurrentlyEnabled ? 'inline-flex' : 'none';
    if (timeoutSelect) {
      timeoutSelect.value = String(this.getInactivityTimeoutMinutes());
      timeoutSelect.disabled = !isCurrentlyEnabled;
    }
  },

  startSetNewPinFlow() {
    this.closeSetupModal();
    const isCurrentlyEnabled = this.isEnabled();
    this.setupStep = isCurrentlyEnabled ? 'verify_old' : 'enter_new';
    this.inputPin = '';

    const overlay = document.getElementById('passcode-lock-overlay');
    if (overlay) overlay.classList.add('active');

    const titleEl = document.getElementById('passcode-title');
    const subtitleEl = document.getElementById('passcode-subtitle');
    if (this.setupStep === 'verify_old') {
      if (titleEl) titleEl.textContent = 'Xác Nhận PIN Hiện Tại 🌸';
      if (subtitleEl) subtitleEl.textContent = 'Vui lòng nhập mã PIN cũ trước khi đổi';
    } else {
      if (titleEl) titleEl.textContent = 'Thiết Lập Mã PIN Mới 🌸';
      if (subtitleEl) subtitleEl.textContent = 'Nhập 4 số bảo vệ nhật ký của bạn';
    }
    this.updateDots();
  },

  async handleSetupPinInput(entered) {
    const titleEl = document.getElementById('passcode-title');
    const subtitleEl = document.getElementById('passcode-subtitle');

    if (this.setupStep === 'verify_old') {
      const isValid = await this.verifyPin(entered);
      if (isValid) {
        this.setupStep = 'enter_new';
        this.inputPin = '';
        this.updateDots();
        if (titleEl) titleEl.textContent = 'Thiết Lập Mã PIN Mới 🌸';
        if (subtitleEl) subtitleEl.textContent = 'Nhập 4 số mới';
      } else {
        this.shakeKeypad('Mã PIN cũ không chính xác');
      }
      return;
    }

    if (this.setupStep === 'enter_new') {
      this.tempNewPin = entered;
      this.setupStep = 'confirm_new';
      this.inputPin = '';
      this.updateDots();
      if (titleEl) titleEl.textContent = 'Xác Nhận Lại Mã PIN 🌸';
      if (subtitleEl) subtitleEl.textContent = 'Nhập lại 4 số vừa tạo để xác nhận';
      return;
    }

    if (this.setupStep === 'confirm_new') {
      if (entered === this.tempNewPin) {
        await this.saveNewPin(entered);
        this.setupStep = null;
        this.tempNewPin = '';
        this.hideLockScreen();
        this.updateProfileMenuUi();
        if (window.KokoroApp) {
          window.KokoroApp.showToast('Đã thiết lập mã PIN bảo mật thành công! 🌸✨');
        }
      } else {
        this.shakeKeypad('Mã PIN không khớp! Thử lại');
        this.setupStep = 'enter_new';
        if (titleEl) titleEl.textContent = 'Thiết Lập Mã PIN Mới 🌸';
        if (subtitleEl) subtitleEl.textContent = 'Nhập 4 số mới';
      }
    }
  },

  updateProfileMenuUi() {
    const badge = document.getElementById('profile-lock-badge');
    if (badge) {
      badge.textContent = this.isEnabled() ? 'Đang bật' : 'Chưa bật';
      badge.className = this.isEnabled() ? 'badge-pill badge-active' : 'badge-pill badge-inactive';
    }
  },

  // --------------------------------------------------------------------------
  // INACTIVITY AUTO-LOCK
  // --------------------------------------------------------------------------
  resetInactivity() {
    this.lastActivityTime = Date.now();
  },

  startInactivityWatcher() {
    const updateActivity = () => this.resetInactivity();
    window.addEventListener('mousemove', updateActivity, { passive: true });
    window.addEventListener('keydown', updateActivity, { passive: true });
    window.addEventListener('touchstart', updateActivity, { passive: true });
    window.addEventListener('scroll', updateActivity, { passive: true });

    // When returning to the tab from background
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.isEnabled()) {
        const timeoutMins = this.getInactivityTimeoutMinutes();
        if (timeoutMins > 0) {
          const elapsedMins = (Date.now() - this.lastActivityTime) / 60000;
          if (elapsedMins >= timeoutMins) {
            sessionStorage.removeItem(`kokoro_unlocked_${this.currentUserId}`);
            this.showLockScreen();
          }
        }
      }
    });

    // Background interval check every 30 seconds
    setInterval(() => {
      if (!this.isLocked && this.isEnabled()) {
        const timeoutMins = this.getInactivityTimeoutMinutes();
        if (timeoutMins > 0) {
          const elapsedMins = (Date.now() - this.lastActivityTime) / 60000;
          if (elapsedMins >= timeoutMins) {
            sessionStorage.removeItem(`kokoro_unlocked_${this.currentUserId}`);
            this.showLockScreen();
          }
        }
      }
    }, 30000);
  },

  bindEvents() {
    // Virtual Numpad button clicks
    document.querySelectorAll('[data-passcode-digit]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const digit = e.currentTarget.dataset.passcodeDigit;
        this.handleDigit(digit);
      });
    });

    const backspaceBtn = document.getElementById('passcode-backspace-btn');
    if (backspaceBtn) {
      backspaceBtn.addEventListener('click', () => this.handleBackspace());
    }

    const cancelBtn = document.getElementById('passcode-cancel-setup-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        this.setupStep = null;
        this.tempNewPin = '';
        if (!this.isLocked) {
          this.hideLockScreen();
        } else {
          this.showLockScreen();
        }
      });
    }

    // Physical Keyboard support (0-9, Backspace, Esc)
    document.addEventListener('keydown', (e) => {
      const overlay = document.getElementById('passcode-lock-overlay');
      if (!overlay || !overlay.classList.contains('active')) return;

      if (e.key >= '0' && e.key <= '9') {
        this.handleDigit(e.key);
      } else if (e.key === 'Backspace') {
        this.handleBackspace();
      } else if (e.key === 'Escape' && !this.isLocked && this.setupStep) {
        this.setupStep = null;
        this.hideLockScreen();
      }
    });
  }
};

window.PasscodeLock = PasscodeLock;
