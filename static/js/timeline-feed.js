/**
 * KOKORO (心) — TIMELINE FEED COMPONENT
 * Handles diary entry rendering, responsive photo mosaic grids, progressive pagination,
 * card actions (lightbox, edit, delete, pin, export), and sidebar/mobile mood filter chips.
 * Complies with AGENTS.md: Modular Layered Architecture & Single Responsibility Principle.
 */

const TimelineFeed = {
  /**
   * Filter entries based on active filters in timelineState
   */
  getFilteredEntries(entries, timelineState, activeDateFilter) {
    if (activeDateFilter) {
      return (entries || []).filter((e) => e.entryDate === activeDateFilter);
    }
    return entries || [];
  },

  /**
   * Render dynamic mood/category filter chips in Desktop Sidebar and Mobile Horizontal Scroll
   */
  renderMoodFilterChips(options) {
    const { sidebarContainer, mobileContainer, categories, totalEntries, timelineState, onSelectMood } = options;
    const isAllActive = (timelineState.mood === 'all' || !timelineState.mood) && !timelineState.categoryId;

    const cats = (categories && categories.length > 0) ? categories : [
      { id: null, name: 'Bình yên', icon: '🌸', color: '#ec4899', usage_count: 0 },
      { id: null, name: 'Ấm áp', icon: '☕', color: '#f59e0b', usage_count: 0 },
      { id: null, name: 'Chiêm nghiệm', icon: '🌙', color: '#8b5cf6', usage_count: 0 },
      { id: null, name: 'Biết ơn', icon: '🍵', color: '#10b981', usage_count: 0 },
      { id: null, name: 'Năng lượng', icon: '⚡', color: '#3b82f6', usage_count: 0 }
    ];

    if (sidebarContainer) {
      let sidebarHtml = `
        <button class="btn-glass ${isAllActive ? 'active' : ''}" data-filter-mood="all" style="justify-content: space-between; width: 100%; border-radius: var(--radius-sm);">
          <span style="display: flex; align-items: center; gap: 8px;"><i class="bi bi-grid"></i> Tất cả bài viết</span>
          <span class="mood-count-badge" data-count-mood="all">${totalEntries}</span>
        </button>
      `;

      cats.forEach((cat) => {
        const isSelected = timelineState.categoryId 
          ? (cat.id === Number(timelineState.categoryId)) 
          : (timelineState.mood === cat.name);
        const safeName = window.escapeHtml(cat.name);
        const safeIcon = window.escapeHtml(cat.icon || '🌸');
        const count = cat.usage_count || 0;
        sidebarHtml += `
          <button class="btn-glass ${isSelected ? 'active' : ''}" 
                  data-filter-mood="${safeName}" 
                  data-category-id="${cat.id || ''}" 
                  style="justify-content: space-between; width: 100%; border-radius: var(--radius-sm);">
            <span style="display: flex; align-items: center; gap: 8px;"><span>${safeIcon}</span> ${safeName}</span>
            <span class="mood-count-badge" data-count-category="${cat.id || ''}">${count}</span>
          </button>
        `;
      });
      sidebarContainer.innerHTML = sidebarHtml;

      sidebarContainer.querySelectorAll('[data-filter-mood]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const mood = e.currentTarget.dataset.filterMood;
          const catId = e.currentTarget.dataset.categoryId ? Number(e.currentTarget.dataset.categoryId) : null;
          if (onSelectMood) onSelectMood(mood, catId);
        });
      });
    }

    if (mobileContainer) {
      let mobileHtml = `
        <button class="btn-glass mood-chip-pill ${isAllActive ? 'active' : ''}" data-filter-mood="all">
          <span class="chip-icon">🌸</span>
          <span class="chip-label">Tất cả</span>
          <span class="mood-count-badge" data-count-mood="all">${totalEntries}</span>
        </button>
      `;

      cats.forEach((cat) => {
        const isSelected = timelineState.categoryId 
          ? (cat.id === Number(timelineState.categoryId)) 
          : (timelineState.mood === cat.name);
        const safeName = window.escapeHtml(cat.name);
        const safeIcon = window.escapeHtml(cat.icon || '🌸');
        const count = cat.usage_count || 0;
        mobileHtml += `
          <button class="btn-glass mood-chip-pill ${isSelected ? 'active' : ''}" 
                  data-filter-mood="${safeName}" 
                  data-category-id="${cat.id || ''}">
            <span class="chip-icon">${safeIcon}</span>
            <span class="chip-label">${safeName}</span>
            <span class="mood-count-badge" data-count-category="${cat.id || ''}">${count}</span>
          </button>
        `;
      });
      mobileContainer.innerHTML = mobileHtml;

      mobileContainer.querySelectorAll('[data-filter-mood]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const mood = e.currentTarget.dataset.filterMood;
          const catId = e.currentTarget.dataset.categoryId ? Number(e.currentTarget.dataset.categoryId) : null;
          if (onSelectMood) onSelectMood(mood, catId);
        });
      });
    }
  },

  /**
   * Build HTML for a single journal card
   */
  buildEntryCardHtml(entry, options = {}) {
    const activeTagFilter = options.activeTagFilter || null;
    const photosCount = entry.photos ? entry.photos.length : 0;
    let photosGridHtml = '';

    if (photosCount > 0) {
      const countAttr = photosCount >= 4 ? 'more' : String(photosCount);
      let itemsHtml = '';

      if (photosCount <= 3) {
        itemsHtml = entry.photos
          .map((p, idx) => {
            const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
            const fullUrl = window.KokoroAPI.resolveMediaUrl(p.url);
            const safeAlt = window.escapeHtml(p.name || 'Photo ' + (idx + 1));
            return `
              <div class="gallery-item" data-full-src="${fullUrl}">
                <img src="${thumbUrl}" alt="${safeAlt}" loading="lazy" onerror="this.onerror=null; this.src='./icons/sakura.svg'; this.classList.add('img-fallback');" />
              </div>
            `;
          })
          .join('');
      } else {
        const displayPhotos = entry.photos.slice(0, 4);
        itemsHtml = displayPhotos
          .map((p, idx) => {
            const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
            const fullUrl = window.KokoroAPI.resolveMediaUrl(p.url);
            const isLast = idx === 3 && photosCount > 4;
            const extraCount = photosCount - 4;
            const safeAlt = window.escapeHtml(p.name || 'Photo ' + (idx + 1));
            return `
              <div class="gallery-item" data-full-src="${fullUrl}">
                <img src="${thumbUrl}" alt="${safeAlt}" loading="lazy" onerror="this.onerror=null; this.src='./icons/sakura.svg'; this.classList.add('img-fallback');" />
                ${isLast ? `<div class="gallery-more-overlay">+${extraCount} ảnh</div>` : ''}
              </div>
            `;
          })
          .join('');
      }

      photosGridHtml = `
        <div class="photo-gallery-grid" data-count="${countAttr}">
          ${itemsHtml}
        </div>
      `;
    }

    const tagsHtml = (entry.tags || [])
      .map(
        (t) => `
        <span class="tag-pill ${activeTagFilter === t ? 'active' : ''}" data-tag="${window.escapeHtml(t)}">${window.escapeHtml(t)}</span>
      `
      )
      .join('');

    const safeTitle = window.escapeHtml(entry.title || '');
    const safeContent = window.escapeHtml(entry.content || '');
    const safeDisplayDate = window.escapeHtml(entry.displayDate || entry.entryDate || '');

    // Category or Mood badge
    let categoryBadgeHtml = '';
    if (entry.categoryName) {
      const safeCatName = window.escapeHtml(entry.categoryName);
      const safeCatIcon = window.escapeHtml(entry.categoryIcon || '🌸');
      const safeCatColor = window.escapeHtml(entry.categoryColor || '#ec4899');
      categoryBadgeHtml = `
        <span class="category-badge-pill" style="--cat-color: ${safeCatColor};">
          <span>${safeCatIcon}</span>
          <span>${safeCatName}</span>
        </span>
      `;
    } else {
      const safeMoodLabel = window.escapeHtml(entry.moodLabel || entry.mood || '🌸 Bình yên');
      categoryBadgeHtml = `<span class="mood-pill mood-${entry.mood}">${safeMoodLabel}</span>`;
    }

    // Weather badge
    const weatherIcons = {
      sunny: '☀️',
      rainy: '🌧️',
      cloudy: '⛅',
      windy: '🍃',
      snowy: '❄️'
    };
    const weatherLabels = {
      sunny: 'Trời nắng',
      rainy: 'Trời mưa',
      cloudy: 'Nhiều mây',
      windy: 'Có gió',
      snowy: 'Có tuyết'
    };
    let weatherBadgeHtml = '';
    if (entry.weather && weatherIcons[entry.weather]) {
      const wIcon = weatherIcons[entry.weather];
      const wLabel = weatherLabels[entry.weather] || entry.weather;
      weatherBadgeHtml = `
        <span class="card-meta-dot">&bull;</span>
        <span class="weather-badge-pill" title="${window.escapeHtml(wLabel)}">
          <span>${wIcon}</span>
        </span>
      `;
    }

    return `
      <article class="glass-panel journal-card glass-card-interactive" id="entry-${entry.id}">
        <div class="card-header entry-card-header">
          <div class="card-meta card-meta-left">
            ${categoryBadgeHtml}
            <span class="card-meta-dot">&bull;</span>
            <span class="card-meta-time entry-date"><i class="bi bi-clock"></i> ${safeDisplayDate}</span>
            ${weatherBadgeHtml}
            ${entry.isPinned ? `<span style="color: var(--sakura-500); margin-left: 4px;" title="Đã ghim"><i class="bi bi-pin-angle-fill"></i></span>` : ''}
          </div>
          <div class="card-actions">
            <button class="action-icon-btn" data-action="export-card" data-id="${entry.id}" title="Xuất thẻ ảnh kỷ niệm ✨">
              <i class="bi bi-card-image"></i>
            </button>
            <button class="action-icon-btn" data-action="pin" data-id="${entry.id}" title="${entry.isPinned ? 'Bỏ ghim' : 'Ghim bài'}">
              <i class="bi ${entry.isPinned ? 'bi-pin-fill text-sakura' : 'bi-pin'}"></i>
            </button>
            <button class="action-icon-btn" data-action="edit" data-id="${entry.id}" title="Chỉnh sửa bài">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="action-icon-btn" data-action="delete" data-id="${entry.id}" title="Xóa bài">
              <i class="bi bi-trash3"></i>
            </button>
          </div>
        </div>

        <h2 class="card-title">${safeTitle}</h2>
        <p class="card-content">${safeContent}</p>

        ${photosGridHtml}

        <div class="card-footer">
          <div class="card-tags-list">
            ${tagsHtml}
          </div>
          <div style="font-size: 12px; color: var(--text-muted);">
            <i class="bi bi-heart text-sakura" style="margin-right: 4px;"></i> Kokoro Journal
          </div>
        </div>
      </article>
    `;
  },

  /**
   * Attach card actions (lightbox, edit, delete, pin, tag filter) to container
   */
  attachCardActions(container, callbacks = {}) {
    if (!container) return;

    // Lightbox for photos
    container.querySelectorAll('.gallery-item').forEach((item) => {
      item.addEventListener('click', () => {
        const fullSrc = item.dataset.fullSrc;
        const img = item.querySelector('img');
        if (window.Lightbox) {
          window.Lightbox.open(fullSrc || (img ? img.src : ''), img ? img.alt : '');
        }
      });
    });

    // Edit action
    container.querySelectorAll('[data-action="edit"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        if (callbacks.onEdit) callbacks.onEdit(id);
      });
    });

    // Delete action
    container.querySelectorAll('[data-action="delete"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        if (callbacks.onDelete) callbacks.onDelete(id);
      });
    });

    // Pin action
    container.querySelectorAll('[data-action="pin"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        if (callbacks.onPin) callbacks.onPin(id);
      });
    });

    // Export Card action
    container.querySelectorAll('[data-action="export-card"]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const id = Number(e.currentTarget.dataset.id);
        if (callbacks.onExportCard) callbacks.onExportCard(id);
      });
    });

    // Tag Pill filter click
    container.querySelectorAll('.tag-pill').forEach((tagBtn) => {
      tagBtn.addEventListener('click', (e) => {
        const tag = e.currentTarget.dataset.tag;
        if (callbacks.onSelectTag) callbacks.onSelectTag(tag);
      });
    });
  },

  /**
   * Render complete timeline list with progressive pagination
   */
  renderTimeline(options) {
    const { feedEl, filteredEntries, isLoading, pagination, callbacks, activeTagFilter } = options;
    if (!feedEl) return;

    if (isLoading) {
      feedEl.innerHTML = `
        <div class="glass-panel text-center" style="padding: 48px 24px;">
          <span class="btn-spinner" style="width: 24px; height: 24px; border-width: 3px; border-color: rgba(244, 114, 182, 0.3); border-top-color: var(--sakura-500);"></span>
          <p style="font-size: 13px; color: var(--text-muted); margin-top: 12px;">Đang tải nhật ký từ máy chủ...</p>
        </div>
      `;
      return;
    }

    if (!filteredEntries || filteredEntries.length === 0) {
      feedEl.innerHTML = `
        <div class="glass-panel text-center" style="padding: 48px 24px;">
          <div style="font-size: 42px; margin-bottom: 12px;">🌸</div>
          <h3 style="font-size: 17px; font-weight: 800; margin: 0 0 6px 0; color: var(--text-primary);">Chưa có nhật ký nào ở chế độ lọc này</h3>
          <p style="font-size: 13px; color: var(--text-muted); margin: 0 0 16px 0;">Hãy bấm nút bên dưới để ghi lại khoảnh khắc đầu tiên nhé!</p>
          <button class="btn-sakura" onclick="window.Editor && window.Editor.open()">+ Ghi nhật ký mới</button>
        </div>
      `;
      return;
    }

    const limit = pagination.visibleLimit;
    const visibleEntries = filteredEntries.slice(0, limit);
    let cardsHtml = visibleEntries.map((entry) => this.buildEntryCardHtml(entry, { activeTagFilter })).join('');

    if (filteredEntries.length > limit) {
      const remainingCount = filteredEntries.length - limit;
      cardsHtml += `
        <div class="timeline-load-more-wrap">
          <button type="button" class="btn-glass timeline-load-more-btn" id="timeline-load-more-btn" aria-label="Xem thêm bài viết cũ hơn">
            <i class="bi bi-feather"></i> Xem thêm bài viết cũ hơn (${remainingCount} bài) 🍃
          </button>
        </div>
      `;
    } else if (filteredEntries.length > pagination.pageSize) {
      cardsHtml += `
        <div class="timeline-end-indicator">
          <span>🌸 Bạn đã xem hết tất cả ${filteredEntries.length} khoảnh khắc 🌸</span>
        </div>
      `;
    }

    feedEl.innerHTML = cardsHtml;
    this.attachCardActions(feedEl, callbacks);

    const loadMoreBtn = feedEl.querySelector('#timeline-load-more-btn');
    if (loadMoreBtn && callbacks.onLoadMore) {
      loadMoreBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        callbacks.onLoadMore();
      });
    }
  },

  /**
   * Append next chunk of entries directly to DOM preserving scroll offset on mobile
   */
  async handleLoadMoreEntries(options) {
    const { feedEl, pagination, callbacks, activeTagFilter, appContext } = options;
    if (!feedEl) return;

    if (appContext && appContext.paginationInfo && appContext.paginationInfo.has_more && window.KokoroAPI) {
      try {
        const nextRes = await window.KokoroAPI.getEntries({
          mood: appContext.timelineState?.mood,
          category_id: appContext.timelineState?.categoryId,
          tag: appContext.timelineState?.tag,
          search: appContext.timelineState?.search,
          offset: (appContext.entries || []).length,
          limit: 15
        });
        const moreItems = nextRes?.entries || nextRes?.data || [];
        if (moreItems.length > 0) {
          appContext.entries = (appContext.entries || []).concat(moreItems);
          appContext.paginationInfo = nextRes.pagination || null;
        }
      } catch (e) {
        console.warn('[TimelineFeed] Không thể tải trang tiếp theo:', e);
      }
    }

    const currentEntries = (appContext && typeof appContext.getFilteredEntries === 'function')
      ? appContext.getFilteredEntries()
      : (options.filteredEntries || []);
    const currentLimit = pagination.visibleLimit;
    const nextLimit = currentLimit + pagination.pageSize;
    const nextChunk = currentEntries.slice(currentLimit, nextLimit);

    if (nextChunk.length === 0) return;

    const existingWrap = feedEl.querySelector('.timeline-load-more-wrap');
    if (existingWrap) {
      existingWrap.remove();
    }

    const fragment = document.createDocumentFragment();
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = nextChunk.map((entry) => this.buildEntryCardHtml(entry, { activeTagFilter })).join('');

    const newCards = Array.from(tempContainer.children);
    newCards.forEach((card) => {
      this.attachCardActions(card, callbacks);
      fragment.appendChild(card);
    });

    feedEl.appendChild(fragment);
    pagination.visibleLimit = nextLimit;

    if (filteredEntries.length > nextLimit) {
      const remainingCount = filteredEntries.length - nextLimit;
      const newWrap = document.createElement('div');
      newWrap.className = 'timeline-load-more-wrap';
      newWrap.innerHTML = `
        <button type="button" class="btn-glass timeline-load-more-btn" id="timeline-load-more-btn" aria-label="Xem thêm bài viết cũ hơn">
          <i class="bi bi-feather"></i> Xem thêm bài viết cũ hơn (${remainingCount} bài) 🍃
        </button>
      `;
      feedEl.appendChild(newWrap);

      const newBtn = newWrap.querySelector('#timeline-load-more-btn');
      if (newBtn && callbacks.onLoadMore) {
        newBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          callbacks.onLoadMore();
        });
      }
    } else {
      const endIndicator = document.createElement('div');
      endIndicator.className = 'timeline-end-indicator';
      endIndicator.innerHTML = `<span>🌸 Bạn đã xem hết tất cả ${filteredEntries.length} khoảnh khắc 🌸</span>`;
      feedEl.appendChild(endIndicator);
    }
  },

  /**
   * Convenience render method for empty states or list updates
   */
  render(entries = []) {
    const feedEl = document.getElementById('timeline-feed');
    if (feedEl) {
      this.renderTimeline({
        feedEl,
        filteredEntries: entries,
        isLoading: false,
        pagination: { visibleLimit: 50 },
        activeTagFilter: null,
        callbacks: {}
      });
    }
  }
};

window.TimelineFeed = TimelineFeed;
window.KokoroTimelineFeed = TimelineFeed;

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TimelineFeed };
}
