/**
 * KOKORO (心) — REST API CLIENT MODULE
 * Designed for dynamic relative URL resolution to seamlessly support
 * local development (port 5050) and Nginx reverse proxy subpaths (e.g. /kokoro/)
 */

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
      if (filters.tag) params.append('tag', filters.tag);
      if (filters.month) params.append('month', filters.month);
      if (filters.search) params.append('search', filters.search);

      const qs = params.toString() ? `?${params.toString()}` : '';
      return await request(`/entries${qs}`, { method: 'GET' });
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
          throw new Error(data.message || data.error || `Lỗi khi lưu bài viết (HTTP ${response.status})`);
        }
        return data;
      } catch (err) {
        console.error(`[KokoroAPI] Error creating entry:`, err);
        throw err;
      }
    },

    // DELETE /api/entries/{id}
    async deleteEntry(id) {
      return await request(`/entries/${id}`, { method: 'DELETE' });
    },

    // PATCH /api/entries/{id}/pin
    async togglePin(id) {
      return await request(`/entries/${id}/pin`, { method: 'PATCH' });
    },

    // GET /api/stats/summary
    async getStats() {
      return await request('/stats/summary', { method: 'GET' });
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
      return new Promise((resolve, reject) => {
        const tx = db.transaction('offline_entries', 'readwrite');
        const store = tx.objectStore('offline_entries');
        const req = store.add({
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

      let syncedCount = 0;
      for (const item of pending) {
        try {
          const formData = new FormData();
          formData.append('title', item.title || 'Khoảnh khắc tĩnh lặng');
          formData.append('content', item.content || '');
          formData.append('mood', item.mood || 'serene');
          formData.append('weather', item.weather || 'sunny');
          formData.append('entry_date', item.entry_date || new Date().toISOString().slice(0, 10));
          formData.append('tags', item.tags || '');

          if (item.photos && item.photos.length > 0) {
            for (const file of item.photos) {
              formData.append('photos', file);
            }
          }

          await this.createEntry(formData);
          await this.deleteOfflineEntry(item.id);
          syncedCount++;
        } catch (err) {
          console.warn(`[KokoroOffline] Lỗi khi đồng bộ bài viết ${item.id}:`, err);
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
      } catch (e) {}
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
    }
  };
})();

window.KokoroAPI = KokoroAPI;
