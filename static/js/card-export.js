/**
 * KOKORO (心) — DAILY CARD EXPORT ENGINE (v1.6.3)
 * High-DPI Canvas Rendering Engine for Journal Memories.
 * Fixed 1080p Canvas Buffers (1080x1080 Square & 1080x1920 Story) to prevent iOS Safari memory crashes.
 * Core Philosophy: "CÓ GÌ HIỂN THỊ NẤY" (Adaptive Layout: Photo+Text, Text-Only, Photo-Only).
 * Features:
 * - Font Gate (document.fonts.ready)
 * - Mini Inline Formatter: **bold** (700) and ==highlight== (Pastel Marker Stroke)
 * - Smart Vietnamese Word-Wrap preserving user paragraph line-breaks (\r?\n) & safe truncation (...)
 * - Pre-generated Blob/File for Instant iOS Safari Web Share API (Prevents NotAllowedError)
 * - Strict Memory Hygiene (URL.revokeObjectURL & Canvas Buffer Reset)
 */

(function () {
  'use strict';

  const KokoroCardExport = {
    activeEntry: null,
    activeRatio: 'square', // 'square' (1:1) or 'story' (9:16)
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
        } catch (e) {}
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

    showLoading(show = true) {
      if (this.loadingEl) {
        this.loadingEl.style.display = show ? 'flex' : 'none';
      }
      if (this.downloadBtn) this.downloadBtn.disabled = show;
      if (this.shareBtn) this.shareBtn.disabled = show;
    },

    /**
     * Safe Image Loader with CORS & Timeout
     */
    loadImageSafe(src) {
      return new Promise((resolve) => {
        if (!src) return resolve(null);
        const img = new Image();
        img.crossOrigin = 'anonymous';
        let resolved = false;

        const timer = setTimeout(() => {
          if (!resolved) {
            resolved = true;
            img.src = '';
            resolve(null);
          }
        }, 5000);

        img.onload = () => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timer);
            resolve(img);
          }
        };

        img.onerror = () => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timer);
            resolve(null);
          }
        };

        img.src = src;
      });
    },

    /**
     * Rounded Rectangle Helper (Cross-browser fallback)
     */
    drawRoundedRect(ctx, x, y, width, height, radius) {
      if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(x, y, width, height, radius);
        return;
      }
      const r = Math.min(radius, width / 2, height / 2);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.lineTo(x + width - r, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + r);
      ctx.lineTo(x + width, y + height - r);
      ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
      ctx.lineTo(x + r, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - r);
      ctx.lineTo(x, y + r);
      ctx.quadraticCurveTo(x, y, x + r, y);
      ctx.closePath();
    },

    /**
     * Draw Image with Object-Fit Cover & Rounded Corners
     */
    drawImageCover(ctx, img, x, y, width, height, radius) {
      if (!img) return;
      ctx.save();
      this.drawRoundedRect(ctx, x, y, width, height, radius);
      ctx.clip();

      const imgRatio = img.naturalWidth / img.naturalHeight;
      const targetRatio = width / height;
      let sx, sy, sWidth, sHeight;

      if (imgRatio > targetRatio) {
        sHeight = img.naturalHeight;
        sWidth = sHeight * targetRatio;
        sx = (img.naturalWidth - sWidth) / 2;
        sy = 0;
      } else {
        sWidth = img.naturalWidth;
        sHeight = sWidth / targetRatio;
        sx = 0;
        sy = (img.naturalHeight - sHeight) / 2;
      }

      ctx.drawImage(img, sx, sy, sWidth, sHeight, x, y, width, height);
      ctx.restore();
    },

    /**
     * Tokenize a paragraph into words with inline formatting metadata:
     * - **bold**: isBold = true
     * - ==highlight==: isHighlight = true
     */
    tokenizeParagraph(paragraph) {
      if (!paragraph) return [];
      const regex = /(\*\*.*?\*\*|==.*?==)/g;
      const parts = paragraph.split(regex);
      const words = [];

      for (const part of parts) {
        if (!part) continue;
        let text = part;
        let isBold = false;
        let isHighlight = false;

        if (text.startsWith('**') && text.endsWith('**') && text.length >= 4) {
          isBold = true;
          text = text.slice(2, -2);
          if (text.startsWith('==') && text.endsWith('==') && text.length >= 4) {
            isHighlight = true;
            text = text.slice(2, -2);
          }
        } else if (text.startsWith('==') && text.endsWith('==') && text.length >= 4) {
          isHighlight = true;
          text = text.slice(2, -2);
          if (text.startsWith('**') && text.endsWith('**') && text.length >= 4) {
            isBold = true;
            text = text.slice(2, -2);
          }
        }

        const tokenWords = text.split(/\s+/).filter(Boolean);
        for (const w of tokenWords) {
          words.push({ text: w, isBold, isHighlight });
        }
      }

      return words;
    },

    /**
     * Smart Vietnamese Word-Wrap Engine with Paragraph Line-Break Preservation (\r?\n)
     * and Mini Inline Formatter support (**bold** & ==highlight==)
     */
    wrapAndFitText(ctx, text, maxWidth, maxHeight, lineHeight, normalFont, boldFont) {
      if (!text) return [];
      const paragraphs = text.split(/\r?\n/);
      const lines = [];
      const maxLines = Math.max(1, Math.floor(maxHeight / lineHeight));
      let reachedLimit = false;

      ctx.font = normalFont;
      const spaceWidth = ctx.measureText(' ').width;

      for (let pIdx = 0; pIdx < paragraphs.length; pIdx++) {
        const paragraph = paragraphs[pIdx].trim();

        // Empty paragraph preservation
        if (!paragraph) {
          if (lines.length < maxLines) {
            lines.push({ chunks: [], isBlank: true, totalWidth: 0 });
          } else {
            reachedLimit = true;
            break;
          }
          continue;
        }

        const words = this.tokenizeParagraph(paragraph);
        let currentLineChunks = [];
        let currentLineWidth = 0;

        for (let wIdx = 0; wIdx < words.length; wIdx++) {
          const wordObj = words[wIdx];
          ctx.font = wordObj.isBold ? boldFont : normalFont;
          const wordWidth = ctx.measureText(wordObj.text).width;
          const neededWidth = currentLineWidth === 0 ? wordWidth : currentLineWidth + spaceWidth + wordWidth;

          if (neededWidth <= maxWidth) {
            currentLineChunks.push({
              text: wordObj.text,
              isBold: wordObj.isBold,
              isHighlight: wordObj.isHighlight,
              width: wordWidth
            });
            currentLineWidth = neededWidth;
          } else {
            // Line is full
            if (lines.length + 1 >= maxLines) {
              reachedLimit = true;
              ctx.font = normalFont;
              const dotsWidth = ctx.measureText('...').width;
              while (currentLineChunks.length > 0 && currentLineWidth + dotsWidth > maxWidth) {
                const popped = currentLineChunks.pop();
                currentLineWidth -= (popped.width + spaceWidth);
              }
              currentLineChunks.push({ text: '...', isBold: false, isHighlight: false, width: dotsWidth });
              lines.push({ chunks: currentLineChunks, isBlank: false, totalWidth: currentLineWidth + dotsWidth });
              break;
            } else {
              lines.push({ chunks: currentLineChunks, isBlank: false, totalWidth: currentLineWidth });
              currentLineChunks = [{
                text: wordObj.text,
                isBold: wordObj.isBold,
                isHighlight: wordObj.isHighlight,
                width: wordWidth
              }];
              currentLineWidth = wordWidth;
            }
          }
        }

        if (reachedLimit) break;

        if (currentLineChunks.length > 0) {
          if (lines.length + 1 > maxLines) {
            ctx.font = normalFont;
            const dotsWidth = ctx.measureText('...').width;
            while (currentLineChunks.length > 0 && currentLineWidth + dotsWidth > maxWidth) {
              const popped = currentLineChunks.pop();
              currentLineWidth -= (popped.width + spaceWidth);
            }
            currentLineChunks.push({ text: '...', isBold: false, isHighlight: false, width: dotsWidth });
            lines.push({ chunks: currentLineChunks, isBlank: false, totalWidth: currentLineWidth + dotsWidth });
            break;
          } else {
            lines.push({ chunks: currentLineChunks, isBlank: false, totalWidth: currentLineWidth });
          }
        }
      }

      return lines;
    },

    /**
     * Render Formatted Lines onto Canvas with Highlighter Stroke and Bold styling
     */
    drawFormattedLines(ctx, lines, startX, startY, lineHeight, normalFont, boldFont, normalColor, align = 'left', maxWidth = 0) {
      ctx.font = normalFont;
      const spaceWidth = ctx.measureText(' ').width;

      let y = startY;
      for (const line of lines) {
        if (line.isBlank) {
          y += lineHeight * 0.65;
          continue;
        }

        let x = startX;
        if (align === 'center') {
          x = startX + (maxWidth - line.totalWidth) / 2;
        }

        // Pass 1: Draw Pastel Highlighter Stroke behind text
        let tempX = x;
        for (let i = 0; i < line.chunks.length; i++) {
          const chunk = line.chunks[i];
          if (chunk.isHighlight) {
            ctx.save();
            // Soft Yellow / Warm Rose Highlighter Marker
            ctx.fillStyle = 'rgba(253, 224, 71, 0.48)';
            this.drawRoundedRect(ctx, tempX - 4, y + lineHeight * 0.42, chunk.width + 8, lineHeight * 0.44, 4);
            ctx.fill();
            ctx.restore();
          }
          tempX += chunk.width + spaceWidth;
        }

        // Pass 2: Draw Text Glyphs
        tempX = x;
        ctx.textBaseline = 'top';
        for (let i = 0; i < line.chunks.length; i++) {
          const chunk = line.chunks[i];
          ctx.save();
          ctx.font = chunk.isBold ? boldFont : normalFont;
          ctx.fillStyle = normalColor;
          ctx.fillText(chunk.text, tempX, y);
          ctx.restore();
          tempX += chunk.width + spaceWidth;
        }

        y += lineHeight;
      }
    },

    /**
     * Main Render Routine — Adaptive "CÓ GÌ HIỂN THỊ NẤY"
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

        const entry = this.activeEntry;
        const isStory = this.activeRatio === 'story';
        const canvas = this.canvasEl;
        const ctx = canvas.getContext('2d');

        // 2. Fixed 1080p Buffer (NO DPR MULTIPLIER to prevent iOS Safari memory crashes)
        const targetWidth = 1080;
        const targetHeight = isStory ? 1920 : 1080;
        canvas.width = targetWidth;
        canvas.height = targetHeight;

        // 3. Draw Ambient Sakura Gradient Background
        const bgGrad = ctx.createLinearGradient(0, 0, targetWidth, targetHeight);
        bgGrad.addColorStop(0, '#fff1f4');
        bgGrad.addColorStop(0.5, '#fdf2f7');
        bgGrad.addColorStop(1, '#fce7f3');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, targetWidth, targetHeight);

        // Soft Glowing Ambient Orbs
        ctx.save();
        const orb1 = ctx.createRadialGradient(180, 180, 20, 180, 180, 360);
        orb1.addColorStop(0, 'rgba(251, 113, 133, 0.22)');
        orb1.addColorStop(1, 'rgba(251, 113, 133, 0)');
        ctx.fillStyle = orb1;
        ctx.fillRect(0, 0, 600, 600);

        const orb2 = ctx.createRadialGradient(targetWidth - 180, targetHeight - 200, 20, targetWidth - 180, targetHeight - 200, 420);
        orb2.addColorStop(0, 'rgba(244, 114, 182, 0.25)');
        orb2.addColorStop(1, 'rgba(244, 114, 182, 0)');
        ctx.fillStyle = orb2;
        ctx.fillRect(targetWidth - 600, targetHeight - 650, 600, 650);
        ctx.restore();

        // 4. Draw Center Frosted Glass Card Panel
        const cardMarginX = isStory ? 70 : 64;
        const cardMarginY = isStory ? 80 : 64;
        const cardWidth = targetWidth - cardMarginX * 2;
        const cardHeight = targetHeight - cardMarginY * 2;
        const cardRadius = 44;

        ctx.save();
        ctx.shadowColor = 'rgba(244, 114, 182, 0.16)';
        ctx.shadowBlur = 48;
        ctx.shadowOffsetY = 16;
        this.drawRoundedRect(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, cardRadius);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.88)';
        ctx.fill();
        ctx.restore();

        // Glass Border
        ctx.save();
        this.drawRoundedRect(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, cardRadius);
        ctx.strokeStyle = 'rgba(244, 114, 182, 0.35)';
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.restore();

        // 5. Header: Category Pill, Date & Time, Weather Icon
        let cursorY = cardMarginY + 68;
        const paddingInner = 56;
        const contentLeft = cardMarginX + paddingInner;
        const contentWidth = cardWidth - paddingInner * 2;

        // Category Badge
        const catName = entry.categoryName || entry.mood || 'Bình yên';
        const catIcon = entry.categoryIcon || '🌸';
        const catColor = entry.categoryColor || '#ec4899';

        ctx.save();
        ctx.font = '700 24px "Plus Jakarta Sans", "Outfit", -apple-system, sans-serif';
        const catText = `${catIcon}  ${catName}`;
        const catMetrics = ctx.measureText(catText);
        const pillW = catMetrics.width + 36;
        const pillH = 46;
        const pillX = contentLeft;
        const pillY = cursorY - 32;

        this.drawRoundedRect(ctx, pillX, pillY, pillW, pillH, 23);
        ctx.fillStyle = catColor.startsWith('#') ? `${catColor}22` : 'rgba(236, 72, 153, 0.15)';
        ctx.fill();
        this.drawRoundedRect(ctx, pillX, pillY, pillW, pillH, 23);
        ctx.strokeStyle = catColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = catColor;
        ctx.textBaseline = 'middle';
        ctx.fillText(catText, pillX + 18, pillY + pillH / 2);
        ctx.restore();

        // Date & Weather (Right-aligned in Header)
        const dateStr = entry.displayDate || entry.entryDate || '';
        const weatherIcons = {
          sunny: '☀️',
          rainy: '🌧️',
          cloudy: '⛅',
          windy: '🍃',
          snowy: '❄️'
        };
        const weatherIcon = entry.weather && weatherIcons[entry.weather] ? weatherIcons[entry.weather] : '';
        const metaRightText = weatherIcon ? `${dateStr}  ${weatherIcon}` : dateStr;

        ctx.save();
        ctx.font = '600 22px "Plus Jakarta Sans", -apple-system, sans-serif';
        ctx.fillStyle = '#64748b';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(metaRightText, cardMarginX + cardWidth - paddingInner, cursorY - 9);
        ctx.restore();

        cursorY += 60;

        // 6. Layout Determination: "CÓ GÌ HIỂN THỊ NẤY"
        const hasPhoto = entry.photos && entry.photos.length > 0;
        const hasTitle = Boolean(entry.title && entry.title.trim());
        const hasContent = Boolean(entry.content && entry.content.trim());
        const hasText = hasTitle || hasContent;

        if (hasPhoto && !hasText) {
          // =========================================================
          // LAYOUT 1: PHOTO-ONLY MODE (Thuần Ảnh — Khung ảnh chiếm diện tích chính)
          // =========================================================
          const photoUrl = window.KokoroAPI.resolveMediaUrl(entry.photos[0].url || entry.photos[0].thumbUrl);
          const photoImg = await this.loadImageSafe(photoUrl);

          const footerSpace = 100;
          const photoH = (cardMarginY + cardHeight - footerSpace) - cursorY;
          const photoW = contentWidth;
          const photoX = contentLeft;
          const photoY = cursorY;

          if (photoImg) {
            this.drawImageCover(ctx, photoImg, photoX, photoY, photoW, photoH, 32);
          }

          // Multiple Photos Badge
          if (entry.photos.length > 1) {
            const extraCount = `+${entry.photos.length - 1} ảnh`;
            ctx.save();
            ctx.font = '700 22px "Plus Jakarta Sans", sans-serif';
            const badgeW = ctx.measureText(extraCount).width + 30;
            const badgeH = 42;
            const badgeX = photoX + photoW - badgeW - 20;
            const badgeY = photoY + photoH - badgeH - 20;

            this.drawRoundedRect(ctx, badgeX, badgeY, badgeW, badgeH, 21);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.76)';
            ctx.fill();

            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(extraCount, badgeX + badgeW / 2, badgeY + badgeH / 2);
            ctx.restore();
          }

        } else if (hasPhoto && hasText) {
          // =========================================================
          // LAYOUT 2: PHOTO + TEXT MODE (Tạp Chí Ảnh — Ảnh trên, Chữ dưới)
          // =========================================================
          const photoUrl = window.KokoroAPI.resolveMediaUrl(entry.photos[0].url || entry.photos[0].thumbUrl);
          const photoImg = await this.loadImageSafe(photoUrl);

          const photoH = isStory ? 760 : 420;
          const photoW = contentWidth;
          const photoX = contentLeft;
          const photoY = cursorY;

          if (photoImg) {
            this.drawImageCover(ctx, photoImg, photoX, photoY, photoW, photoH, 28);
          } else {
            ctx.save();
            this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, 28);
            ctx.fillStyle = 'rgba(244, 114, 182, 0.1)';
            ctx.fill();
            ctx.font = '600 24px "Plus Jakarta Sans", sans-serif';
            ctx.fillStyle = '#f472b6';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('🌸 Kokoro Memory', photoX + photoW / 2, photoY + photoH / 2);
            ctx.restore();
          }

          // Multiple Photos Badge (+X ảnh)
          if (entry.photos.length > 1) {
            const extraCount = `+${entry.photos.length - 1} ảnh`;
            ctx.save();
            ctx.font = '700 20px "Plus Jakarta Sans", sans-serif';
            const badgeW = ctx.measureText(extraCount).width + 26;
            const badgeH = 36;
            const badgeX = photoX + photoW - badgeW - 16;
            const badgeY = photoY + photoH - badgeH - 16;

            this.drawRoundedRect(ctx, badgeX, badgeY, badgeW, badgeH, 18);
            ctx.fillStyle = 'rgba(15, 23, 42, 0.72)';
            ctx.fill();

            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(extraCount, badgeX + badgeW / 2, badgeY + badgeH / 2);
            ctx.restore();
          }

          cursorY += photoH + 42;

          // Title with Formatter
          if (hasTitle) {
            const titleNormalFont = '800 36px "Outfit", "Plus Jakarta Sans", sans-serif';
            const titleBoldFont = '900 36px "Outfit", "Plus Jakarta Sans", sans-serif';
            const titleLineH = 46;
            const titleLines = this.wrapAndFitText(ctx, entry.title, contentWidth, 92, titleLineH, titleNormalFont, titleBoldFont);

            this.drawFormattedLines(ctx, titleLines, contentLeft, cursorY, titleLineH, titleNormalFont, titleBoldFont, '#0f172a', 'left');
            cursorY += titleLines.length * titleLineH + 12;
          }

          // Content with Formatter
          if (hasContent) {
            const contentNormalFont = '500 27px "Plus Jakarta Sans", -apple-system, sans-serif';
            const contentBoldFont = '700 27px "Plus Jakarta Sans", -apple-system, sans-serif';
            const contentLineH = 44;

            const footerSpace = 130;
            const availableHeight = (cardMarginY + cardHeight - footerSpace) - cursorY;
            const contentLines = this.wrapAndFitText(ctx, entry.content, contentWidth, availableHeight, contentLineH, contentNormalFont, contentBoldFont);

            this.drawFormattedLines(ctx, contentLines, contentLeft, cursorY, contentLineH, contentNormalFont, contentBoldFont, '#334155', 'left');
          }

        } else {
          // =========================================================
          // LAYOUT 3: TEXT-ONLY ZEN QUOTE MODE (Trang Tản Văn — Cỡ chữ lớn, căn chỉnh thanh thoát)
          // =========================================================
          cursorY += isStory ? 80 : 30;

          // Zen Quote Decorative Emblem
          ctx.save();
          ctx.font = isStory ? '64px sans-serif' : '52px sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('🌸', targetWidth / 2, cursorY);
          ctx.restore();

          cursorY += isStory ? 80 : 60;

          // Title with Formatter
          if (hasTitle) {
            const titleNormalFont = isStory ? '800 50px "Outfit", "Plus Jakarta Sans", sans-serif' : '800 42px "Outfit", "Plus Jakarta Sans", sans-serif';
            const titleBoldFont = isStory ? '900 50px "Outfit", "Plus Jakarta Sans", sans-serif' : '900 42px "Outfit", "Plus Jakarta Sans", sans-serif';
            const titleLineH = isStory ? 64 : 54;
            const titleMaxHeight = isStory ? 160 : 120;

            const titleLines = this.wrapAndFitText(ctx, entry.title, contentWidth, titleMaxHeight, titleLineH, titleNormalFont, titleBoldFont);
            this.drawFormattedLines(ctx, titleLines, contentLeft, cursorY, titleLineH, titleNormalFont, titleBoldFont, '#0f172a', 'center', contentWidth);
            cursorY += titleLines.length * titleLineH + (isStory ? 36 : 24);
          }

          // Subtle Divider Line
          ctx.save();
          const divW = isStory ? 160 : 120;
          ctx.beginPath();
          ctx.moveTo((targetWidth - divW) / 2, cursorY);
          ctx.lineTo((targetWidth + divW) / 2, cursorY);
          ctx.strokeStyle = 'rgba(244, 114, 182, 0.45)';
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.restore();

          cursorY += isStory ? 54 : 36;

          // Content with Formatter in Zen Style
          if (hasContent) {
            const contentNormalFont = isStory ? '500 36px "Plus Jakarta Sans", -apple-system, sans-serif' : '500 31px "Plus Jakarta Sans", -apple-system, sans-serif';
            const contentBoldFont = isStory ? '700 36px "Plus Jakarta Sans", -apple-system, sans-serif' : '700 31px "Plus Jakarta Sans", -apple-system, sans-serif';
            const contentLineH = isStory ? 60 : 50;

            const footerSpace = 130;
            const availableHeight = (cardMarginY + cardHeight - footerSpace) - cursorY;
            const contentLines = this.wrapAndFitText(ctx, entry.content, contentWidth, availableHeight, contentLineH, contentNormalFont, contentBoldFont);

            this.drawFormattedLines(ctx, contentLines, contentLeft, cursorY, contentLineH, contentNormalFont, contentBoldFont, '#334155', 'center', contentWidth);
          }
        }

        // 7. Footer: Tags & Brand Watermark
        const footerY = cardMarginY + cardHeight - 54;

        // Tags (Left)
        if (entry.tags && entry.tags.length > 0) {
          ctx.save();
          ctx.font = '600 20px "Plus Jakarta Sans", sans-serif';
          ctx.fillStyle = '#ec4899';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          const tagsText = entry.tags.map((t) => (t.startsWith('#') ? t : `#${t}`)).slice(0, 3).join('  ');
          ctx.fillText(tagsText, contentLeft, footerY);
          ctx.restore();
        }

        // Watermark (Right)
        ctx.save();
        ctx.font = '700 21px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#64748b';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText('🌸 Kokoro (心) Journal', cardMarginX + cardWidth - paddingInner, footerY);
        ctx.restore();

        // 8. Pre-generate Blob & File for Instant iOS Safari Web Share
        this.cleanupMemory();
        await new Promise((resolve) => {
          canvas.toBlob((blob) => {
            if (blob) {
              this.currentBlobUrl = URL.createObjectURL(blob);
              const datePart = (entry.entryDate || new Date().toISOString().slice(0, 10)).replace(/-/g, '');
              const filename = `kokoro-${datePart}-${this.activeRatio}.png`;
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
      const datePart = (this.activeEntry.entryDate || new Date().toISOString().slice(0, 10)).replace(/-/g, '');
      const filename = `kokoro-card-${datePart}-${this.activeRatio}.png`;

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
          // User aborted share dialog or permission denied
          if (err.name !== 'AbortError') {
            console.warn('[KokoroCardExport] Web Share API failed, fallback to download:', err);
          } else {
            return;
          }
        }
      }

      // 2. Fallback to direct download
      this.download();
    }
  };

  // Export to window
  window.KokoroCardExport = KokoroCardExport;

  // CommonJS support for tests
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KokoroCardExport };
  }
})();
