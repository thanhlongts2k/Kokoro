/**
 * KOKORO (心) — PROFILE & STATS VIEW COMPONENT
 * Handles profile user details, streak calculations, mood distribution breakdown,
 * and count synchronization across desktop and mobile navigation badges.
 * Complies with AGENTS.md: Modular Layered Architecture & Single Responsibility Principle.
 */

const ProfileStats = {
  MOOD_SEGMENTS: [
    { key: 'serene', cls: 'segment-serene', label: 'Thanh bình' },
    { key: 'cozy', cls: 'segment-cozy', label: 'Ấm áp' },
    { key: 'reflective', cls: 'segment-reflective', label: 'Chiêm nghiệm' },
    { key: 'grateful', cls: 'segment-grateful', label: 'Biết ơn' },
    { key: 'energetic', cls: 'segment-energetic', label: 'Năng lượng' },
  ],

  /**
   * Calculate consecutive journaling days streak
   */
  calculateStreak(entries) {
    if (!entries || !entries.length) return 0;
    const sortedDates = Array.from(new Set(entries.map((e) => e.entryDate).filter(Boolean))).sort().reverse();
    if (!sortedDates.length) return 0;

    const todayStr = new Date().toISOString().split('T')[0];
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    let streak = 0;
    let expectedDate = sortedDates[0] === todayStr ? todayStr : (sortedDates[0] === yesterdayStr ? yesterdayStr : null);
    if (!expectedDate) return 0;

    const checkDate = new Date(expectedDate);
    for (const d of sortedDates) {
      const curStr = checkDate.toISOString().split('T')[0];
      if (d === curStr) {
        streak++;
        checkDate.setDate(checkDate.getDate() - 1);
      } else {
        break;
      }
    }
    return streak;
  },

  /**
   * Synchronize mood filter counts across Desktop Sidebar and Mobile Chips
   */
  updateMoodCountBadges(options) {
    const { stats, entries, categories } = options;
    const badges = document.querySelectorAll('[data-count-mood], [data-count-category]');
    badges.forEach((badge) => {
      if (badge.dataset.countMood) {
        const moodKey = badge.dataset.countMood;
        let count = 0;
        if (moodKey === 'all') {
          count = (stats && stats.totalEntries !== undefined) ? stats.totalEntries : (entries ? entries.length : 0);
        } else {
          count = (stats && stats.moodCounts && stats.moodCounts[moodKey]) ? stats.moodCounts[moodKey] : 0;
        }
        badge.textContent = count;
      } else if (badge.dataset.countCategory) {
        const catId = Number(badge.dataset.countCategory);
        const cat = (categories || []).find((c) => c.id === catId);
        badge.textContent = cat ? (cat.usage_count || 0) : 0;
      }
    });
  },

  /**
   * Render horizontal multi-color mood breakdown bar
   */
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

    let html = '';
    this.MOOD_SEGMENTS.forEach((m) => {
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

  /**
   * Render sidebar stats widget
   */
  renderStats(options) {
    const { entries, stats } = options;
    const countEl = document.getElementById('stat-total-entries');
    if (countEl) countEl.textContent = entries ? entries.length : 0;

    const total = entries ? entries.length : 0;
    const moodCounts = { serene: 0, cozy: 0, reflective: 0, grateful: 0, energetic: 0 };
    (entries || []).forEach((e) => {
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
   * Render Profile View & Management Metrics
   */
  renderProfileView(options) {
    const { user, entries, stats } = options;

    // 1. User Header & Personalization (v1.8.5)
    const avatarEl = document.getElementById('profile-view-avatar');
    const nameEl = document.getElementById('profile-view-name');
    const emailEl = document.getElementById('profile-view-email');
    const bioEl = document.getElementById('profile-view-bio');

    if (avatarEl) {
      avatarEl.onerror = () => { avatarEl.onerror = null; avatarEl.src = './icons/sakura.svg'; };
      const rawAvatar = user ? (user.effectiveAvatarUrl || ((user.use_custom_profile || user.useCustomProfile) ? (user.custom_avatar_url || user.customAvatarUrl) : (user.avatar_url || user.avatarUrl)) || user.avatar_url) : null;
      avatarEl.src = rawAvatar ? (window.KokoroAPI && typeof window.KokoroAPI.resolveMediaUrl === 'function' ? window.KokoroAPI.resolveMediaUrl(rawAvatar) : rawAvatar) : './icons/sakura.svg';
    }
    if (nameEl) nameEl.textContent = user ? user.name : 'Khách vãng lai';
    if (emailEl) emailEl.textContent = user ? user.email : 'chua_dang_nhap@kokoro.me';
    if (bioEl) {
      const bioText = user ? (user.bio || '') : '';
      if (bioText.trim()) {
        bioEl.textContent = `“${bioText}”`;
        bioEl.style.display = 'inline-block';
      } else {
        bioEl.textContent = '';
        bioEl.style.display = 'none';
      }
    }

    // Bind edit profile button
    const editBtn = document.getElementById('profile-edit-btn');
    if (editBtn && !editBtn._bound) {
      editBtn._bound = true;
      editBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.openEditProfileModal(window.KokoroApp || options.appContext);
      });
    }

    // 2. Metrics & Stats
    const entriesCountEl = document.getElementById('profile-stat-entries');
    const streakEl = document.getElementById('profile-stat-streak');
    const photosCountEl = document.getElementById('profile-stat-photos');

    let totalPhotos = 0;
    (entries || []).forEach((e) => {
      if (e.photos) totalPhotos += e.photos.length;
    });

    if (entriesCountEl) entriesCountEl.textContent = entries ? entries.length : 0;
    if (streakEl) streakEl.textContent = `${stats ? stats.streakDays || 0 : 0} ngày`;
    if (photosCountEl) photosCountEl.textContent = totalPhotos;

    // 3. Mood distribution breakdown in Profile
    if (stats && stats.moodBreakdown) {
      const breakdown = stats.moodBreakdown;
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
      const isPinSet = Boolean(window.PasscodeLock && (
        (typeof window.PasscodeLock.isEnabled === 'function' && window.PasscodeLock.isEnabled()) ||
        (typeof window.PasscodeLock.isPasscodeSetForUser === 'function' && window.PasscodeLock.isPasscodeSetForUser())
      ));
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
   * Action handler for cleaning up orphaned media files from uploads directory
   */
  async cleanupOrphanedMedia(appContext) {
    try {
      const confirmed = window.KokoroDialog
        ? await window.KokoroDialog.confirm({
            title: 'Dọn dẹp ảnh rác 🧹',
            message: 'Hệ thống sẽ quét và xóa vĩnh viễn các tệp ảnh mồ côi không còn thuộc bài viết nào trong thư mục /uploads/ để giải phóng dung lượng. Bạn có chắc chắn muốn dọn dẹp?',
            confirmText: 'Dọn dẹp ngay',
            cancelText: 'Hủy bỏ',
            isDanger: true,
            icon: 'bi-trash3'
          })
        : window.confirm('Hệ thống sẽ quét và xóa vĩnh viễn các tệp ảnh mồ côi không còn thuộc bài viết nào trong thư mục /uploads/ để giải phóng dung lượng. Bạn có chắc chắn muốn dọn dẹp?');

      if (!confirmed) return;

      const toast = (msg, type = 'success') => {
        if (appContext && typeof appContext.showToast === 'function') appContext.showToast(msg, type);
        else if (window.KokoroToast) window.KokoroToast.show(msg, type);
      };

      toast('Đang quét và dọn dẹp ảnh mồ côi... 🍃', 'info');
      const res = await window.KokoroAPI.cleanupOrphanedMedia(2.0);
      const data = res?.data || {};
      const deletedCount = data.deleted_count !== undefined ? data.deleted_count : (res?.deleted_count || 0);
      const freedMb = data.freed_mb !== undefined ? data.freed_mb : (res?.freed_mb || 0);

      toast(`✨ Đã dọn dẹp sạch sẽ: Xóa thành công ${deletedCount} tệp ảnh rác, giải phóng ${freedMb} MB dung lượng đĩa`);
      this.showCleanupResultModal(data, appContext);
      if (appContext && typeof appContext.loadStats === 'function') {
        await appContext.loadStats();
      }
    } catch (err) {
      console.error('[ProfileStats] Lỗi khi dọn dẹp ảnh mồ côi:', err);
      const errMsg = 'Lỗi khi dọn dẹp ảnh rác: ' + (err.message || err);
      if (appContext && typeof appContext.showToast === 'function') appContext.showToast(errMsg, 'error');
      else if (window.KokoroToast) window.KokoroToast.show(errMsg, 'error');
    }
  },

  showCleanupResultModal(data, appContext) {
    const modal = document.getElementById('cleanup-result-modal');
    if (!modal) return;

    const scannedEl = document.getElementById('cleanup-res-scanned');
    const deletedEl = document.getElementById('cleanup-res-deleted');
    const freedEl = document.getElementById('cleanup-res-freed');
    const durationEl = document.getElementById('cleanup-res-duration');
    const closeBtn = document.getElementById('cleanup-result-close-btn');

    if (scannedEl) scannedEl.textContent = data.scanned_count ?? 0;
    if (deletedEl) deletedEl.textContent = data.deleted_count ?? 0;
    if (freedEl) freedEl.textContent = (data.freed_mb ?? 0) + ' MB';
    if (durationEl) durationEl.textContent = (data.duration_ms ?? 0) + ' ms';

    modal.style.display = 'flex';
    modal.classList.add('active');

    const closeModal = () => {
      modal.style.display = 'none';
      modal.classList.remove('active');
    };

    if (closeBtn) closeBtn.onclick = closeModal;
    modal.onclick = (e) => {
      if (e.target === modal) closeModal();
    };
  },

  /**
   * Open the Personalization Hub Modal (v1.8.5)
   */
  openEditProfileModal(appContext) {
    const modal = document.getElementById('edit-profile-modal');
    if (!modal) return;

    const user = appContext?.currentUser || window.KokoroAuth?.currentUser;
    if (!user) {
      if (window.KokoroToast) window.KokoroToast.show('Vui lòng đăng nhập để chỉnh sửa hồ sơ 🌸', 'warning');
      return;
    }

    this.initEditProfileModal(appContext);

    const nameInput = document.getElementById('edit-profile-name-input');
    const bioInput = document.getElementById('edit-profile-bio-input');
    const bioCounter = document.getElementById('edit-profile-bio-counter');
    const avatarPreview = document.getElementById('edit-profile-avatar-preview');
    const googleSyncToggle = document.getElementById('edit-profile-google-sync-toggle');
    const errorEl = document.getElementById('edit-profile-error');
    const fileInput = document.getElementById('edit-profile-avatar-input');

    if (fileInput) fileInput.value = '';
    if (errorEl) {
      errorEl.style.display = 'none';
      errorEl.textContent = '';
    }

    const useCustom = Boolean(user.use_custom_profile || user.useCustomProfile);
    const isGoogleSync = !useCustom;
    if (googleSyncToggle) {
      googleSyncToggle.checked = isGoogleSync;
    }

    if (nameInput) {
      nameInput.value = user.name || '';
      nameInput.disabled = false;
    }

    if (bioInput) {
      bioInput.value = user.bio || '';
      if (bioCounter) bioCounter.textContent = `${bioInput.value.length}/250`;
    }

    const currentAvatar = user.effectiveAvatarUrl || (useCustom ? (user.custom_avatar_url || user.customAvatarUrl) : (user.avatar_url || user.avatarUrl)) || user.avatar_url || './icons/sakura.svg';
    if (avatarPreview) {
      avatarPreview.onerror = () => { avatarPreview.onerror = null; avatarPreview.src = './icons/sakura.svg'; };
      avatarPreview.src = (window.KokoroAPI && typeof window.KokoroAPI.resolveMediaUrl === 'function') ? window.KokoroAPI.resolveMediaUrl(currentAvatar) : currentAvatar;
    }

    modal.style.display = 'flex';
    modal.classList.add('active');
    if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(true);
  },

  /**
   * Close the Personalization Hub Modal
   */
  closeEditProfileModal() {
    const modal = document.getElementById('edit-profile-modal');
    if (!modal) return;
    modal.style.display = 'none';
    modal.classList.remove('active');
    if (typeof window.lockBodyScroll === 'function') window.lockBodyScroll(false);
  },

  /**
   * Initialize Edit Profile Modal event listeners once
   */
  initEditProfileModal(appContext) {
    if (this._editModalInitialized) return;
    this._editModalInitialized = true;

    const modal = document.getElementById('edit-profile-modal');
    if (!modal) return;

    const closeBtn = document.getElementById('edit-profile-close-btn');
    const cancelBtn = document.getElementById('edit-profile-cancel-btn');
    const avatarTrigger = document.getElementById('edit-profile-avatar-trigger');
    const fileInput = document.getElementById('edit-profile-avatar-input');
    const avatarPreview = document.getElementById('edit-profile-avatar-preview');
    const googleSyncToggle = document.getElementById('edit-profile-google-sync-toggle');
    const bioInput = document.getElementById('edit-profile-bio-input');
    const bioCounter = document.getElementById('edit-profile-bio-counter');
    const form = document.getElementById('edit-profile-form');
    const nameInput = document.getElementById('edit-profile-name-input');
    const errorEl = document.getElementById('edit-profile-error');
    const submitBtn = document.getElementById('edit-profile-submit-btn');
    const spinner = document.getElementById('edit-profile-submit-spinner');
    const submitText = document.getElementById('edit-profile-submit-text');

    const closeModal = () => this.closeEditProfileModal();

    if (closeBtn) closeBtn.onclick = closeModal;
    if (cancelBtn) cancelBtn.onclick = closeModal;
    modal.onclick = (e) => {
      if (e.target === modal) closeModal();
    };

    // Avatar file trigger
    if (avatarTrigger && fileInput) {
      avatarTrigger.onclick = () => fileInput.click();
    }

    // Avatar file selected preview
    if (fileInput) {
      fileInput.onchange = (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        // Validate max 5MB
        if (file.size > 5 * 1024 * 1024) {
          if (errorEl) {
            errorEl.textContent = 'Kích thước tệp ảnh vượt quá 5MB. Vui lòng chọn ảnh nhỏ hơn 🌸';
            errorEl.style.display = 'block';
          }
          fileInput.value = '';
          return;
        }

        // Validate image mime
        if (!file.type.startsWith('image/')) {
          if (errorEl) {
            errorEl.textContent = 'Vui lòng chọn tệp hình ảnh hợp lệ (JPEG, PNG, WEBP) 🌸';
            errorEl.style.display = 'block';
          }
          fileInput.value = '';
          return;
        }

        if (errorEl) {
          errorEl.style.display = 'none';
          errorEl.textContent = '';
        }

        // Instant circular preview
        const reader = new FileReader();
        reader.onload = (ev) => {
          if (avatarPreview) avatarPreview.src = ev.target.result;
          // Uncheck Google sync since user picked a custom avatar
          if (googleSyncToggle && googleSyncToggle.checked) {
            googleSyncToggle.checked = false;
          }
        };
        reader.readAsDataURL(file);
      };
    }

    // Google sync toggle switcher
    if (googleSyncToggle) {
      googleSyncToggle.onchange = () => {
        const isGoogleSync = googleSyncToggle.checked;
        const user = appContext?.currentUser || window.KokoroAuth?.currentUser;
        if (!user) return;

        if (isGoogleSync) {
          // Switch to Google GIS info
          if (fileInput) fileInput.value = '';
          const gAvatar = user.avatar_url || user.avatarUrl || './icons/sakura.svg';
          if (avatarPreview) avatarPreview.src = gAvatar;
        } else {
          // Switch to Custom profile info
          const cAvatar = user.custom_avatar_url || user.customAvatarUrl || user.avatar_url || user.avatarUrl || './icons/sakura.svg';
          if (avatarPreview) {
            avatarPreview.src = (window.KokoroAPI && typeof window.KokoroAPI.resolveMediaUrl === 'function') ? window.KokoroAPI.resolveMediaUrl(cAvatar) : cAvatar;
          }
        }
      };
    }

    // Bio character counter
    if (bioInput && bioCounter) {
      bioInput.oninput = () => {
        const len = bioInput.value.length;
        bioCounter.textContent = `${len}/250`;
        if (len > 250) {
          bioCounter.style.color = '#ef4444';
        } else {
          bioCounter.style.color = 'var(--text-muted)';
        }
      };
    }

    // Form submission
    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const name = nameInput ? nameInput.value.trim() : '';
        if (!name) {
          if (errorEl) {
            errorEl.textContent = 'Tên hiển thị không được để trống 🌸';
            errorEl.style.display = 'block';
          }
          return;
        }

        const bio = bioInput ? bioInput.value.trim() : '';
        if (bio.length > 250) {
          if (errorEl) {
            errorEl.textContent = 'Châm ngôn sống không được vượt quá 250 ký tự 🌸';
            errorEl.style.display = 'block';
          }
          return;
        }

        const isGoogleSync = googleSyncToggle ? googleSyncToggle.checked : false;
        const useCustomProfile = !isGoogleSync;

        const formData = new FormData();
        formData.append('name', name);
        formData.append('bio', bio);
        formData.append('use_custom_profile', useCustomProfile ? 'true' : 'false');

        const file = fileInput && fileInput.files && fileInput.files[0];
        if (file && useCustomProfile) {
          formData.append('avatar_file', file);
        }

        // UI Loading state
        if (submitBtn) submitBtn.disabled = true;
        if (spinner) spinner.style.display = 'inline-block';
        if (submitText) submitText.textContent = 'Đang lưu...';
        if (errorEl) { errorEl.style.display = 'none'; errorEl.textContent = ''; }

        try {
          const res = await window.KokoroAPI.updateProfile(formData);
          const updatedUser = res?.user;
          if (updatedUser) {
            if (appContext) {
              appContext.currentUser = updatedUser;
            }
            if (window.KokoroAuth) {
              window.KokoroAuth.currentUser = updatedUser;
              window.KokoroAuth.saveLastAuthUser(updatedUser);
              window.KokoroAuth.updateHeaderUI(updatedUser);
            }
            this.renderProfileView({
              user: updatedUser,
              entries: appContext?.entries,
              stats: appContext?.stats,
              appContext
            });
            if (window.KokoroToast) {
              window.KokoroToast.show('Cập nhật hồ sơ cá nhân thành công 🌸', 'success');
            }
            closeModal();
          } else {
            throw new Error(res?.message || 'Không nhận được dữ liệu phản hồi');
          }
        } catch (err) {
          console.error('[ProfileStats] Error updating profile:', err);
          if (errorEl) {
            errorEl.textContent = err.message || 'Lỗi khi cập nhật hồ sơ 🌸';
            errorEl.style.display = 'block';
          }
        } finally {
          if (submitBtn) submitBtn.disabled = false;
          if (spinner) spinner.style.display = 'none';
          if (submitText) submitText.textContent = 'Lưu thay đổi 🌸';
        }
      };
    }
  }
};

window.ProfileStats = ProfileStats;

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ProfileStats };
}
