/**
 * KOKORO (心) — FULLSCREEN PHOTO LIGHTBOX
 */

const Lightbox = {
  modalEl: null,
  imgEl: null,

  init() {
    this.modalEl = document.getElementById('lightbox-modal');
    this.imgEl = document.getElementById('lightbox-img');

    if (!this.modalEl || !this.imgEl) return;

    // Close when clicking overlay or close button
    this.modalEl.addEventListener('click', (e) => {
      if (e.target.closest('.lightbox-img-wrapper')) return;
      this.close();
    });

    const closeBtn = document.getElementById('lightbox-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    // Close with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modalEl.classList.contains('active')) {
        this.close();
      }
    });
  },

  open(imgSrc, altText = '') {
    if (!this.modalEl || !this.imgEl) return;
    this.imgEl.src = imgSrc;
    this.imgEl.alt = altText;
    this.modalEl.classList.add('active');
    document.body.style.overflow = 'hidden';
  },

  close() {
    if (!this.modalEl) return;
    this.modalEl.classList.remove('active');
    document.body.style.overflow = '';
    setTimeout(() => {
      if (this.imgEl) this.imgEl.src = '';
    }, 250);
  }
};

window.Lightbox = Lightbox;
