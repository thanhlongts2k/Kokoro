const CACHE_NAME = 'kokoro-v1.3.0';
const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/tokens.css?v=1.3.0',
  './css/glass.css?v=1.3.0',
  './css/layout.css?v=1.3.0',
  './js/mock-data.js?v=1.3.0',
  './js/api.js?v=1.3.0',
  './js/auth.js?v=1.3.0',
  './js/app.js?v=1.3.0',
  './js/editor.js?v=1.3.0',
  './js/lightbox.js?v=1.3.0',
  './js/pwa.js?v=1.3.0',
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

// Fetch: Cache-First for static assets, Network-First for APIs & Navigation
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls: Network-First
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ error: 'Offline mode active' }), {
          headers: { 'Content-Type': 'application/json' }
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
