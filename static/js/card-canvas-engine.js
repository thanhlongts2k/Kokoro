/**
 * KOKORO (心) — CARD CANVAS RENDERING ENGINE (v1.7.0)
 * Mathematical 2D Canvas Renderer for Memory Cards.
 * Fixed 1080p Canvas Buffers (1080x1080 Square & 1080x1920 Story) to prevent iOS Safari memory crashes.
 * Core Philosophy: "CÓ GÌ HIỂN THỊ NẤY" (Adaptive Layout: Photo+Text, Text-Only, Photo-Only).
 * Complies with AGENTS.md: Modular Layered Architecture, Strict Typing, Zero Magic Numbers.
 */

(function () {
  'use strict';

  const KokoroCardCanvasEngine = {
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
     * Safe Image Loader with Dual Offline Fallback (v1.8.6)
     * Tries original URL first; if failed/offline, falls back to thumbUrl (CacheStorage)
     */
    async loadPhotoWithFallback(photo) {
      if (!photo) return null;
      const rawUrl = photo.url || photo.thumbUrl;
      const primaryUrl = window.KokoroAPI ? window.KokoroAPI.resolveMediaUrl(rawUrl) : rawUrl;
      let img = await this.loadImageSafe(primaryUrl);
      if (!img && photo.thumbUrl && photo.url && photo.thumbUrl !== photo.url) {
        const fallbackUrl = window.KokoroAPI ? window.KokoroAPI.resolveMediaUrl(photo.thumbUrl) : photo.thumbUrl;
        img = await this.loadImageSafe(fallbackUrl);
      }
      return img;
    },

    /**
     * Parallel Multi-Photo Loader (v1.8.6)
     * Uses Promise.all to load multiple images concurrently, eliminating cumulative lag
     */
    async loadMultiplePhotosSafe(photos, maxCount = 4) {
      if (!photos || !photos.length) return [];
      const targetPhotos = photos.slice(0, maxCount);
      const loadPromises = targetPhotos.map((p) => this.loadPhotoWithFallback(p));
      const loadedImages = await Promise.all(loadPromises);
      return loadedImages.filter(Boolean);
    },

    /**
     * Adaptive Multi-Photo Collage / Scrapbook Engine (v1.8.6)
     * Mathematically calculates layouts for 2, 3, or 4 photos on 1080p canvas.
     * Prevents aspect ratio distortion via drawImageCover() smart focal point cropping.
     * @param {CanvasRenderingContext2D} ctx
     * @param {Array<HTMLImageElement>} images
     * @param {number} photoX
     * @param {number} photoY
     * @param {number} photoW
     * @param {number} photoH
     * @param {number} gap (default: 14)
     * @param {number} baseRadius (default: 20)
     */
    drawCollageFrame(ctx, images, photoX, photoY, photoW, photoH, gap = 14, baseRadius = 20) {
      if (!ctx || !images || !images.length) return;

      const count = images.length;

      if (count === 1) {
        // Single photo fallback
        this.drawImageCover(ctx, images[0], photoX, photoY, photoW, photoH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.restore();
        return;
      }

      if (count === 2) {
        // ====================================================================
        // KỊCH BẢN 2 ẢNH: SPLIT DUO (Chia đôi chiều rộng, 2 cột đều nhau)
        // ====================================================================
        const colW = (photoW - gap) / 2;
        const colH = photoH;

        // Ảnh 1 (Trái)
        this.drawImageCover(ctx, images[0], photoX, photoY, colW, colH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, photoX, photoY, colW, colH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.restore();

        // Ảnh 2 (Phải)
        const rightX = photoX + colW + gap;
        this.drawImageCover(ctx, images[1], rightX, photoY, colW, colH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, rightX, photoY, colW, colH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.restore();
        return;
      }

      if (count === 3) {
        // ====================================================================
        // KỊCH BẢN 3 ẢNH: MAGAZINE COVER (Hero 60% trái + 2 ảnh phụ 40% phải)
        // ====================================================================
        const leftW = Math.round((photoW - gap) * 0.60);
        const rightW = photoW - gap - leftW;
        const rightH = (photoH - gap) / 2;

        // Ảnh 1: Hero chính bên trái (chiếm 60% chiều rộng)
        this.drawImageCover(ctx, images[0], photoX, photoY, leftW, photoH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, photoX, photoY, leftW, photoH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.restore();

        // Cột phải: 2 ảnh phụ xếp dọc đều nhau
        const rightX = photoX + leftW + gap;

        // Ảnh 2: Phụ trên
        this.drawImageCover(ctx, images[1], rightX, photoY, rightW, rightH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, rightX, photoY, rightW, rightH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 3.5;
        ctx.stroke();
        ctx.restore();

        // Ảnh 3: Phụ dưới
        const sub2Y = photoY + rightH + gap;
        this.drawImageCover(ctx, images[2], rightX, sub2Y, rightW, rightH, baseRadius);
        ctx.save();
        this.drawRoundedRect(ctx, rightX, sub2Y, rightW, rightH, baseRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 3.5;
        ctx.stroke();
        ctx.restore();
        return;
      }

      // ======================================================================
      // KỊCH BẢN 4 ẢNH (HOẶC NHIỀU HƠN): BALANCED 2x2 GRID (Lưới 4 ô đều nhau)
      // ======================================================================
      const cellW = (photoW - gap) / 2;
      const cellH = (photoH - gap) / 2;
      const cellRadius = Math.min(baseRadius, 18);

      const positions = [
        { x: photoX, y: photoY },                           // Top-left
        { x: photoX + cellW + gap, y: photoY },              // Top-right
        { x: photoX, y: photoY + cellH + gap },              // Bottom-left
        { x: photoX + cellW + gap, y: photoY + cellH + gap } // Bottom-right
      ];

      for (let i = 0; i < 4 && i < count; i++) {
        const pos = positions[i];
        this.drawImageCover(ctx, images[i], pos.x, pos.y, cellW, cellH, cellRadius);

        ctx.save();
        this.drawRoundedRect(ctx, pos.x, pos.y, cellW, cellH, cellRadius);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.lineWidth = 3.5;
        ctx.stroke();
        ctx.restore();
      }
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
        // Smart Focal Point: Anchor crop at ~35% from the top (Rule of Thirds)
        // to prevent chopping faces/foreheads in portrait photos
        sy = Math.max(0, (img.naturalHeight - sHeight) * 0.35);
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
        let paragraph = paragraphs[pIdx].trim();
        // Clean raw markdown blockquote prefix '>' e.g. "> 🌸" -> "🌸"
        paragraph = paragraph.replace(/^(?:>\s*)+/, '');

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
     * Format entry date with Vietnamese Day-of-Week & Timestamp (v1.6.5)
     * e.g., "Thứ Ba • 13/10/2026, 13:12"
     */
    formatCardDate(entry) {
      if (!entry) return '';
      const rawDate = entry.created_at || entry.createdAt || entry.entry_date || entry.entryDate || entry.displayDate;
      if (!rawDate) return '';
      const d = new Date(rawDate);
      if (isNaN(d.getTime())) {
        return entry.displayDate || entry.entryDate || String(rawDate);
      }

      const weekdays = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
      const dayOfWeek = weekdays[d.getDay()];
      const day = String(d.getDate()).padStart(2, '0');
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = d.getFullYear();

      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const isDateOnly = typeof rawDate === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(rawDate.trim());

      if (!isDateOnly && (d.getHours() !== 0 || d.getMinutes() !== 0 || (typeof rawDate === 'string' && rawDate.includes('T')))) {
        return `${dayOfWeek} • ${day}/${month}/${year}, ${hours}:${minutes}`;
      }
      return `${dayOfWeek} • ${day}/${month}/${year}`;
    },

    /**
     * Format date in vintage film camera style ('26 10 13)
     */
    formatFilmDate(entry) {
      const rawDate = entry.created_at || entry.createdAt || entry.entry_date || entry.entryDate;
      const d = rawDate ? new Date(rawDate) : new Date();
      if (isNaN(d.getTime())) return "'26 10 13";
      const yy = String(d.getFullYear()).slice(-2);
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `'${yy} ${mm} ${dd}`;
    },

    /**
     * Bullet Journal Dot-Grid Texture Engine (v1.6.5)
     * Draws subtle dotted grid paper texture on warm cream background (#faf6ed)
     */
    drawDotGrid(ctx, startX, startY, width, height, spacing = 28, radius = 1, color = 'rgba(0, 0, 0, 0.06)') {
      ctx.save();
      ctx.fillStyle = color;
      const endX = startX + width;
      const endY = startY + height;
      for (let x = startX + (spacing / 2); x <= endX; x += spacing) {
        for (let y = startY + (spacing / 2); y <= endY; y += spacing) {
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.restore();
    },

    /**
     * Washi Tape Gingham Engine (v1.6.5)
     * Draws semi-transparent pastel pink gingham/caro checkered washi tape taped over photo
     */
    drawWashiTapeGingham(ctx, x, y, width, height, angle = -0.05) {
      ctx.save();
      ctx.translate(x + width / 2, y + height / 2);
      ctx.rotate(angle);

      // Tape soft drop shadow
      ctx.shadowColor = 'rgba(0, 0, 0, 0.12)';
      ctx.shadowBlur = 10;
      ctx.shadowOffsetY = 4;

      const hw = width / 2;
      const hh = height / 2;

      // Base tape rounded rectangle
      this.drawRoundedRect(ctx, -hw, -hh, width, height, 4);
      ctx.fillStyle = 'rgba(254, 215, 226, 0.88)'; // Pastel pink base
      ctx.fill();

      // Reset shadow for pattern clipping
      ctx.shadowColor = 'transparent';
      ctx.save();
      this.drawRoundedRect(ctx, -hw, -hh, width, height, 4);
      ctx.clip();

      // Checkered Gingham / Caro stripes
      const step = 10;
      const lineW = 3.5;
      ctx.fillStyle = 'rgba(244, 114, 182, 0.45)'; // Rose pink stripes

      for (let lx = -hw; lx <= hw; lx += step) {
        ctx.fillRect(lx, -hh, lineW, height);
      }
      for (let ly = -hh; ly <= hh; ly += step) {
        ctx.fillRect(-hw, ly, width, lineW);
      }
      ctx.restore();

      // Subtle edge border
      this.drawRoundedRect(ctx, -hw, -hh, width, height, 4);
      ctx.strokeStyle = 'rgba(244, 114, 182, 0.40)';
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.restore();
    },

    /**
     * Hand-Drawn Doodle Heart Helper (v1.6.5)
     * Renders pencil-sketched heart (♡) with subtle organic curvature
     */
    drawDoodleHeart(ctx, x, y, size, angle = 0, strokeColor = 'rgba(244, 114, 182, 0.85)', fillColor = 'rgba(254, 215, 226, 0.4)') {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.beginPath();
      const d = size / 2;
      ctx.moveTo(0, d * 0.4);
      ctx.bezierCurveTo(-d * 0.8, -d * 0.6, -d * 1.5, d * 0.4, 0, d * 1.4);
      ctx.bezierCurveTo(d * 1.5, d * 0.4, d * 0.8, -d * 0.6, 0, d * 0.4);
      ctx.closePath();
      if (fillColor) {
        ctx.fillStyle = fillColor;
        ctx.fill();
      }
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.4;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.stroke();
      ctx.restore();
    },

    /**
     * Memory Metadata Engine (v1.6.5)
     * Fills lower half space with nostalgic journal details:
     * - Location & Weather: "📍 Sài Gòn • 🌧️ 28°C"
     * - Writing Streak: "Ngày thứ {streak_days} 🌸"
     * - Felt-pen handwritten signature: "Ghi lại bởi {user.name} ✒️"
     */
    drawMemoryMetadata(ctx, entry, themeId, isStory, contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, footerY, cursorY) {
      if (!entry) return;

      const themeCfg = (window.KokoroCardThemes && window.KokoroCardThemes.getTheme(themeId)) || {
        textPrimary: '#0f172a',
        textSecondary: '#334155',
        textMuted: '#64748b'
      };

      // 1. Resolve Location & Weather
      const location = entry.location || entry.place || 'Sài Gòn';
      const weatherMap = {
        sunny: { icon: '☀️', temp: '32°C' },
        rainy: { icon: '🌧️', temp: '28°C' },
        cloudy: { icon: '⛅', temp: '29°C' },
        windy: { icon: '🍃', temp: '26°C' },
        snowy: { icon: '❄️', temp: '15°C' },
        cozy: { icon: '☕', temp: '25°C' },
        serene: { icon: '🌸', temp: '27°C' }
      };
      const weatherKey = (entry.weather && weatherMap[entry.weather]) ? entry.weather : 'rainy';
      const weatherInfo = weatherMap[weatherKey];
      const weatherTemp = entry.temperature ? `${entry.temperature}°C` : weatherInfo.temp;
      const weatherIcon = weatherInfo.icon;

      // 2. Resolve Streak Days
      let streakDays = entry.streak_days || entry.streakDays;
      if (!streakDays && window.app && window.app.stats && window.app.stats.streakDays) {
        streakDays = window.app.stats.streakDays;
      }
      if (!streakDays) streakDays = 142; // Nostalgic milestone default
      const streakText = `Ngày thứ ${streakDays} 🌸`;

      // 3. Resolve Author Name - Full name without truncation (e.g. "Ghi lại bởi Aria Tanaka ✒️")
      let authorName = (window.KokoroAuth && window.KokoroAuth.currentUser && window.KokoroAuth.currentUser.name) || entry.author || 'Aria Tanaka';
      authorName = authorName.replace(/\s*\(.*?\)/, '').trim() || 'Aria Tanaka';
      const signatureText = `Ghi lại bởi ${authorName} ✒️`;

      if (themeId === 'music') {
        // Music Theme: Location & Timestamp placed dynamically below music player, with full signature
        const d = entry.created_at || entry.entryDate ? new Date(entry.created_at || entry.entryDate) : new Date();
        const dateFormatted = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
        const timeFormatted = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;

        // In Story: generous breathing room below player. In Square: anchored with strict safe ceiling (at least 52px above footer)
        const metaY = isStory
          ? Math.max((cursorY || 0) + 28, footerY - 140)
          : Math.min((cursorY || 0) + 20, footerY - 54);

        ctx.save();
        ctx.font = '500 21px "Plus Jakarta Sans", monospace';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`📍 ${location}, ${dateFormatted}, ${timeFormatted} ${weatherIcon}`, contentLeft + 6, metaY);
        ctx.restore();

        // Chữ ký đầy đủ: "Ghi lại bởi {user.name} ✒️"
        ctx.save();
        ctx.font = 'italic 600 22px "Plus Jakarta Sans", cursive, sans-serif';
        ctx.fillStyle = '#c084fc';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(signatureText, contentLeft + contentWidth - 6, metaY);
        ctx.restore();
        return;
      }

      if (isStory) {
        // STORY 9:16: Airy multi-row layout filling bottom space elegantly
        const row1Y = Math.max((cursorY || 0) + 36, footerY - 145);
        const row2Y = Math.max(row1Y + 54, footerY - 72);

        // Row 1: Location & Weather
        ctx.save();
        ctx.font = '600 23px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = themeCfg.textMuted;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`📍 ${location} • ${weatherIcon} ${weatherTemp}`, contentLeft + 6, row1Y);
        ctx.restore();

        // Row 2: Left = Streak milestone
        ctx.save();
        ctx.font = '700 23px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = themeCfg.textPrimary;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(streakText, contentLeft + 6, row2Y);
        ctx.restore();

        // Row 2: Right = Signature
        ctx.save();
        ctx.font = 'italic 600 24px "Plus Jakarta Sans", cursive, sans-serif';
        ctx.fillStyle = themeCfg.textPrimary;
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(signatureText, contentLeft + contentWidth - 6, row2Y);
        ctx.restore();

      } else {
        // SQUARE 1:1: Compact layout
        const metaY = Math.max((cursorY || 0) + 20, footerY - 55);

        ctx.save();
        ctx.font = '600 20px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = themeCfg.textMuted;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`📍 ${location} • ${weatherIcon} ${weatherTemp}  •  ${streakText}`, contentLeft + 4, metaY);
        ctx.restore();

        ctx.save();
        ctx.font = 'italic 600 20px "Plus Jakarta Sans", cursive, sans-serif';
        ctx.fillStyle = themeCfg.textPrimary;
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(signatureText, contentLeft + contentWidth - 4, metaY);
        ctx.restore();
      }
    },

    /**
     * Studio Photo Frame Engine (v1.6.5)
     * Handles specialized frames for: sakura, polaroid, scrapbook, music, editorial
     */
    drawPhotoFrame(ctx, entry, photoImg, photoX, photoY, photoW, photoH, baseRadius, isStory, theme) {
      const themeId = theme || 'sakura';

      if (themeId === 'polaroid' || themeId === 'scrapbook') {
        // 🎞️ POLAROID & 💌 SCRAPBOOK: Tilted photo frame (-2.6°) with soft drop shadow & Washi tape
        const tiltAngle = -0.046; // ~ -2.65 degrees (-2.5° to -3°)
        const cx = photoX + photoW / 2;
        const cy = photoY + photoH / 2;

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(tiltAngle);

        ctx.shadowColor = 'rgba(0, 0, 0, 0.12)';
        ctx.shadowBlur = 32;
        ctx.shadowOffsetY = 14;
        ctx.shadowOffsetX = -4;

        const halfW = photoW / 2;
        const halfH = photoH / 2;
        const polaroidRadius = 16;
        this.drawRoundedRect(ctx, -halfW, -halfH, photoW, photoH, polaroidRadius);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        ctx.shadowColor = 'transparent';

        const framePadSide = 22;
        const framePadTop = 22;
        const bottomChin = 62;
        const innerX = -halfW + framePadSide;
        const innerY = -halfH + framePadTop;
        const innerW = photoW - framePadSide * 2;
        const innerH = photoH - framePadTop - bottomChin;

        if (photoImg) {
          this.drawImageCover(ctx, photoImg, innerX, innerY, innerW, innerH, 8);
          // Delicate inner border outline
          ctx.save();
          this.drawRoundedRect(ctx, innerX, innerY, innerW, innerH, 8);
          ctx.strokeStyle = 'rgba(0, 0, 0, 0.08)';
          ctx.lineWidth = 1.2;
          ctx.stroke();
          ctx.restore();
        } else {
          ctx.save();
          this.drawRoundedRect(ctx, innerX, innerY, innerW, innerH, 8);
          ctx.fillStyle = themeId === 'polaroid' ? 'rgba(217, 119, 6, 0.08)' : 'rgba(244, 114, 182, 0.08)';
          ctx.fill();
          ctx.restore();
        }

        // Orange film camera timestamp in bottom right chin ('26 10 13)
        const filmDate = this.formatFilmDate(entry);
        ctx.save();
        ctx.font = '700 22px "Courier New", monospace';
        ctx.fillStyle = themeId === 'polaroid' ? '#ea580c' : '#db2777';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(filmDate, innerX + innerW - 6, -halfH + photoH - (bottomChin / 2));
        ctx.restore();

        // Washi Tape (Semi-transparent pastel pink gingham / caro checkered tape taped over top edge)
        // ONLY drawn for 'scrapbook'. Theme 'polaroid' is clean minimal film style without tape.
        if (themeId === 'scrapbook') {
          this.drawWashiTapeGingham(ctx, -halfW + photoW * 0.32, -halfH - 14, 140, 36, -0.05);
        }

        ctx.restore();

      } else if (themeId === 'music') {
        // 🎵 MUSIC THEME: Neon violet ambient glow & glass frame
        ctx.save();
        ctx.shadowColor = 'rgba(192, 132, 252, 0.35)';
        ctx.shadowBlur = 32;
        ctx.shadowOffsetY = 8;
        this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, 24);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.6)';
        ctx.fill();
        ctx.restore();

        const innerPad = 6;
        if (photoImg) {
          this.drawImageCover(ctx, photoImg, photoX + innerPad, photoY + innerPad, photoW - innerPad * 2, photoH - innerPad * 2, 20);
        }

        ctx.save();
        this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, 24);
        ctx.strokeStyle = 'rgba(192, 132, 252, 0.45)';
        ctx.lineWidth = 2.5;
        ctx.stroke();
        ctx.restore();

      } else {
        // 🌸 SAKURA & 📰 EDITORIAL THEMES: Elegant rounded card with clean soft border
        const framePad = 7;
        const photoRadius = 24;

        ctx.save();
        ctx.shadowColor = themeId === 'editorial' ? 'rgba(0, 0, 0, 0.07)' : 'rgba(15, 23, 42, 0.08)';
        ctx.shadowBlur = 24;
        ctx.shadowOffsetY = 8;
        this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, photoRadius + 4);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.restore();

        if (photoImg) {
          this.drawImageCover(ctx, photoImg, photoX + framePad, photoY + framePad, photoW - framePad * 2, photoH - framePad * 2, photoRadius);

          ctx.save();
          this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, photoRadius + 4);
          ctx.strokeStyle = themeId === 'editorial' ? 'rgba(15, 23, 42, 0.12)' : 'rgba(255, 255, 255, 0.85)';
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.restore();
        } else {
          ctx.save();
          this.drawRoundedRect(ctx, photoX + framePad, photoY + framePad, photoW - framePad * 2, photoH - framePad * 2, photoRadius);
          ctx.fillStyle = 'rgba(244, 114, 182, 0.1)';
          ctx.fill();
          ctx.font = '600 24px "Plus Jakarta Sans", sans-serif';
          ctx.fillStyle = '#f472b6';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('🌸 Kokoro Memory', photoX + photoW / 2, photoY + photoH / 2);
          ctx.restore();
        }
      }
    },

    /**
     * Studio Decorations Engine (v1.6.5)
     * Handles specialized accents:
     * - scrapbook: vintage circular postal cancellation stamp & hand-drawn doodle hearts
     * - music: mini audio player timeline bar (01:43 ──●── 03:20), waveforms, floating notes & Now Playing
     * - editorial: large translucent quote watermark behind text
     */
    drawDecorations(ctx, entry, layout, theme, isStory, targetWidth, targetHeight, cursorY, contentLines, contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, footerY, photoBounds) {
      const themeId = theme || 'sakura';

      if (themeId === 'scrapbook') {
        // Double-ring Vintage Postal Cancellation Stamp (AIR MAIL)
        // Stamped safely across the Polaroid photo frame's corner, completely clear of header text!
        ctx.save();
        const photoTop = (photoBounds && photoBounds.y) ? photoBounds.y : (cardMarginY + (isStory ? 220 : 160));
        const stampX = cardMarginX + cardWidth - 115;
        const stampY = photoTop + 65;
        ctx.translate(stampX, stampY);
        ctx.rotate(0.12);
        ctx.strokeStyle = 'rgba(225, 29, 72, 0.28)';
        ctx.lineWidth = 2.5;

        // Double ring
        ctx.beginPath(); ctx.arc(0, 0, 42, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(0, 0, 36, 0, Math.PI * 2); ctx.stroke();

        ctx.font = '800 10.5px sans-serif';
        ctx.fillStyle = 'rgba(225, 29, 72, 0.32)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('KOKORO POST', 0, -11);
        ctx.fillText('AIR MAIL 🌸', 0, 11);

        // Wavy cancel lines
        ctx.beginPath();
        for (let i = -2; i <= 2; i++) {
          ctx.moveTo(46, i * 7.5);
          ctx.quadraticCurveTo(64, i * 7.5 - 3.5, 82, i * 7.5);
        }
        ctx.stroke();
        ctx.restore();

        // Hand-drawn Doodle Hearts (♡) next to quote narrative
        if (layout === 'photo-text' || layout === 'text-only') {
          // Pair 1: Upper right of quote block
          const h1X = contentLeft + contentWidth - 42;
          const h1Y = Math.max(cursorY - 80, cardMarginY + (isStory ? 640 : 420));
          this.drawDoodleHeart(ctx, h1X, h1Y, 22, 0.22, 'rgba(244, 114, 182, 0.85)', 'rgba(254, 215, 226, 0.45)');
          this.drawDoodleHeart(ctx, h1X + 20, h1Y + 12, 15, -0.18, 'rgba(244, 114, 182, 0.8)', 'rgba(254, 215, 226, 0.4)');

          // Pair 2: Lower left of quote block
          const h2X = contentLeft + 18;
          const h2Y = cursorY + 18;
          this.drawDoodleHeart(ctx, h2X, h2Y, 17, -0.28, 'rgba(244, 114, 182, 0.8)', 'rgba(254, 215, 226, 0.4)');
          this.drawDoodleHeart(ctx, h2X - 16, h2Y + 14, 12, 0.18, 'rgba(244, 114, 182, 0.75)', 'rgba(254, 215, 226, 0.35)');
        }

      } else if (themeId === 'music') {
        // Mini Music Track Progress Bar, Floating Notes & Now Playing
        // DYNAMIC Y: Starting strictly below text (musicWidgetY = cursorY + 24)
        ctx.save();
        const playerW = Math.min(contentWidth, 680);
        const playerX = contentLeft + (contentWidth - playerW) / 2;
        const musicWidgetY = cursorY + 24;
        const playerY = musicWidgetY;

        // Floating musical notes (♫ ♪ ♬) around track
        ctx.font = '24px sans-serif';
        ctx.fillStyle = 'rgba(192, 132, 252, 0.85)';
        ctx.fillText('♪', playerX - 18, playerY - 16);
        ctx.fillStyle = 'rgba(236, 72, 153, 0.85)';
        ctx.fillText('♫', playerX + playerW * 0.28, playerY - 32);
        ctx.fillStyle = 'rgba(192, 132, 252, 0.75)';
        ctx.fillText('♪', playerX + playerW * 0.72, playerY - 30);
        ctx.fillStyle = 'rgba(236, 72, 153, 0.85)';
        ctx.fillText('♫', playerX + playerW + 10, playerY - 12);
        ctx.fillStyle = 'rgba(192, 132, 252, 0.8)';
        ctx.fillText('♬', playerX - 12, playerY + 88);
        ctx.fillStyle = 'rgba(236, 72, 153, 0.8)';
        ctx.fillText('♫', playerX + playerW + 8, playerY + 84);

        // Timestamps 01:43 / 03:20
        const barY = playerY + 28;
        ctx.font = '600 18px "Plus Jakarta Sans", monospace';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText('01:43', playerX, barY);

        const trackX = playerX + 66;
        const trackW = playerW - 132;
        ctx.fillText('03:20', playerX + playerW - 52, barY);

        // Track Line Background
        ctx.beginPath();
        ctx.moveTo(trackX, barY);
        ctx.lineTo(trackX + trackW, barY);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Active Track Progress (52%)
        const progress = 0.52;
        ctx.beginPath();
        ctx.moveTo(trackX, barY);
        ctx.lineTo(trackX + trackW * progress, barY);
        ctx.strokeStyle = '#c084fc';
        ctx.lineWidth = 4;
        ctx.stroke();

        // Knob Dot
        ctx.beginPath();
        ctx.arc(trackX + trackW * progress, barY, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        // Controls with Mini Soundwave Bars
        const ctrlY = barY + 38;
        ctx.font = '22px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#c084fc';
        ctx.fillText('⏮   ▶   ⏭', playerX + playerW / 2, ctrlY);

        // Waveforms
        const waveY = ctrlY;
        const leftWaveX = playerX + playerW * 0.22;
        const rightWaveX = playerX + playerW * 0.78;
        const barHeights = [10, 18, 6, 22, 14, 8];
        ctx.fillStyle = 'rgba(192, 132, 252, 0.45)';
        for (let i = 0; i < barHeights.length; i++) {
          const h = barHeights[i];
          ctx.fillRect(leftWaveX + i * 8, waveY - h / 2, 4, h);
          ctx.fillRect(rightWaveX - i * 8, waveY - h / 2, 4, h);
        }

        // Now Playing Label
        const nowPlayingY = ctrlY + 48;
        ctx.font = '600 23px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const songName = (entry?.songTitle || entry?.song_title || entry?.title || 'Giai điệu ngày bình yên');
        ctx.fillText(`🎵 Now Playing: ${songName}`, targetWidth / 2, nowPlayingY);

        ctx.restore();

        // Return bottom edge of music widget so downstream metadata is pushed dynamically
        return nowPlayingY + 28;

      } else if (themeId === 'editorial') {
        // Large Translucent Watermark Quote behind content
        ctx.save();
        ctx.font = '900 160px Georgia, serif';
        ctx.fillStyle = 'rgba(15, 23, 42, 0.08)';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('“', targetWidth / 2, Math.max(cardMarginY + 280, cursorY - 40));
        ctx.restore();
      }
    },

    /**
     * Main 2D Canvas Render Routine
     * @param {HTMLCanvasElement} canvas
     * @param {Object} entry
     * @param {Object} options - { ratio: 'square' | 'story', theme: 'sakura' | ... }
     */
    async renderCard(canvas, entry, options = {}) {
      if (!canvas || !entry) return;

      const isStory = options.ratio === 'story';
      const themeId = options.theme || 'sakura';
      const themeCfg = (window.KokoroCardThemes && window.KokoroCardThemes.getTheme(themeId)) || {
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
      };

      const ctx = canvas.getContext('2d');

      // Fixed 1080p Buffer (NO DPR MULTIPLIER to prevent iOS Safari memory crashes)
      const targetWidth = 1080;
      const targetHeight = isStory ? 1920 : 1080;
      canvas.width = targetWidth;
      canvas.height = targetHeight;

      // Draw Ambient Gradient Background
      const bgGrad = ctx.createLinearGradient(0, 0, targetWidth, targetHeight);
      bgGrad.addColorStop(0, themeCfg.bgGrad[0]);
      bgGrad.addColorStop(0.5, themeCfg.bgGrad[1]);
      bgGrad.addColorStop(1, themeCfg.bgGrad[2]);
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, targetWidth, targetHeight);

      // Dot-grid Bullet Journal Texture on Background
      if (themeCfg.hasDotGrid || themeId === 'scrapbook') {
        this.drawDotGrid(ctx, 0, 0, targetWidth, targetHeight, 28, 1, 'rgba(0, 0, 0, 0.04)');
      }

      // Soft Glowing Ambient Orbs
      ctx.save();
      const orb1 = ctx.createRadialGradient(180, 180, 20, 180, 180, 360);
      orb1.addColorStop(0, themeCfg.orb1);
      orb1.addColorStop(1, 'transparent');
      ctx.fillStyle = orb1;
      ctx.fillRect(0, 0, 600, 600);

      const orb2 = ctx.createRadialGradient(targetWidth - 180, targetHeight - 200, 20, targetWidth - 180, targetHeight - 200, 420);
      orb2.addColorStop(0, themeCfg.orb2);
      orb2.addColorStop(1, 'transparent');
      ctx.fillStyle = orb2;
      ctx.fillRect(targetWidth - 600, targetHeight - 650, 600, 650);
      ctx.restore();

      // Draw Center Frosted Glass Card Panel
      const cardMarginX = isStory ? 70 : 64;
      const cardMarginY = isStory ? 80 : 64;
      const cardWidth = targetWidth - cardMarginX * 2;
      const cardHeight = targetHeight - cardMarginY * 2;
      const cardRadius = 44;

      ctx.save();
      ctx.shadowColor = themeCfg.cardShadow || 'rgba(0, 0, 0, 0.12)';
      ctx.shadowBlur = 48;
      ctx.shadowOffsetY = 16;
      this.drawRoundedRect(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, cardRadius);
      ctx.fillStyle = themeCfg.cardBg;
      ctx.fill();
      ctx.restore();

      // Bullet Journal Dot-Grid Texture on Card Panel
      if (themeCfg.hasDotGrid || themeId === 'scrapbook') {
        ctx.save();
        this.drawRoundedRect(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, cardRadius);
        ctx.clip();
        this.drawDotGrid(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, 28, 1, 'rgba(0, 0, 0, 0.06)');
        ctx.restore();
      }

      // Glass Border
      ctx.save();
      this.drawRoundedRect(ctx, cardMarginX, cardMarginY, cardWidth, cardHeight, cardRadius);
      ctx.strokeStyle = themeCfg.cardBorder;
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.restore();

      // Header: Category Pill, Date & Time, Weather Icon
      let cursorY = cardMarginY + 68;
      const paddingInner = 56;
      const contentLeft = cardMarginX + paddingInner;
      const contentWidth = cardWidth - paddingInner * 2;

      // Category Badge
      const catName = entry.categoryName || entry.mood || 'Bình yên';
      const catIcon = entry.categoryIcon || '🌸';
      const catColor = entry.categoryColor || themeCfg.accent;

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

      // Date & Weather
      const dateStr = this.formatCardDate(entry);
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
      ctx.fillStyle = themeCfg.textMuted;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(metaRightText, cardMarginX + cardWidth - paddingInner, cursorY - 9);
      ctx.restore();

      cursorY += 60;

      // Layout Determination: "CÓ GÌ HIỂN THỊ NẤY"
      const hasPhoto = entry.photos && entry.photos.length > 0;
      const hasTitle = Boolean(entry.title && entry.title.trim());
      const hasContent = Boolean(entry.content && entry.content.trim());
      const hasText = hasTitle || hasContent;

      // Photo Selection Mode (v1.8.6):
      // -1: Collage Mode (khi >= 2 ảnh), 0..N: Single selected photo
      const selectedPhotoIndex = (typeof options.selectedPhotoIndex === 'number')
        ? options.selectedPhotoIndex
        : (hasPhoto && entry.photos.length >= 2 ? -1 : 0);
      const isCollage = selectedPhotoIndex === -1 && hasPhoto && entry.photos.length >= 2;

      if (hasPhoto && !hasText) {
        // =========================================================
        // LAYOUT 1: PHOTO-ONLY MODE (Thuần Ảnh — Khung ảnh chiếm diện tích chính)
        // =========================================================
        const footerSpace = isStory ? 200 : 100;
        const photoH = (cardMarginY + cardHeight - footerSpace) - cursorY;
        const photoW = contentWidth;
        const photoX = contentLeft;
        const photoY = cursorY;

        ctx.save();
        ctx.shadowColor = 'rgba(15, 23, 42, 0.08)';
        ctx.shadowBlur = 24;
        ctx.shadowOffsetY = 8;
        this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, 32);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.restore();

        let photoImg = null;
        let photoImages = null;

        if (isCollage) {
          // Adaptive Collage Mode (v1.8.6): 2, 3, or 4 photos
          photoImages = await this.loadMultiplePhotosSafe(entry.photos, 4);
          this.drawCollageFrame(ctx, photoImages, photoX, photoY, photoW, photoH, 14, 28);

          // Overflow badge if > 4 photos
          if (entry.photos.length > 4) {
            const extraCount = `+${entry.photos.length - 4} ảnh`;
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
        } else {
          // Single Selected Photo
          const targetPhoto = (selectedPhotoIndex >= 0 && entry.photos[selectedPhotoIndex]) ? entry.photos[selectedPhotoIndex] : entry.photos[0];
          const photoUrl = window.KokoroAPI ? window.KokoroAPI.resolveMediaUrl(targetPhoto.url || targetPhoto.thumbUrl) : (targetPhoto.url || targetPhoto.thumbUrl);
          photoImg = await this.loadImageSafe(photoUrl) || await this.loadPhotoWithFallback(targetPhoto);

          if (photoImg) {
            this.drawImageCover(ctx, photoImg, photoX, photoY, photoW, photoH, 32);

            ctx.save();
            this.drawRoundedRect(ctx, photoX, photoY, photoW, photoH, 32);
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 14;
            ctx.stroke();
            ctx.restore();
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
        }

        // Studio Theme Decorations
        const decor1Y = this.drawDecorations(ctx, entry, 'photo-only', themeId, isStory, targetWidth, targetHeight, cursorY, [], contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, cardMarginY + cardHeight - 54, { x: photoX, y: photoY, w: photoW, h: photoH });
        if (decor1Y && decor1Y > cursorY) {
          cursorY = decor1Y;
        }

        // Memory Hygiene: Release image references immediately
        photoImg = null;
        photoImages = null;

      } else if (hasPhoto && hasText) {
        // =========================================================
        // LAYOUT 2: PHOTO + TEXT MODE (Tạp Chí Ảnh — Ảnh trên, Chữ dưới)
        // =========================================================
        const contentRaw = (entry.content || '').replace(/^(?:>\s*)+/gm, '').trim();
        const titleRaw = (entry.title || '').replace(/^(?:>\s*)+/gm, '').trim();
        const roughLineCount = (titleRaw ? 1 : 0) + (contentRaw ? contentRaw.split(/\r?\n/).reduce((acc, p) => acc + Math.max(1, Math.ceil(p.length / 40)), 0) : 0);
        const isShortText = roughLineCount <= 4;

        let photoH;
        if (isStory) {
          photoH = isShortText ? Math.min(1020, Math.round(contentWidth * 1.22)) : 760;
        } else {
          if (themeId === 'music') {
            photoH = isShortText ? 330 : 290;
          } else {
            photoH = isShortText ? 460 : 420;
          }
        }

        // Vertical Balancing for Story 9:16
        if (isStory) {
          const estTitleLines = hasTitle ? 1 : 0;
          const estTitleH = estTitleLines * 46 + 14;
          const estContentLines = Math.min(Math.max(1, roughLineCount), 8);
          const estContentH = estContentLines * 48;
          const estMusicWidgetH = themeId === 'music' ? 180 : 0;
          const estMetadataH = 150;
          const totalContentH = photoH + 42 + estTitleH + estContentH + estMusicWidgetH + estMetadataH;
          const availableViewportH = (cardMarginY + cardHeight - 70) - cursorY;
          const freeSpace = availableViewportH - totalContentH;
          if (freeSpace > 60) {
            const verticalOffset = Math.min(160, Math.floor(freeSpace * 0.35));
            cursorY += verticalOffset;
          }
        }

        const photoW = contentWidth;
        const photoX = contentLeft;
        const photoY = cursorY;

        let photoImg = null;
        let photoImages = null;

        if (isCollage) {
          // Adaptive Collage Mode (v1.8.6): 2, 3, or 4 photos
          photoImages = await this.loadMultiplePhotosSafe(entry.photos, 4);
          this.drawCollageFrame(ctx, photoImages, photoX, photoY, photoW, photoH, 14, 20);

          // Overflow badge if > 4 photos
          if (entry.photos.length > 4) {
            const extraCount = `+${entry.photos.length - 4} ảnh`;
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
        } else {
          // Single Selected Photo
          const targetPhoto = (selectedPhotoIndex >= 0 && entry.photos[selectedPhotoIndex]) ? entry.photos[selectedPhotoIndex] : entry.photos[0];
          const photoUrl = window.KokoroAPI ? window.KokoroAPI.resolveMediaUrl(targetPhoto.url || targetPhoto.thumbUrl) : (targetPhoto.url || targetPhoto.thumbUrl);
          photoImg = await this.loadImageSafe(photoUrl) || await this.loadPhotoWithFallback(targetPhoto);

          this.drawPhotoFrame(ctx, entry, photoImg, photoX, photoY, photoW, photoH, 24, isStory, themeId);

          // Multiple Photos Badge
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
        }

        // Memory Hygiene: Release image references immediately
        photoImg = null;
        photoImages = null;

        cursorY += photoH + 42;

        // Title with Formatter
        if (hasTitle) {
          const titleNormalFont = '800 36px "Outfit", "Plus Jakarta Sans", sans-serif';
          const titleBoldFont = '900 36px "Outfit", "Plus Jakarta Sans", sans-serif';
          const titleLineH = 46;
          const titleLines = this.wrapAndFitText(ctx, entry.title, contentWidth, 92, titleLineH, titleNormalFont, titleBoldFont);

          this.drawFormattedLines(ctx, titleLines, contentLeft, cursorY, titleLineH, titleNormalFont, titleBoldFont, themeCfg.textPrimary, 'left');
          cursorY += titleLines.length * titleLineH + 14;
        }

        // Content with Formatter
        if (hasContent) {
          const contentNormalFont = '500 27px "Plus Jakarta Sans", -apple-system, sans-serif';
          const contentBoldFont = '700 27px "Plus Jakarta Sans", -apple-system, sans-serif';
          const contentLineH = 48;

          const footerSpace = isStory ? (themeId === 'music' ? 340 : 240) : (themeId === 'music' ? 320 : 130);
          const availableHeight = (cardMarginY + cardHeight - footerSpace) - cursorY;
          const contentLines = this.wrapAndFitText(ctx, entry.content, contentWidth, availableHeight, contentLineH, contentNormalFont, contentBoldFont);

          if (contentLines.length > 0 && themeId !== 'editorial') {
            ctx.save();
            ctx.font = '800 36px Georgia, serif';
            ctx.fillStyle = 'rgba(244, 114, 182, 0.32)';
            ctx.textBaseline = 'top';
            ctx.fillText('“', contentLeft - 22, cursorY - 6);
            ctx.restore();
          }

          this.drawFormattedLines(ctx, contentLines, contentLeft, cursorY, contentLineH, contentNormalFont, contentBoldFont, themeCfg.textSecondary, 'left');

          const lastLine = contentLines[contentLines.length - 1];
          if (lastLine && !lastLine.isBlank && contentLines.length <= 4 && themeId !== 'editorial') {
            ctx.save();
            ctx.font = '800 36px Georgia, serif';
            ctx.fillStyle = 'rgba(244, 114, 182, 0.32)';
            ctx.textBaseline = 'top';
            const endX = Math.min(contentLeft + lastLine.totalWidth + 6, contentLeft + contentWidth - 20);
            const endY = cursorY + (contentLines.length - 1) * contentLineH - 6;
            ctx.fillText('”', endX, endY);
            ctx.restore();
          }

          cursorY += contentLines.length * contentLineH;
        }

        // Studio Theme Decorations
        const decor2Y = this.drawDecorations(ctx, entry, 'photo-text', themeId, isStory, targetWidth, targetHeight, cursorY, [], contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, cardMarginY + cardHeight - 54, { x: photoX, y: photoY, w: photoW, h: photoH });
        if (decor2Y && decor2Y > cursorY) {
          cursorY = decor2Y;
        }

      } else {
        // =========================================================
        // LAYOUT 3: TEXT-ONLY ZEN QUOTE MODE (Trang Tản Văn — Cỡ chữ lớn, căn chỉnh thanh thoát)
        // =========================================================
        if (isStory) {
          const roughTitleLines = hasTitle ? Math.ceil((entry.title || '').length / 25) : 0;
          const roughContentLines = hasContent ? (entry.content || '').split(/\r?\n/).reduce((acc, p) => acc + Math.max(1, Math.ceil(p.length / 32)), 0) : 0;
          const estTextH = (roughTitleLines * 64) + (roughContentLines * 64) + 260;
          const availableH = (cardMarginY + cardHeight - 260) - cursorY;
          const freeSpace = availableH - estTextH;
          if (freeSpace > 80) {
            cursorY += Math.min(260, Math.floor(freeSpace * 0.40));
          } else {
            cursorY += 80;
          }
        } else {
          cursorY += 30;
        }

        // Zen Quote Decorative Emblem
        ctx.save();
        ctx.font = isStory ? '64px sans-serif' : '52px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(themeId === 'music' ? '🎵' : (themeId === 'scrapbook' ? '💌' : (themeId === 'polaroid' ? '🎞️' : '🌸')), targetWidth / 2, cursorY);
        ctx.restore();

        cursorY += isStory ? 80 : 60;

        // Title with Formatter
        if (hasTitle) {
          const titleNormalFont = isStory ? '800 50px "Outfit", "Plus Jakarta Sans", sans-serif' : '800 42px "Outfit", "Plus Jakarta Sans", sans-serif';
          const titleBoldFont = isStory ? '900 50px "Outfit", "Plus Jakarta Sans", sans-serif' : '900 42px "Outfit", "Plus Jakarta Sans", sans-serif';
          const titleLineH = isStory ? 64 : 54;
          const titleMaxHeight = isStory ? 160 : 120;

          const titleLines = this.wrapAndFitText(ctx, entry.title, contentWidth, titleMaxHeight, titleLineH, titleNormalFont, titleBoldFont);
          this.drawFormattedLines(ctx, titleLines, contentLeft, cursorY, titleLineH, titleNormalFont, titleBoldFont, themeCfg.textPrimary, 'center', contentWidth);
          cursorY += titleLines.length * titleLineH + (isStory ? 36 : 24);
        }

        // Divider Line
        ctx.save();
        const divW = isStory ? 160 : 120;
        ctx.beginPath();
        ctx.moveTo((targetWidth - divW) / 2, cursorY);
        ctx.lineTo((targetWidth + divW) / 2, cursorY);
        ctx.strokeStyle = themeCfg.accent;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();

        cursorY += isStory ? 54 : 36;

        // Content with Formatter
        if (hasContent) {
          const contentNormalFont = isStory ? '500 36px "Plus Jakarta Sans", -apple-system, sans-serif' : '500 31px "Plus Jakarta Sans", -apple-system, sans-serif';
          const contentBoldFont = isStory ? '700 36px "Plus Jakarta Sans", -apple-system, sans-serif' : '700 31px "Plus Jakarta Sans", -apple-system, sans-serif';
          const contentLineH = isStory ? 64 : 54;

          const footerSpace = isStory ? 240 : 130;
          const availableHeight = (cardMarginY + cardHeight - footerSpace) - cursorY;
          const contentLines = this.wrapAndFitText(ctx, entry.content, contentWidth, availableHeight, contentLineH, contentNormalFont, contentBoldFont);

          if (contentLines.length > 0 && themeId !== 'editorial') {
            ctx.save();
            ctx.font = isStory ? '800 68px Georgia, serif' : '800 56px Georgia, serif';
            ctx.fillStyle = 'rgba(244, 114, 182, 0.22)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('“', targetWidth / 2, cursorY - (isStory ? 24 : 18));
            ctx.restore();
          }

          this.drawFormattedLines(ctx, contentLines, contentLeft, cursorY, contentLineH, contentNormalFont, contentBoldFont, themeCfg.textSecondary, 'center', contentWidth);

          if (contentLines.length > 0 && themeId !== 'editorial') {
            ctx.save();
            ctx.font = isStory ? '800 60px Georgia, serif' : '800 48px Georgia, serif';
            ctx.fillStyle = 'rgba(244, 114, 182, 0.22)';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('”', targetWidth / 2, cursorY + contentLines.length * contentLineH + (isStory ? 22 : 16));
            ctx.restore();
          }

          cursorY += contentLines.length * contentLineH;
        }

        // Studio Theme Decorations
        const decor3Y = this.drawDecorations(ctx, entry, 'text-only', themeId, isStory, targetWidth, targetHeight, cursorY, [], contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, cardMarginY + cardHeight - 54);
        if (decor3Y && decor3Y > cursorY) {
          cursorY = decor3Y;
        }
      }

      // Memory Metadata: Location, Weather, Streak Days, and Handwritten Signature
      const footerY = cardMarginY + cardHeight - 54;
      this.drawMemoryMetadata(ctx, entry, themeId, isStory, contentLeft, contentWidth, cardMarginX, cardWidth, cardMarginY, cardHeight, footerY, cursorY);

      // Footer: Tags & Brand Watermark
      const showTags = entry.tags && entry.tags.length > 0 && (isStory || themeId !== 'music');
      if (showTags) {
        ctx.save();
        ctx.font = '600 20px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = themeCfg.accent;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        const tagsText = entry.tags.map((t) => (t.startsWith('#') ? t : `#${t}`)).slice(0, 3).join('  ');
        ctx.fillText(tagsText, contentLeft, footerY);
        ctx.restore();
      }

      // Watermark (Right)
      ctx.save();
      ctx.font = '700 21px "Plus Jakarta Sans", sans-serif';
      ctx.fillStyle = themeCfg.textMuted;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      const brandRight = '🌸 Kokoro (心) Journal';
      ctx.fillText(brandRight, cardMarginX + cardWidth - paddingInner, footerY);
      ctx.restore();
    }
  };

  // Export to global scope
  window.KokoroCardCanvasEngine = Object.freeze(KokoroCardCanvasEngine);

  // CommonJS export for testing
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KokoroCardCanvasEngine };
  }
})();
