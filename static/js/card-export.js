/**
 * KOKORO (心) — DAILY CARD EXPORT COORDINATOR (v1.7.0)
 * UI Controller & Modal Coordinator for Daily Card Export.
 * Delegates 2D Canvas rendering to `KokoroCardCanvasEngine` and themes to `KokoroCardThemes`.
 * Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers (< 350 lines).
 */

(function () {
  'use strict';

  // Supported Themes Reference: 'sakura', 'polaroid', 'scrapbook', 'music', 'editorial'
  const SUPPORTED_THEMES = ['sakura', 'polaroid', 'scrapbook', 'music', 'editorial'];

  const KokoroCardExport = {
    activeEntry: null,
    activeRatio: 'square', // 'square' (1:1) or 'story' (9:16)
    activeTheme: 'sakura', // 'sakura', 'polaroid', 'scrapbook', 'music', 'editorial'
    currentBlobUrl: null,
    currentExportFile: null,
    isRendering: false,

    // DOM Elements Cache
    modalEl: null,
    canvasEl: null,
    squareBtn: null,
    storyBtn: null,
    downloadBtn: null,
    shareBtn: null,
    closeBtn: null,
    loadingEl: null,

    init() {
      this.modalEl = document.getElementById('card-export-modal');
      this.canvasEl = document.getElementById('card-export-canvas');
      this.squareBtn = document.getElementById('card-export-ratio-square');
      this.storyBtn = document.getElementById('card-export-ratio-story');
      this.downloadBtn = document.getElementById('card-export-download-btn');
      this.shareBtn = document.getElementById('card-export-share-btn');
      this.closeBtn = document.getElementById('card-export-close-btn');
      this.loadingEl = document.getElementById('card-export-loading');

      if (this.squareBtn) {
        this.squareBtn.addEventListener('click', () => this.setRatio('square'));
      }
      if (this.storyBtn) {
        this.storyBtn.addEventListener('click', () => this.setRatio('story'));
      }

      // Bind Theme Switcher Buttons (v1.6.5)
      if (this.modalEl) {
        this.modalEl.querySelectorAll('.export-theme-btn').forEach((btn) => {
          btn.addEventListener('click', (e) => {
            const theme = e.currentTarget.dataset.theme;
            if (theme) this.setTheme(theme);
          });
        });
      }

      if (this.downloadBtn) {
        this.downloadBtn.addEventListener('click', () => this.download());
      }
      if (this.shareBtn) {
        this.shareBtn.addEventListener('click', () => this.share());
      }
      if (this.closeBtn) {
        this.closeBtn.addEventListener('click', () => this.close());
      }

      // Close on backdrop click
      if (this.modalEl) {
        this.modalEl.addEventListener('click', (e) => {
          if (e.target === this.modalEl) this.close();
        });
      }

      // Close on ESC key press
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.modalEl && this.modalEl.classList.contains('active')) {
          e.preventDefault();
          this.close();
        }
      });
    },

    open(entry) {
      if (!entry) return;
      this.activeEntry = entry;
      this.activeRatio = 'square';

      if (!this.modalEl) this.init();

      if (this.modalEl) {
        this.modalEl.classList.add('active');
        if (window.lockBodyScroll) window.lockBodyScroll(true);
      }

      this.updateRatioButtons();
      this.updateThemeButtons();
      this.render();
    },

    close() {
      if (this.modalEl) {
        this.modalEl.classList.remove('active');
        if (window.lockBodyScroll) window.lockBodyScroll(false);
      }

      // Memory Hygiene: Revoke Blob URL immediately
      this.cleanupMemory();

      // Clear Canvas to free GPU memory
      if (this.canvasEl) {
        this.canvasEl.width = 0;
        this.canvasEl.height = 0;
      }
      this.activeEntry = null;
    },

    cleanupMemory() {
      if (this.currentBlobUrl) {
        try {
          URL.revokeObjectURL(this.currentBlobUrl);
        } catch (e) {
          console.warn('[CardExport] Failed to revoke object URL:', e);
        }
        this.currentBlobUrl = null;
      }
      this.currentExportFile = null;
    },

    setRatio(ratio) {
      if (this.activeRatio === ratio || this.isRendering) return;
      this.activeRatio = ratio;
      this.updateRatioButtons();
      this.render();
    },

    setTheme(theme) {
      if (this.activeTheme === theme || this.isRendering) return;
      this.activeTheme = theme;
      this.updateThemeButtons();
      this.render();
    },

    updateRatioButtons() {
      if (this.squareBtn) {
        if (this.activeRatio === 'square') {
          this.squareBtn.classList.add('active');
        } else {
          this.squareBtn.classList.remove('active');
        }
      }
      if (this.storyBtn) {
        if (this.activeRatio === 'story') {
          this.storyBtn.classList.add('active');
        } else {
          this.storyBtn.classList.remove('active');
        }
      }
    },

    updateThemeButtons() {
      if (!this.modalEl) return;
      this.modalEl.querySelectorAll('.export-theme-btn').forEach((btn) => {
        if (btn.dataset.theme === this.activeTheme) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    },

    showLoading(show = true) {
      if (this.loadingEl) {
        this.loadingEl.style.display = show ? 'flex' : 'none';
      }
      if (this.downloadBtn) this.downloadBtn.disabled = show;
      if (this.shareBtn) this.shareBtn.disabled = show;
    },

    /**
     * Standardized Export Filename (v1.6.5)
     * Format: kokoro_{theme}_{layout}_{yyyyMMdd_HHmmss}.jpg
     * e.g., kokoro_scrapbook_square_20261013_155023.jpg
     */
    getExportFilename() {
      const theme = this.activeTheme || 'sakura';
      const layout = this.activeRatio || 'square';
      const now = new Date();
      const yyyy = now.getFullYear();
      const MM = String(now.getMonth() + 1).padStart(2, '0');
      const dd = String(now.getDate()).padStart(2, '0');
      const HH = String(now.getHours()).padStart(2, '0');
      const mm = String(now.getMinutes()).padStart(2, '0');
      const ss = String(now.getSeconds()).padStart(2, '0');
      const timestamp = `${yyyy}${MM}${dd}_${HH}${mm}${ss}`;
      return `kokoro_${theme}_${layout}_${timestamp}.jpg`;
    },

    /**
     * Render Coordinator — Delegates Drawing to KokoroCardCanvasEngine
     */
    async render() {
      if (!this.canvasEl || !this.activeEntry) return;
      this.isRendering = true;
      this.showLoading(true);

      try {
        // 1. Font Gate: Ensure Google Fonts are 100% ready
        if (document.fonts && document.fonts.ready) {
          await document.fonts.ready;
        }

        const engine = window.KokoroCardCanvasEngine;
        if (!engine) {
          throw new Error('KokoroCardCanvasEngine is not loaded.');
        }

        // 2. Execute 2D Canvas rendering via dedicated engine
        await engine.renderCard(this.canvasEl, this.activeEntry, {
          ratio: this.activeRatio,
          theme: this.activeTheme
        });

        // 3. Pre-generate Blob & File for Instant iOS Safari Web Share
        this.cleanupMemory();
        const canvas = this.canvasEl;
        await new Promise((resolve) => {
          canvas.toBlob((blob) => {
            if (blob) {
              this.currentBlobUrl = URL.createObjectURL(blob);
              const filename = this.getExportFilename();
              try {
                this.currentExportFile = new File([blob], filename, { type: 'image/png' });
              } catch (e) {
                this.currentExportFile = blob;
              }
            }
            resolve();
          }, 'image/png');
        });

      } catch (err) {
        console.error('[KokoroCardExport] Render failed:', err);
        if (window.KokoroToast) {
          window.KokoroToast.show('Không thể tạo thẻ ảnh: ' + err.message, 'error');
        }
      } finally {
        this.isRendering = false;
        this.showLoading(false);
      }
    },

    /**
     * Download Card Image to Local Disk
     */
    download() {
      if (!this.currentBlobUrl || !this.activeEntry) return;
      const filename = this.getExportFilename();

      const link = document.createElement('a');
      link.download = filename;
      link.href = this.currentBlobUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      if (window.KokoroToast) {
        window.KokoroToast.show('Đã tải thẻ ảnh kỷ niệm về máy 🌸', 'success');
      }
    },

    /**
     * Share Card Image (Web Share API with fallback to Download)
     * Executes synchronously within user activation to prevent Safari NotAllowedError
     */
    async share() {
      if (!this.activeEntry) return;

      const title = this.activeEntry.title || 'Khoảnh khắc nhật ký Kokoro';
      const text = this.activeEntry.content ? this.activeEntry.content.slice(0, 100) : 'Lắng đọng tâm trí cùng Kokoro Journal 🌸';

      // 1. Web Share API with File payload (iOS Safari & Android PWA)
      if (this.currentExportFile && navigator.canShare) {
        try {
          const shareData = {
            files: [this.currentExportFile],
            title: title,
            text: text
          };

          if (navigator.canShare(shareData)) {
            await navigator.share(shareData);
            if (window.KokoroToast) {
              window.KokoroToast.show('Đã mở bảng chia sẻ khoảnh khắc ✨', 'success');
            }
            return;
          }
        } catch (err) {
          if (err.name !== 'AbortError') {
            console.warn('[KokoroCardExport] Web Share API failed, fallback to download:', err);
          } else {
            return;
          }
        }
      }

      // 2. Fallback to direct download
      this.download();
    },

    // Backward-compatible accessors forwarding to modular engines
    get CARD_THEMES() { return (window.KokoroCardThemes && window.KokoroCardThemes.CARD_THEMES) || {}; },
    drawRoundedRect(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawRoundedRect(...args); },
    drawImageCover(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawImageCover(...args); },
    wrapAndFitText(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.wrapAndFitText(...args); },
    drawFormattedLines(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawFormattedLines(...args); },
    formatCardDate(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.formatCardDate(...args); },
    formatFilmDate(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.formatFilmDate(...args); },
    drawDotGrid(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawDotGrid(...args); },
    drawWashiTapeGingham(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawWashiTapeGingham(...args); },
    drawDoodleHeart(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawDoodleHeart(...args); },
    drawMemoryMetadata(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawMemoryMetadata(...args); },
    drawPhotoFrame(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawPhotoFrame(...args); },
    drawDecorations(...args) { return window.KokoroCardCanvasEngine && window.KokoroCardCanvasEngine.drawDecorations(...args); }
  };

  // Export to global scope
  window.KokoroCardExport = KokoroCardExport;

  // CommonJS export for testing
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KokoroCardExport };
  }
})();
