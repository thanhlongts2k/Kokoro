/**
 * KOKORO (心) — PWA REGISTRATION, AUTO-UPDATE & INSTALLATION HANDLER
 */

let deferredPrompt = null;
let refreshing = false;

const PWA = {
  init() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
    this.setupAutoReloadListener();
  },

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker
          .register('./sw.js')
          .then((registration) => {
            console.log('[Kokoro PWA] Service Worker registered with scope:', registration.scope);

            // 1. Thăm dò kiểm tra bản mới ngay khi vào app
            registration.update();

            // 2. Thăm dò lại mỗi khi người dùng chuyển tab quay lại app
            document.addEventListener('visibilitychange', () => {
              if (document.visibilityState === 'visible') {
                registration.update();
              }
            });

            // 3. Nếu đã có worker đang chờ (waiting), gửi lệnh SKIP_WAITING ngay
            if (registration.waiting) {
              registration.waiting.postMessage({ type: 'SKIP_WAITING' });
            }

            // 4. Khi phát hiện bản mới đang cài đặt, kích hoạt ngay khi cài xong
            registration.addEventListener('updatefound', () => {
              const newWorker = registration.installing;
              if (newWorker) {
                newWorker.addEventListener('statechange', () => {
                  if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    newWorker.postMessage({ type: 'SKIP_WAITING' });
                  }
                });
              }
            });
          })
          .catch((err) => {
            console.warn('[Kokoro PWA] Service Worker registration failed:', err);
          });
      });
    }
  },

  setupAutoReloadListener() {
    if ('serviceWorker' in navigator) {
      // Bắt sự kiện controllerchange để tự reload (có cờ chống loop)
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true;
          console.log('[Kokoro PWA] Controller changed -> Auto-refreshing for newest version ✨');
          window.location.reload();
        }
      });
    }
  },

  setupInstallPrompt() {
    const installBtn = document.getElementById('pwa-install-btn');
    const installMenuItem = document.getElementById('pwa-install-menu-item');
    const pwaMenuDivider = document.getElementById('pwa-menu-divider');

    const triggerPrompt = async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log('[Kokoro PWA] Install prompt outcome:', outcome);
      deferredPrompt = null;
      if (installBtn) installBtn.style.display = 'none';
      if (installMenuItem) installMenuItem.style.display = 'none';
      if (pwaMenuDivider) pwaMenuDivider.style.display = 'none';
    };

    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent browser's default prompt
      e.preventDefault();
      deferredPrompt = e;
      if (installBtn) installBtn.style.display = 'inline-flex';
      if (installMenuItem) installMenuItem.style.display = 'flex';
      if (pwaMenuDivider) pwaMenuDivider.style.display = 'block';

      if (installBtn) installBtn.addEventListener('click', triggerPrompt);
      if (installMenuItem) installMenuItem.addEventListener('click', triggerPrompt);
    });

    window.addEventListener('appinstalled', () => {
      console.log('[Kokoro PWA] App was successfully installed!');
      if (installBtn) installBtn.style.display = 'none';
      if (installMenuItem) installMenuItem.style.display = 'none';
      if (pwaMenuDivider) pwaMenuDivider.style.display = 'none';
    });
  }
};

window.PWA = PWA;
