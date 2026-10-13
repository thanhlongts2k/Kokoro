/**
 * KOKORO (心) — MEMORIES VIEW COMPONENT
 * Handles photo memories gallery, hashtag pills, mood filtering, and Lightbox integration.
 * Complies with AGENTS.md: Modular Layered Architecture & Single Responsibility Principle.
 */

const MemoriesView = {
  /**
   * Render dynamic mood/category filter chips in Memories View
   */
  renderMemoriesMoodFilterChips(options) {
    const { container, categories, memoriesState, onSelectMood } = options;
    if (!container) return;

    const isAllActive = (memoriesState.mood === 'all' || !memoriesState.mood) && !memoriesState.categoryId;

    const cats = (categories && categories.length > 0) ? categories : [
      { id: null, name: 'Bình yên', icon: '🌸', color: '#ec4899' },
      { id: null, name: 'Ấm áp', icon: '☕', color: '#f59e0b' },
      { id: null, name: 'Chiêm nghiệm', icon: '🌙', color: '#8b5cf6' },
      { id: null, name: 'Biết ơn', icon: '🍵', color: '#10b981' },
      { id: null, name: 'Năng lượng', icon: '⚡', color: '#3b82f6' }
    ];

    let html = `
      <button class="btn-glass memory-mood-pill ${isAllActive ? 'active' : ''}" data-memories-mood="all">
        <span class="chip-icon">🌸</span>
        <span class="chip-label">Tất cả cảm xúc</span>
        <span class="memories-mood-count" data-memories-count-mood="all">0</span>
      </button>
    `;

    cats.forEach((cat) => {
      const isSelected = memoriesState.categoryId 
        ? (cat.id === Number(memoriesState.categoryId)) 
        : (memoriesState.mood === cat.name);
      const safeName = window.escapeHtml(cat.name);
      const safeIcon = window.escapeHtml(cat.icon || '🌸');
      html += `
        <button class="btn-glass memory-mood-pill ${isSelected ? 'active' : ''}" 
                data-memories-mood="${safeName}" 
                data-memories-cat-id="${cat.id || ''}">
          <span class="chip-icon">${safeIcon}</span>
          <span class="chip-label">${safeName}</span>
          <span class="memories-mood-count" data-memories-count-cat="${cat.id || ''}">0</span>
        </button>
      `;
    });

    container.innerHTML = html;

    container.querySelectorAll('[data-memories-mood]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const mood = e.currentTarget.dataset.memoriesMood;
        const catId = e.currentTarget.dataset.memoriesCatId ? Number(e.currentTarget.dataset.memoriesCatId) : null;
        if (onSelectMood) onSelectMood(mood, catId);
      });
    });
  },

  /**
   * Synchronize photo counts on Memories Mood Badges
   */
  updateMemoriesMoodBadges(entries, memoriesState) {
    const entriesWithPhotos = (entries || []).filter((e) => e.photos && e.photos.length > 0);
    const catPhotoCounts = {};
    const moodPhotoCounts = {};
    let totalPhotos = 0;

    entriesWithPhotos.forEach((e) => {
      const pCount = e.photos.length;
      totalPhotos += pCount;

      const catId = e.categoryId || e.category_id;
      if (catId) {
        catPhotoCounts[catId] = (catPhotoCounts[catId] || 0) + pCount;
      }
      if (e.mood) {
        moodPhotoCounts[e.mood] = (moodPhotoCounts[e.mood] || 0) + pCount;
      }
    });

    const badges = document.querySelectorAll('[data-memories-count-mood], [data-memories-count-cat]');
    badges.forEach((b) => {
      if (b.dataset.memoriesCountMood) {
        const m = b.dataset.memoriesCountMood;
        b.textContent = m === 'all' ? totalPhotos : (moodPhotoCounts[m] || 0);
      } else if (b.dataset.memoriesCountCat) {
        const cId = Number(b.dataset.memoriesCountCat);
        b.textContent = catPhotoCounts[cId] || 0;
      }
    });
  },

  /**
   * Render Memories Photo Gallery Grid with Mood & Hashtag Filters
   */
  renderMemoriesGallery(options) {
    const { gridEl, badgeEl, tagScrollEl, entries, memoriesState, activeMemoriesMood, onSelectTag, onPhotoClick } = options;
    if (!gridEl) return;

    const sourceEntries = entries || [];
    const entriesWithPhotos = sourceEntries.filter((e) => e.photos && e.photos.length > 0);

    // 1. Extract and render dynamic hashtags
    const tagCounts = {};
    entriesWithPhotos.forEach((e) => {
      if (e.tags && Array.isArray(e.tags)) {
        e.tags.forEach((t) => {
          const cleanTag = t.trim().toLowerCase();
          if (cleanTag) {
            tagCounts[cleanTag] = (tagCounts[cleanTag] || 0) + 1;
          }
        });
      }
    });

    if (tagScrollEl) {
      const tagList = Object.keys(tagCounts);
      if (tagList.length === 0) {
        tagScrollEl.innerHTML = '';
        tagScrollEl.style.display = 'none';
      } else {
        tagScrollEl.style.display = 'flex';
        tagScrollEl.innerHTML = tagList.map((tag) => {
          const isSelected = memoriesState.tag === tag;
          const cleanTagName = tag.replace(/^#+/, '');
          const safeTag = window.escapeHtml(cleanTagName);
          return `
            <button type="button" class="memory-tag-chip ${isSelected ? 'active' : ''}" data-memories-tag="${window.escapeHtml(tag)}">
              <span>#${safeTag}</span>
              <span style="opacity: 0.7; font-size: 11px;">(${tagCounts[tag]})</span>
            </button>
          `;
        }).join('');

        tagScrollEl.querySelectorAll('.memory-tag-chip').forEach((btn) => {
          btn.addEventListener('click', (e) => {
            const clickedTag = e.currentTarget.dataset.memoriesTag;
            if (onSelectTag) onSelectTag(clickedTag);
          });
        });
      }
    }

    // 2. Collect photos filtered by hashtag
    const allPhotos = [];
    entriesWithPhotos.forEach((e) => {
      if (memoriesState.tag) {
        const hasTag = e.tags && Array.isArray(e.tags) && e.tags.some((t) => t.trim().toLowerCase() === memoriesState.tag);
        if (!hasTag) return;
      }
      e.photos.forEach((p) => {
        allPhotos.push({
          ...p,
          entryId: e.id,
          entryTitle: e.title,
          entryDate: e.entryDate,
          displayDate: e.displayDate || e.entryDate,
          mood: e.mood,
          moodLabel: e.moodLabel || e.mood,
          categoryId: e.categoryId || e.category_id,
          categoryName: e.categoryName || e.category_name,
          categoryIcon: e.categoryIcon || e.category_icon
        });
      });
    });

    // 3. Filter by active memories mood / category
    let filteredPhotos = allPhotos;
    const activeCatId = memoriesState.categoryId;
    const activeMood = memoriesState.mood || activeMemoriesMood;
    if (activeCatId) {
      filteredPhotos = allPhotos.filter((p) => p.categoryId === Number(activeCatId));
    } else if (activeMood && activeMood !== 'all') {
      filteredPhotos = allPhotos.filter((p) => p.mood === activeMood || (p.categoryName && p.categoryName.toLowerCase() === activeMood.toLowerCase()));
    }

    if (badgeEl) {
      badgeEl.textContent = `📸 ${filteredPhotos.length} ảnh`;
    }

    this.updateMemoriesMoodBadges(entries, memoriesState);

    // 4. Render photo grid or empty state
    if (filteredPhotos.length === 0) {
      const cleanEmptyTag = memoriesState.tag ? memoriesState.tag.replace(/^#+/, '') : '';
      const safeEmptyTag = cleanEmptyTag ? window.escapeHtml(cleanEmptyTag) : '';
      gridEl.innerHTML = `
        <div class="glass-panel" style="padding: 44px 20px; text-align: center; grid-column: 1 / -1; border-radius: var(--radius-lg);">
          <div style="font-size: 38px; margin-bottom: 8px;">📷</div>
          <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Chưa có hình ảnh kỷ niệm phù hợp</div>
          <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 18px;">
            ${memoriesState.tag ? `Không tìm thấy hình ảnh nào với thẻ #${safeEmptyTag}.` : 'Hãy đính kèm hình ảnh vào các bài viết nhật ký để lưu giữ kỷ niệm tại đây nhé! 🌸'}
          </div>
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
        const safeTitle = window.escapeHtml(p.entryTitle || '');
        const safeDisplayTitle = safeTitle || 'Khoảnh khắc';
        const safeDate = window.escapeHtml(p.displayDate || '');
        const safeCat = p.categoryName ? `${p.categoryIcon || '🌸'} ${p.categoryName}` : (p.moodLabel || '');
        const safeMeta = window.escapeHtml(safeCat);
        const safeAlt = window.escapeHtml(p.name || 'Memory Photo');
        return `
          <div class="c-memory-item" data-full-src="${fullUrl}" data-title="${safeTitle}" data-date="${safeDate}">
            <img src="${thumbUrl}" alt="${safeAlt}" loading="lazy" onerror="this.onerror=null; this.src='./icons/sakura.svg'; this.classList.add('img-fallback');" />
            <div class="c-memory-overlay">
              <span class="c-memory-title">${safeDisplayTitle}</span>
              <span class="c-memory-meta"><i class="bi bi-clock"></i> ${safeDate} &bull; ${safeMeta}</span>
            </div>
          </div>
        `;
      })
      .join('');

    // Attach click listener for Lightbox
    gridEl.querySelectorAll('.c-memory-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        const fullSrc = e.currentTarget.dataset.fullSrc;
        const title = e.currentTarget.dataset.title;
        const date = e.currentTarget.dataset.date;
        if (onPhotoClick) {
          onPhotoClick(fullSrc, `${title} (${date})`);
        } else if (window.Lightbox) {
          window.Lightbox.open(fullSrc, `${title} (${date})`);
        }
      });
    });
  }
};

window.MemoriesView = MemoriesView;

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MemoriesView };
}
