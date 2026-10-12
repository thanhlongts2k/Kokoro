/**
 * KOKORO (心) — TOAST NOTIFICATION MODULE
 * Architecture: Standalone UI Utility, decoupled from app coordinator.
 * Features: Soft Sakura styling, deduplication, max 2 active toasts, auto-dismiss.
 */

const KokoroToast = (() => {
  const getContainer = () => document.getElementById('toast-container');

  /**
   * Display a Soft Sakura pastel toast notification.
   * @param {string} message - Message to display
   * @param {'success'|'error'|'warning'|'info'} type - Toast type
   */
  const show = (message, type = 'success') => {
    const container = getContainer();
    if (!container || !message) return;

    const trimmedMsg = String(message).trim();

    // 1. Deduplication: Check if identical message already exists in container
    const existingToasts = Array.from(container.querySelectorAll('.toast-item'));
    for (const existing of existingToasts) {
      if (existing.dataset.toastMessage === trimmedMsg) {
        // Reset timer on existing toast without creating duplicate element
        if (existing._dismissTimer) clearTimeout(existing._dismissTimer);
        existing.classList.remove('hide');
        existing._dismissTimer = setTimeout(() => {
          existing.classList.add('hide');
          setTimeout(() => {
            if (existing.parentNode) existing.parentNode.removeChild(existing);
          }, 350);
        }, 3200);
        return;
      }
    }

    // 2. Limit maximum active toasts to 2: Evict oldest if count >= 2
    if (existingToasts.length >= 2) {
      const oldest = existingToasts[0];
      if (oldest._dismissTimer) clearTimeout(oldest._dismissTimer);
      if (oldest.parentNode) oldest.parentNode.removeChild(oldest);
    }

    // 3. Create new Toast element
    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.dataset.toastMessage = trimmedMsg;

    let icon = '🌸';
    if (type === 'error') icon = '⚠️';
    if (type === 'success') icon = '✨';
    if (type === 'warning') icon = '🍃';
    if (type === 'info') icon = '🌸';

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span>${trimmedMsg}</span>
    `;

    container.appendChild(toast);

    // Auto dismiss after 3.2s
    toast._dismissTimer = setTimeout(() => {
      toast.classList.add('hide');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 350);
    }, 3200);
  };

  const success = (msg) => show(msg, 'success');
  const error = (msg) => show(msg, 'error');
  const warning = (msg) => show(msg, 'warning');
  const info = (msg) => show(msg, 'info');

  return {
    show,
    success,
    error,
    warning,
    info
  };
})();

window.KokoroToast = KokoroToast;
