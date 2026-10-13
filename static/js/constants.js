/**
 * KOKORO (心) — CLIENT CONSTANTS & SYSTEM ENUMS
 * Single Source of Truth for magic numbers, timeouts, UI enums, and storage keys.
 * Complies with AGENTS.md: Rule-14 (Zero Magic Numbers & Centralized Constants).
 */

const KokoroConstants = Object.freeze({
  // Pagination & Display Limits
  PAGINATION: Object.freeze({
    DEFAULT_PAGE_SIZE: 15,
    INITIAL_VISIBLE_LIMIT: 15,
    SUMMARY_SNIPPET_LENGTH: 120,
    MAX_TAGS_PREVIEW: 3,
    MAX_PHOTOS_PREVIEW: 3,
  }),

  // Delays & Timeouts (milliseconds)
  TIMEOUTS: Object.freeze({
    SEARCH_DEBOUNCE_MS: 300,
    DRAFT_AUTOSAVE_MS: 1000,
    TOAST_DURATION_MS: 3000,
    ANIMATION_DELAY_MS: 200,
    CANVAS_FONT_LOAD_TIMEOUT_MS: 2000,
  }),

  // Views & Routing
  VIEWS: Object.freeze({
    TIMELINE: 'timeline',
    CALENDAR: 'calendar',
    MEMORIES: 'memories',
    PROFILE: 'profile',
  }),

  // Standard Moods Mapping
  MOODS: Object.freeze({
    SERENE: { id: 'serene', label: 'Bình yên', emoji: '🌸', color: '#ec4899' },
    COZY: { id: 'cozy', label: 'Ấm áp', emoji: '☕', color: '#f59e0b' },
    REFLECTIVE: { id: 'reflective', label: 'Chiêm nghiệm', emoji: '🌙', color: '#8b5cf6' },
    GRATEFUL: { id: 'grateful', label: 'Biết ơn', emoji: '🍵', color: '#10b981' },
    ENERGETIC: { id: 'energetic', label: 'Năng lượng', emoji: '⚡', color: '#3b82f6' },
  }),

  // Weather Types
  WEATHER: Object.freeze({
    SUNNY: { id: 'sunny', label: 'Nắng ấm', icon: '☀️' },
    CLOUDY: { id: 'cloudy', label: 'Nhiều mây', icon: '☁️' },
    RAINY: { id: 'rainy', label: 'Mưa rào', icon: '🌧️' },
    SNOWY: { id: 'snowy', label: 'Tuyết rơi', icon: '❄️' },
    WINDY: { id: 'windy', label: 'Gió nhẹ', icon: '🍃' },
  }),

  // Local Storage Keys
  STORAGE_KEYS: Object.freeze({
    DRAFT_PREFIX: 'kokoro_draft_',
    THEME_KEY: 'kokoro_active_theme',
    PASSCODE_KEY: 'kokoro_passcode_hash',
    APP_LOCKED: 'kokoro_app_locked',
    ZEN_ACTIVE_PREFIX: 'kokoro_zen_active_',
  }),

  // Keyboard Keys
  KEYS: Object.freeze({
    ESCAPE: 'Escape',
    ENTER: 'Enter',
    ARROW_LEFT: 'ArrowLeft',
    ARROW_RIGHT: 'ArrowRight',
  }),

  // Card Export Themes
  EXPORT_THEMES: Object.freeze({
    SAKURA: 'sakura',
    POLAROID: 'polaroid',
    SCRAPBOOK: 'scrapbook',
    MUSIC: 'music',
    EDITORIAL: 'editorial',
  }),
});

// Export to window
window.KokoroConstants = KokoroConstants;

// CommonJS support for test runner
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { KokoroConstants };
}
