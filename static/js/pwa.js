/**
 * KOKORO (心) — PWA REGISTRATION & INSTALLATION HANDLER
 */

let deferredPrompt = null;

const PWA = {
  init() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
  },

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker
          .register('./sw.js')
          .then((reg) => {
            console.log('[Kokoro PWA] Service Worker registered with scope:', reg.scope);
            // Proactively check for Service Worker updates on page load
            reg.update();
          })
          .catch((err) => {
            console.warn('[Kokoro PWA] Service Worker registration failed:', err);
          });
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
