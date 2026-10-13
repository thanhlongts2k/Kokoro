const CACHE_NAME = 'kokoro-v1.7.0';
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/tokens.css?v=1.7.0',
  './css/glass.css?v=1.7.0',
  './css/components.css?v=1.7.0',
  './css/layout.css?v=1.7.0',
  './js/constants.js?v=1.7.0',
  './js/api.js?v=1.7.0',
  './js/auth.js?v=1.7.0',
  './js/toast.js?v=1.7.0',
  './js/datetime-picker.js?v=1.7.0',
  './js/tag-manager.js?v=1.7.0',
  './js/lightbox.js?v=1.7.0',
  './js/zen-prompts.js?v=1.7.0',
  './js/editor.js?v=1.7.0',
  './js/card-export.js?v=1.7.0',
  './js/zen-audio.js?v=1.7.0',
  './js/passcode.js?v=1.7.0',
  './js/pwa.js?v=1.7.0',
  './js/timeline-feed.js?v=1.7.0',
  './js/calendar-view.js?v=1.7.0',
  './js/memories-view.js?v=1.7.0',
  './js/profile-stats.js?v=1.7.0',
  './js/app.js?v=1.7.0',
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

  // API calls: Pure native bypass. Never intercept or proxy /api/ through SW
  // to prevent WebKit/Safari multipart form-data body stripping.
  if (url.pathname.includes('/api/')) {
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

