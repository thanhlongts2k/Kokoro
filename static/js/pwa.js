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
          })
          .catch((err) => {
            console.warn('[Kokoro PWA] Service Worker registration failed:', err);
          });
      });
    }
  },

  setupInstallPrompt() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (!installBtn) return;

    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent browser's default prompt
      e.preventDefault();
      deferredPrompt = e;
      installBtn.style.display = 'inline-flex';

      installBtn.addEventListener('click', async () => {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log('[Kokoro PWA] Install prompt outcome:', outcome);
        deferredPrompt = null;
        installBtn.style.display = 'none';
      });
    });

    window.addEventListener('appinstalled', () => {
      console.log('[Kokoro PWA] App was successfully installed!');
      if (installBtn) installBtn.style.display = 'none';
    });
  }
};

window.PWA = PWA;
