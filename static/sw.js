// Kokoro Service Worker v1.8.1 (Tech Debt Sprint: 2026-10-21)
const CACHE_NAME = 'kokoro-v1.8.1';
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/tokens.css?v=1.8.1',
  './css/glass.css?v=1.8.1',
  './css/components.css?v=1.8.1',
  './css/layout.css?v=1.8.1',
  './js/constants.js?v=1.8.1',
  './js/api.js?v=1.8.1',
  './js/auth.js?v=1.8.1',
  './js/toast.js?v=1.8.1',
  './js/datetime-picker.js?v=1.8.1',
  './js/tag-manager.js?v=1.8.1',
  './js/lightbox.js?v=1.8.1',
  './js/zen-prompts.js?v=1.8.1',
  './js/editor.js?v=1.8.1',
  './js/card-themes.js?v=1.8.1',
  './js/card-canvas-engine.js?v=1.8.1',
  './js/card-export.js?v=1.8.1',
  './js/zen-audio.js?v=1.8.1',
  './js/passcode.js?v=1.8.1',
  './js/pwa.js?v=1.8.1',
  './js/timeline-feed.js?v=1.8.1',
  './js/calendar-view.js?v=1.8.1',
  './js/memories-view.js?v=1.8.1',
  './js/profile-stats.js?v=1.8.1',
  './js/app.js?v=1.8.1',
  './audio/rain.mp3',
  './audio/furin.mp3',
  './audio/waves.mp3',
  './audio/stream.mp3',
  './icons/sakura.svg'
];

// Whitelist of allowed external CDN hostnames for runtime offline caching
const ALLOWED_CDN_HOSTS = [
  'fonts.googleapis.com',
  'fonts.gstatic.com',
  'cdn.jsdelivr.net'
];

// Install: Cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: Pure native bypass for /api/, Cache-First for static assets, Network-First for Navigation
self.addEventListener('fetch', (event) => {
  // Only intercept GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  // API calls: Network-First with Cache fallback for GET requests.
  // (Non-GET requests like POST/PUT/DELETE are bypassed at line 70, protecting WebKit multipart uploads)
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResponse;
        })
        .catch(() => {
          return caches.match(event.request).then((cached) => {
            if (cached) return cached;
            return new Response(JSON.stringify({ status: 'error', message: 'Offline mode active', _isOffline: true }), {
              headers: { 'Content-Type': 'application/json' }
            });
          });
        })
    );
    return;
  }

  // HTML navigation: Network-First with cache fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Static assets & CDN resources: Cache-First with Network fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse) {
          return networkResponse;
        }

        const isCdn = ALLOWED_CDN_HOSTS.some((host) => url.hostname === host || url.hostname.endsWith('.' + host));
        const isSameOrigin = url.origin === self.location.origin;

        // Determine if response is cacheable:
        // 1. Same-origin static or thumbnail asset with status 200 OK
        // 2. Allowed CDN assets (Google Fonts, Bootstrap Icons) including CORS (200) or opaque (status 0)
        const isCacheable = (
          (isSameOrigin && networkResponse.status === 200 && (networkResponse.type === 'basic' || url.pathname.includes('/uploads/thumbnails/'))) ||
          (isCdn && (networkResponse.status === 200 || networkResponse.type === 'opaque'))
        );

        if (!isCacheable) {
          return networkResponse;
        }

        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      });
    })
  );
});

