/**
 * KOKORO (心) — CARD EXPORT THEMES SPECIFICATION (v1.7.0)
 * Design tokens and theme palettes for Daily Memory Card Canvas rendering.
 * Complies with AGENTS.md: Modular Layered Architecture, SSoT Tokens, Zero Magic Numbers.
 */

(function () {
  'use strict';

  const CARD_THEMES = Object.freeze({
    sakura: {
      id: 'sakura',
      name: '🌸 Sakura',
      bgGrad: ['#fff1f4', '#fdf2f7', '#fce7f3'],
      orb1: 'rgba(251, 113, 133, 0.22)',
      orb2: 'rgba(244, 114, 182, 0.25)',
      cardBg: 'rgba(255, 255, 255, 0.88)',
      cardBorder: 'rgba(244, 114, 182, 0.35)',
      cardShadow: 'rgba(244, 114, 182, 0.16)',
      textPrimary: '#0f172a',
      textSecondary: '#334155',
      textMuted: '#64748b',
      accent: '#ec4899',
      hasDotGrid: false
    },
    polaroid: {
      id: 'polaroid',
      name: '🎞️ Polaroid',
      bgGrad: ['#fdfbf7', '#f8f4ec', '#f1e8d9'],
      orb1: 'rgba(245, 158, 11, 0.08)',
      orb2: 'rgba(217, 119, 6, 0.08)',
      cardBg: '#ffffff',
      cardBorder: 'rgba(217, 119, 6, 0.18)',
      cardShadow: 'rgba(180, 83, 9, 0.10)',
      textPrimary: '#1c1917',
      textSecondary: '#44403c',
      textMuted: '#78716c',
      accent: '#ea580c',
      hasDotGrid: false
    },
    scrapbook: {
      id: 'scrapbook',
      name: '💌 Sổ Tay',
      bgGrad: ['#faf6ed', '#faf6ed', '#f4ede0'],
      orb1: 'rgba(234, 179, 8, 0.10)',
      orb2: 'rgba(244, 114, 182, 0.10)',
      cardBg: '#faf6ed',
      cardBorder: 'rgba(202, 138, 4, 0.24)',
      cardShadow: 'rgba(161, 98, 7, 0.10)',
      textPrimary: '#1e293b',
      textSecondary: '#334155',
      textMuted: '#64748b',
      accent: '#db2777',
      hasDotGrid: true
    },
    music: {
      id: 'music',
      name: '🎵 Giai Điệu',
      bgGrad: ['#181826', '#1e1b4b', '#0f172a'],
      orb1: 'rgba(168, 85, 247, 0.28)',
      orb2: 'rgba(236, 72, 153, 0.28)',
      cardBg: 'rgba(30, 27, 75, 0.76)',
      cardBorder: 'rgba(192, 132, 252, 0.40)',
      cardShadow: 'rgba(0, 0, 0, 0.35)',
      textPrimary: '#f8fafc',
      textSecondary: '#e2e8f0',
      textMuted: '#94a3b8',
      accent: '#c084fc',
      hasDotGrid: false
    },
    editorial: {
      id: 'editorial',
      name: '📰 Tạp Chí',
      bgGrad: ['#fcfbf9', '#f7f6f2', '#f0ede6'],
      orb1: 'rgba(15, 23, 42, 0.08)',
      orb2: 'rgba(100, 116, 139, 0.08)',
      cardBg: '#ffffff',
      cardBorder: 'rgba(15, 23, 42, 0.16)',
      cardShadow: 'rgba(0, 0, 0, 0.08)',
      textPrimary: '#09090b',
      textSecondary: '#27272a',
      textMuted: '#52525b',
      accent: '#0f172a',
      hasDotGrid: false
    }
  });

  const KokoroCardThemes = {
    CARD_THEMES,
    getTheme(themeId) {
      return CARD_THEMES[themeId] || CARD_THEMES.sakura;
    },
    listThemes() {
      return Object.values(CARD_THEMES);
    }
  };

  // Export to global scope
  window.KokoroCardThemes = Object.freeze(KokoroCardThemes);

  // CommonJS export for testing
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CARD_THEMES, KokoroCardThemes };
  }
})();
