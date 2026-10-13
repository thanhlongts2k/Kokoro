const CACHE_NAME = 'kokoro-v1.6.3';
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/tokens.css?v=1.6.3',
  './css/glass.css?v=1.6.3',
  './css/components.css?v=1.6.3',
  './css/layout.css?v=1.6.3',
  './js/mock-data.js?v=1.6.3',
  './js/api.js?v=1.6.3',
  './js/auth.js?v=1.6.3',
  './js/toast.js?v=1.6.3',
  './js/datetime-picker.js?v=1.6.3',
  './js/tag-manager.js?v=1.6.3',
  './js/lightbox.js?v=1.6.3',
  './js/zen-prompts.js?v=1.6.3',
  './js/editor.js?v=1.6.3',
  './js/card-export.js?v=1.6.3',
  './js/zen-audio.js?v=1.6.3',
  './js/passcode.js?v=1.6.3',
  './js/pwa.js?v=1.6.3',
  './js/app.js?v=1.6.3',
  './audio/rain.mp3',
  './audio/furin.mp3',
  './audio/waves.mp3',
  './audio/stream.mp3',
  './icons/sakura.svg'
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

  // Static assets: Cache-First with Network fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (
          !networkResponse ||
          networkResponse.status !== 200 ||
          networkResponse.type !== 'basic'
        ) {
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
