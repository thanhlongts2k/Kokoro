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
   * Universal fetch with error handling
   */
  const request = async (endpoint, options = {}) => {
    const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || `Lỗi yêu cầu (HTTP ${response.status})`);
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
          body: formData
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.message || `Lỗi khi lưu bài viết (HTTP ${response.status})`);
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

    // GET /api/auth/me
    async getCurrentUser() {
      return await request('/auth/me', { method: 'GET' });
    }
  };
})();

window.KokoroAPI = KokoroAPI;
