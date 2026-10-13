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
  }
};

window.ProfileStats = ProfileStats;

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ProfileStats };
}
