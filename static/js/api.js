/**
 * Global Body Scroll Lock helper for Modals & Lightbox (SSoT)
 * Prevents body scroll leakage and suppresses native scrollbars
 */
function lockBodyScroll(locked) {
  if (locked) {
    document.body.classList.add('modal-scroll-locked');
    document.documentElement.classList.add('modal-scroll-locked');
  } else {
    // Only remove if no other modal/lightbox remains active
    const hasActive = document.querySelector('.modal-overlay.active, .lightbox-modal.active, #delete-confirm-modal.active, #passcode-lock-overlay.active');
    if (!hasActive) {
      document.body.classList.remove('modal-scroll-locked');
      document.documentElement.classList.remove('modal-scroll-locked');
    }
  }
}
window.lockBodyScroll = lockBodyScroll;

/**
 * Global HTML Entity Sanitizer for XSS Prevention (SSoT)
 * Encodes special characters before inserting into HTML / innerHTML strings.
 */
function escapeHtml(unsafe) {
  if (unsafe === null || unsafe === undefined) return '';
  return String(unsafe)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;


const KokoroAPI = (() => {
  // Dynamically resolve base path regardless of whether app is at root '/' or '/kokoro/'
  const getBasePath = () => {
    let p = window.location.pathname;
    if (p.endsWith('.html')) {
      p = p.substring(0, p.lastIndexOf('/'));
    }
    return p.replace(/\/+$/, '');
  };

  const BASE_PATH = getBasePath();
  const API_BASE = `${BASE_PATH}/api`;

  /**
   * Helper to resolve relative media paths from backend (e.g. "uploads/originals/...")
   */
  const resolveMediaUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
      return url;
    }
    const cleanUrl = url.replace(/^\/+/, '');
    return `${BASE_PATH}/${cleanUrl}`;
  };

  /**
   * Safe response parser that protects against Safari WebKit SyntaxError:
   * "The string did not match the expected pattern" when server returns non-JSON or HTML error.
   */
  const parseResponse = async (response) => {
    const text = await response.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      // If server returned HTML/plain text error page
      const cleanText = text.replace(/<[^>]*>?/gm, '').trim();
      const snippet = cleanText.length > 120 ? cleanText.substring(0, 120) + '...' : cleanText;
      data = { message: snippet || `Lỗi máy chủ (HTTP ${response.status})` };
    }
    return data;
  };

  /**
   * Universal fetch with error handling
   */
  const request = async (endpoint, options = {}) => {
    const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    try {
      const response = await fetch(url, {
        credentials: 'same-origin',
        ...options,
      });
      const data = await parseResponse(response);
      if (!response.ok) {
        throw new Error(data.message || data.error || `Lỗi yêu cầu (HTTP ${response.status})`);
      }
      return data;
    } catch (err) {
      console.error(`[KokoroAPI] Error requesting ${url}:`, err);
      throw err;
    }
  };

  return {
    BASE_PATH,
    API_BASE,
    resolveMediaUrl,

    // GET /api/entries
    async getEntries(filters = {}) {
      const params = new URLSearchParams();
      if (filters.mood && filters.mood !== 'all') params.append('mood', filters.mood);
      if (filters.category_id && filters.category_id !== 'all') params.append('category_id', filters.category_id);
      if (filters.category && filters.category !== 'all') params.append('category_id', filters.category);
      if (filters.tag) params.append('tag', filters.tag);
      if (filters.month) params.append('month', filters.month);
      if (filters.search) params.append('search', filters.search);
      params.append('_t', Date.now()); // Anti-cache timestamp for iOS Safari / WebKit

      const qs = `?${params.toString()}`;
      return await request(`/entries${qs}`, {
        method: 'GET',
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
    },

    // POST /api/entries (multipart/form-data)
    async createEntry(formData) {
      const url = `${API_BASE}/entries`;
      try {
        const response = await fetch(url, {
          method: 'POST',
          credentials: 'same-origin',
          body: formData
        });
        const data = await parseResponse(response);
        if (!response.ok) {
          const err = new Error(data.message || data.error || `Lỗi khi lưu bài viết (HTTP ${response.status})`);
          err.status = response.status;
          throw err;
        }
        return data;
      } catch (err) {
        console.error(`[KokoroAPI] Error creating entry:`, err);
        throw err;
      }
    },

    // PUT /api/entries/{id}
    async updateEntry(id, formData) {
      const url = `${API_BASE}/entries/${id}`;
      try {
        const response = await fetch(url, {
          method: 'PUT',
          body: formData,
          credentials: 'same-origin'
        });
        const data = await parseResponse(response);
        if (!response.ok) {
          const err = new Error(data.message || `Lỗi cập nhật nhật ký (HTTP ${response.status})`);
          err.status = response.status;
          throw err;
        }
        return data;
      } catch (err) {
        console.error(`[KokoroAPI] Error updating entry ${id}:`, err);
        throw err;
      }
    },

    // DELETE /api/entries/{id}
    async deleteEntry(id) {
      return await request(`/entries/${id}`, { method: 'DELETE' });
    },

    // DELETE /api/entries/{id}/photos/{photoId}
    async deleteEntryPhoto(entryId, photoId) {
      return await request(`/entries/${entryId}/photos/${photoId}`, { method: 'DELETE' });
    },

    // PATCH /api/entries/{id}/pin
    async togglePin(id) {
      return await request(`/entries/${id}/pin`, { method: 'PATCH' });
    },

    // GET /api/stats/summary
    async getStats() {
      return await request('/stats/summary', { method: 'GET' });
    },

    // GET /api/categories
    async getCategories() {
      return await request('/categories', { method: 'GET' });
    },

    // POST /api/categories
    async createCategory(data) {
      return await request('/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },

    // PUT /api/categories/:id
    async updateCategory(id, data) {
      return await request(`/categories/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    },

    // DELETE /api/categories/:id
    async deleteCategory(id) {
      return await request(`/categories/${id}`, { method: 'DELETE' });
    },

    // GET /api/tags
    async getTags() {
      return await request('/tags', { method: 'GET' });
    },

    // POST /api/tags
    async createTag(name) {
      return await request('/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
    },

    // PUT /api/tags/:id
    async updateTag(tagId, newName) {
      return await request(`/tags/${tagId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName })
      });
    },

    // DELETE /api/tags/:id
    async deleteTag(tagId) {
      return await request(`/tags/${tagId}`, { method: 'DELETE' });
    },

    // DELETE /api/tags/cleanup-orphans
    async cleanupOrphanTags() {
      return await request('/tags/cleanup-orphans', { method: 'DELETE' });
    },

    // GET /api/entries/export (JSON attachment download)
    async exportEntries() {
      const url = `${API_BASE}/entries/export`;
      try {
        const response = await fetch(url, { credentials: 'same-origin' });
        if (!response.ok) {
          const data = await parseResponse(response);
          throw new Error(data.message || `Lỗi tải bản sao lưu (HTTP ${response.status})`);
        }
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        a.download = `kokoro_backup_${today}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        return true;
      } catch (err) {
        console.error('[KokoroAPI] Error exporting entries:', err);
        throw err;
      }
    },

    // POST /api/entries/import (Upload JSON backup file)
    async importEntries(file) {
      const formData = new FormData();
      formData.append('backup_file', file);
      return await request('/entries/import', {
        method: 'POST',
        body: formData
      });
    },

    // -----------------------------------------------------------------------
    // OFFLINE STORAGE & INDEXEDDB QUEUE (SAFE FOR LARGE BLOBS/FILES)
    // -----------------------------------------------------------------------
    async openOfflineDB() {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open('kokoro_offline_db', 1);
        request.onupgradeneeded = (e) => {
          const db = e.target.result;
          if (!db.objectStoreNames.contains('offline_entries')) {
            db.createObjectStore('offline_entries', { keyPath: 'id', autoIncrement: true });
          }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    },

    async saveOfflineEntry(entryData) {
      const db = await this.openOfflineDB();
      const currentUserId = entryData.user_id || (window.KokoroAuth && window.KokoroAuth.currentUser ? window.KokoroAuth.currentUser.id : null);
      return new Promise((resolve, reject) => {
        const tx = db.transaction('offline_entries', 'readwrite');
        const store = tx.objectStore('offline_entries');
        const hasValidCategory = entryData.category_id !== undefined && 
                                  entryData.category_id !== null && 
                                  entryData.category_id !== '' && 
                                  entryData.category_id !== 'null';
        const req = store.add({
          user_id: currentUserId,
          category_id: hasValidCategory ? Number(entryData.category_id) : null,
          title: entryData.title,
          content: entryData.content,
          mood: entryData.mood,
          weather: entryData.weather || 'sunny',
          entry_date: entryData.entry_date,
          tags: entryData.tags,
          photos: entryData.photos || [], // Array of File/Blob objects
          createdAt: new Date().toISOString()
        });
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
    },

    async getOfflineEntries() {
      const db = await this.openOfflineDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction('offline_entries', 'readonly');
        const store = tx.objectStore('offline_entries');
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error);
      });
    },

    async deleteOfflineEntry(id) {
      const db = await this.openOfflineDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction('offline_entries', 'readwrite');
        const store = tx.objectStore('offline_entries');
        const req = store.delete(id);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
    },

    async syncOfflineQueue() {
      const pending = await this.getOfflineEntries();
      if (!pending || pending.length === 0) return 0;

      const currentUserId = window.KokoroAuth && window.KokoroAuth.currentUser ? window.KokoroAuth.currentUser.id : null;
      // Multi-account data isolation: only sync entries belonging to current user
      const userPending = pending.filter(item => !item.user_id || item.user_id === currentUserId);
      if (userPending.length === 0) return 0;

      let syncedCount = 0;
      for (const item of userPending) {
        try {
          const formData = new FormData();
          formData.append('title', item.title || 'Khoảnh khắc tĩnh lặng');
          formData.append('content', item.content || '');
          formData.append('mood', item.mood || 'serene');
          formData.append('weather', item.weather || 'sunny');
          formData.append('entry_date', item.entry_date || new Date().toISOString().slice(0, 10));
          formData.append('tags', item.tags || '');

          // Data integrity: Only append category_id when it is genuinely a valid non-null value
          if (item.category_id !== undefined && 
              item.category_id !== null && 
              item.category_id !== '' && 
              item.category_id !== 'null') {
            formData.append('category_id', String(item.category_id));
          }

          if (item.photos && item.photos.length > 0) {
            for (const file of item.photos) {
              if (file && (file instanceof Blob || (typeof file === 'object' && file.name))) {
                formData.append('photos', file);
              }
            }
          }

          // If item has neither content nor valid photos, immediately drop it
          const validPhotos = formData.getAll('photos');
          if (!item.content && validPhotos.length === 0) {
            console.warn(`[KokoroOffline] Bản ghi ngoại tuyến ${item.id} không có dữ liệu hợp lệ, tự động dọn dẹp khỏi IndexedDB.`);
            await this.deleteOfflineEntry(item.id);
            continue;
          }

          await this.createEntry(formData);
          await this.deleteOfflineEntry(item.id);
          syncedCount++;
        } catch (err) {
          console.warn(`[KokoroOffline] Lỗi khi đồng bộ bài viết ${item.id}:`, err);
          const status = err ? err.status : null;

          // CRITICAL FIX (DEBT-01): If server returned 401/403 (Unauthorized / Session expired),
          // DO NOT delete the offline entry! Halt syncing immediately to preserve user's data
          // and wait for user to re-authenticate.
          if (status === 401 || status === 403 || (err.message && (err.message.includes('401') || err.message.includes('đăng nhập')))) {
            console.warn(`[KokoroOffline] Phiên đăng nhập hết hạn (HTTP ${status || 401}). Tạm dừng đồng bộ để bảo vệ bài viết trong IndexedDB.`);
            break; // Halt syncing remaining items to prevent redundant failed requests
          }

          // Only permanently delete item if it is genuinely an unrecoverable client error (400 Bad Request or 422)
          const isUnrecoverableClientError = (status === 400 || status === 422) ||
                                            (err.message && (err.message.includes('400') || err.message.includes('422') || err.message.includes('nhập nội dung')));
          if (isUnrecoverableClientError) {
            console.warn(`[KokoroOffline] Xóa bản ghi lỗi dữ liệu không thể phục hồi ${item.id} khỏi IndexedDB để chấm dứt vòng lặp lỗi.`);
            try {
              await this.deleteOfflineEntry(item.id);
            } catch (delErr) {
              console.error('[KokoroOffline] Không thể xóa bản ghi lỗi:', delErr);
            }
          }
        }
      }
      return syncedCount;
    },

    // -----------------------------------------------------------------------
    // LOCALSTORAGE DRAFT MANAGEMENT
    // -----------------------------------------------------------------------
    saveDraft(userId, draft) {
      try {
        const key = `kokoro_draft_${userId || 'guest'}`;
        localStorage.setItem(key, JSON.stringify({
          ...draft,
          savedAt: new Date().toISOString()
        }));
      } catch (e) {
        console.warn('[KokoroAPI] Lỗi lưu bản nháp vào localStorage:', e);
      }
    },

    getDraft(userId) {
      try {
        const key = `kokoro_draft_${userId || 'guest'}`;
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },

    clearDraft(userId) {
      try {
        const key = `kokoro_draft_${userId || 'guest'}`;
        localStorage.removeItem(key);
      } catch (e) {
        console.warn('[KokoroAPI] Failed to clear draft from localStorage:', e);
      }
    },

    // -----------------------------------------------------------------------
    // AUTHENTICATION API
    // -----------------------------------------------------------------------

    // GET /api/auth/config
    async getAuthConfig() {
      return await request('/auth/config', { method: 'GET' });
    },

    // GET /api/auth/me
    async getCurrentUser() {
      return await request('/auth/me', { method: 'GET' });
    },

    // GET /api/auth/mock-users
    async getMockUsers() {
      return await request('/auth/mock-users', { method: 'GET' });
    },

    // POST /api/auth/mock-login
    async mockLogin(userId) {
      return await request('/auth/mock-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
    },

    // POST /api/auth/google
    async googleLogin(credential) {
      return await request('/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential })
      });
    },

    // POST /api/auth/logout
    async logout() {
      return await request('/auth/logout', { method: 'POST' });
    },

    // HTML Sanitizer
    escapeHtml
  };
})();

KokoroAPI.escapeHtml = escapeHtml;
window.KokoroAPI = KokoroAPI;
