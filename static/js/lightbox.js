/**
 * KOKORO (心) — ADVANCED INTERACTIVE PHOTO LIGHTBOX
 * Features:
 * - GPU-accelerated Smooth Zoom & Pan (translate3d + scale)
 * - Mobile Touch: Double-Tap to 2x/1x, Pinch-to-Zoom (1x - 3.5x), Pan on zoom, Swipe down/up to dismiss
 * - Touch-Action & Passive: false integration for zero gesture hijacking
 * - Desktop: Wheel Zoom around cursor, Mouse Drag Pan with grab/grabbing cursor
 * - Toolbar: Zoom In (+), Zoom Out (-), Reset (1x), Close (Esc)
 * - Strict Body Scroll Lock integration (SSoT)
 */

const Lightbox = {
  modalEl: null,
  imgWrapperEl: null,
  imgEl: null,
  captionEl: null,
  controlsBarEl: null,

  // Transform State
  scale: 1.0,
  minScale: 1.0,
  maxScale: 3.5,
  translateX: 0,
  translateY: 0,

  // Interaction State
  initialized: false,
  isDragging: false,
  dragStartX: 0,
  dragStartY: 0,
  lastTapTime: 0,
  initialPinchDist: 0,
  initialPinchScale: 1.0,
  touchStartX: 0,
  touchStartY: 0,
  isSwipingDismiss: false,

  init() {
    if (this.initialized) return;
    this.modalEl = document.getElementById('lightbox-modal');
    this.imgWrapperEl = document.getElementById('lightbox-img-wrapper');
    this.imgEl = document.getElementById('lightbox-img');
    this.captionEl = document.getElementById('lightbox-caption');
    this.controlsBarEl = document.getElementById('lightbox-controls-bar');

    if (!this.modalEl || !this.imgEl) return;
    this.initialized = true;

    this.bindToolbarButtons();
    this.bindMouseEvents();
    this.bindTouchEvents();
    this.bindKeyboardAndOverlay();
  },

  bindToolbarButtons() {
    const zoomInBtn = document.getElementById('lightbox-zoom-in-btn');
    const zoomOutBtn = document.getElementById('lightbox-zoom-out-btn');
    const resetBtn = document.getElementById('lightbox-reset-btn');
    const closeBtn = document.getElementById('lightbox-close-btn');

    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.zoomBy(0.5);
      });
    }

    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.zoomBy(-0.5);
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.resetZoom(true);
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.close();
      });
    }
  },

  bindKeyboardAndOverlay() {
    // Click outside image to close (only when not zoomed or dragging)
    this.modalEl.addEventListener('click', (e) => {
      if (e.target.closest('#lightbox-controls-bar') || e.target.closest('#lightbox-img')) return;
      if (this.scale <= 1) {
        this.close();
      } else {
        this.resetZoom(true);
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (!this.modalEl || !this.modalEl.classList.contains('active')) return;

      if (e.key === 'Escape') {
        this.close();
      } else if (e.key === '+' || e.key === '=') {
        this.zoomBy(0.5);
      } else if (e.key === '-' || e.key === '_') {
        this.zoomBy(-0.5);
      } else if (e.key === '0' || e.key === 'r' || e.key === 'R') {
        this.resetZoom(true);
      }
    });
  },

  // --------------------------------------------------------------------------
  // DESKTOP INTERACTION (MOUSE DRAG & WHEEL ZOOM)
  // --------------------------------------------------------------------------
  bindMouseEvents() {
    if (!this.imgEl) return;

    // Wheel Zoom centered at mouse position
    this.modalEl.addEventListener('wheel', (e) => {
      if (!this.modalEl.classList.contains('active')) return;
      e.preventDefault();

      const delta = e.deltaY < 0 ? 0.3 : -0.3;
      this.zoomBy(delta, e.clientX, e.clientY);
    }, { passive: false });

    // Mouse Drag (Pan) when zoomed
    this.imgEl.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return; // Left click only
      if (this.scale <= 1) return;

      e.preventDefault();
      this.isDragging = true;
      this.dragStartX = e.clientX - this.translateX;
      this.dragStartY = e.clientY - this.translateY;
      this.imgEl.classList.add('is-dragging');
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      e.preventDefault();

      this.translateX = e.clientX - this.dragStartX;
      this.translateY = e.clientY - this.dragStartY;
      this.applyTransform(false);
    });

    const finishMouseDrag = () => {
      if (this.isDragging) {
        this.isDragging = false;
        if (this.imgEl) this.imgEl.classList.remove('is-dragging');
        this.constrainBounds();
        this.applyTransform(true);
      }
    };

    window.addEventListener('mouseup', finishMouseDrag);
    window.addEventListener('mouseleave', finishMouseDrag);
  },

  // --------------------------------------------------------------------------
  // MOBILE INTERACTION (DOUBLE-TAP, PINCH-TO-ZOOM, PAN, SWIPE TO DISMISS)
  // --------------------------------------------------------------------------
  bindTouchEvents() {
    if (!this.imgEl || !this.modalEl) return;

    const handleTouchStart = (e) => {
      if (e.target.closest('#lightbox-controls-bar')) return;

      if (e.touches.length === 1) {
        const touch = e.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;

        // Double-Tap Detection (< 300ms)
        const now = Date.now();
        const timeDiff = now - this.lastTapTime;
        if (timeDiff > 0 && timeDiff < 320) {
          e.preventDefault();
          this.lastTapTime = 0;
          if (this.scale > 1.05) {
            this.resetZoom(true);
          } else {
            this.zoomTo(2.0, touch.clientX, touch.clientY);
          }
          return;
        }
        this.lastTapTime = now;

        // Single touch pan setup
        if (this.scale > 1) {
          this.isDragging = true;
          this.dragStartX = touch.clientX - this.translateX;
          this.dragStartY = touch.clientY - this.translateY;
          this.imgEl.classList.add('is-dragging');
        } else {
          this.isSwipingDismiss = true;
        }
      } else if (e.touches.length === 2) {
        // Pinch-to-zoom setup: Chặn cử chỉ mặc định của browser
        e.preventDefault();
        this.isDragging = false;
        this.isSwipingDismiss = false;
        this.initialPinchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        this.initialPinchScale = this.scale;
      }
    };

    const handleTouchMove = (e) => {
      if (!this.modalEl.classList.contains('active')) return;
      if (e.target.closest('#lightbox-controls-bar')) return;

      if (e.touches.length === 2 && this.initialPinchDist > 0) {
        // Pinch-to-zoom: Bắt buộc preventDefault() để không zoom cả trang web
        e.preventDefault();
        const currentDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const factor = currentDist / this.initialPinchDist;
        let targetScale = this.initialPinchScale * factor;
        targetScale = Math.min(this.maxScale, Math.max(0.85, targetScale));

        this.scale = targetScale;
        this.applyTransform(false);
      } else if (e.touches.length === 1) {
        const touch = e.touches[0];

        if (this.scale > 1) {
          // Pan when zoomed: Bắt buộc preventDefault()
          e.preventDefault();
          if (!this.isDragging) {
            this.isDragging = true;
            this.dragStartX = touch.clientX - this.translateX;
            this.dragStartY = touch.clientY - this.translateY;
            this.imgEl.classList.add('is-dragging');
          }
          this.translateX = touch.clientX - this.dragStartX;
          this.translateY = touch.clientY - this.dragStartY;
          this.applyTransform(false);
        } else if (this.scale <= 1 && this.isSwipingDismiss) {
          // Swipe vertically to dismiss
          const dy = touch.clientY - this.touchStartY;
          if (Math.abs(dy) > 12) {
            e.preventDefault();
          }
          this.translateY = dy * 0.85;
          const opacityFraction = Math.max(0.35, 1 - Math.abs(dy) / 450);
          this.modalEl.style.backgroundColor = `rgba(10, 10, 15, ${0.94 * opacityFraction})`;
          this.applyTransform(false);
        }
      }
    };

    const handleTouchEnd = (e) => {
      if (this.imgEl) this.imgEl.classList.remove('is-dragging');
      this.isDragging = false;

      if (e.touches.length === 0) {
        if (this.scale <= 1 && this.isSwipingDismiss) {
          this.isSwipingDismiss = false;
          if (Math.abs(this.translateY) > 90) {
            this.close();
            return;
          } else {
            if (this.modalEl) this.modalEl.style.backgroundColor = '';
            this.resetZoom(true);
            return;
          }
        }

        if (this.scale < this.minScale) {
          this.resetZoom(true);
        } else {
          this.constrainBounds();
          this.applyTransform(true);
        }
      }
    };

    // Gắn listener với { passive: false } trên modal và img
    this.modalEl.addEventListener('touchstart', handleTouchStart, { passive: false });
    this.modalEl.addEventListener('touchmove', handleTouchMove, { passive: false });
    this.modalEl.addEventListener('touchend', handleTouchEnd);
    this.modalEl.addEventListener('touchcancel', handleTouchEnd);

    this.imgEl.addEventListener('touchstart', handleTouchStart, { passive: false });
    this.imgEl.addEventListener('touchmove', handleTouchMove, { passive: false });
    this.imgEl.addEventListener('touchend', handleTouchEnd);
    this.imgEl.addEventListener('touchcancel', handleTouchEnd);
  },

  // --------------------------------------------------------------------------
  // ZOOM COMPUTATION & TRANSFORMS
  // --------------------------------------------------------------------------
  zoomBy(delta, clientX = null, clientY = null) {
    let targetScale;
    if (delta > 0) {
      if (this.scale < 1.35) targetScale = 1.5;
      else if (this.scale < 1.85) targetScale = 2.0;
      else if (this.scale < 2.35) targetScale = 2.5;
      else if (this.scale < 2.85) targetScale = 3.0;
      else targetScale = Math.min(this.maxScale, this.scale + 0.5);
    } else {
      if (this.scale > 2.65) targetScale = 2.5;
      else if (this.scale > 2.15) targetScale = 2.0;
      else if (this.scale > 1.65) targetScale = 1.5;
      else targetScale = 1.0;
    }
    this.zoomTo(targetScale, clientX, clientY);
  },

  zoomTo(targetScale, clientX = null, clientY = null) {
    if (!this.imgEl) return;

    if (targetScale <= 1.01) {
      this.resetZoom(true);
      return;
    }

    if (clientX !== null && clientY !== null) {
      const rect = this.imgEl.getBoundingClientRect();
      const originX = clientX - (rect.left + rect.width / 2);
      const originY = clientY - (rect.top + rect.height / 2);

      const ratio = targetScale / this.scale;
      this.translateX = this.translateX - originX * (ratio - 1) * 0.4;
      this.translateY = this.translateY - originY * (ratio - 1) * 0.4;
    }

    this.scale = targetScale;
    this.constrainBounds();
    this.applyTransform(true);
  },

  constrainBounds() {
    if (!this.imgEl || this.scale <= 1) {
      this.translateX = 0;
      this.translateY = 0;
      return;
    }

    const rect = this.imgEl.getBoundingClientRect();
    const naturalW = rect.width / (this.scale || 1);
    const naturalH = rect.height / (this.scale || 1);

    const currentW = naturalW * this.scale;
    const currentH = naturalH * this.scale;

    const maxPanX = Math.max(0, (currentW - window.innerWidth) / 2 + 40);
    const maxPanY = Math.max(0, (currentH - window.innerHeight) / 2 + 40);

    this.translateX = Math.min(maxPanX, Math.max(-maxPanX, this.translateX));
    this.translateY = Math.min(maxPanY, Math.max(-maxPanY, this.translateY));
  },

  applyTransform(animate = false) {
    if (!this.imgEl) return;

    if (animate) {
      this.imgEl.style.transition = 'transform 0.15s ease-out';
    } else {
      this.imgEl.style.transition = 'none';
    }

    this.imgEl.style.transform = `translate3d(${this.translateX}px, ${this.translateY}px, 0) scale(${this.scale})`;

    if (this.scale > 1.05) {
      this.imgEl.classList.add('is-zoomed');
    } else {
      this.imgEl.classList.remove('is-zoomed');
    }
  },

  resetZoom(animate = true) {
    this.scale = 1.0;
    this.translateX = 0;
    this.translateY = 0;
    this.isDragging = false;
    this.isSwipingDismiss = false;
    if (this.modalEl) this.modalEl.style.backgroundColor = '';
    this.applyTransform(animate);
  },

  // --------------------------------------------------------------------------
  // OPEN & CLOSE LIFECYCLE
  // --------------------------------------------------------------------------
  open(imgSrc, captionText = '') {
    if (!this.modalEl || !this.imgEl) return;

    // Reset zoom and coordinates
    this.resetZoom(false);

    this.imgEl.src = imgSrc;
    this.imgEl.alt = captionText || 'Kokoro Photo';

    if (this.captionEl) {
      this.captionEl.textContent = captionText;
      this.captionEl.style.display = captionText ? 'block' : 'none';
    }

    this.modalEl.classList.add('active');

    // Strict Body Scroll Lock
    if (window.lockBodyScroll) {
      window.lockBodyScroll(true);
    } else {
      document.body.classList.add('modal-scroll-locked');
      document.documentElement.classList.add('modal-scroll-locked');
    }
  },

  close() {
    if (!this.modalEl) return;

    this.modalEl.classList.remove('active');
    this.resetZoom(false);

    // Release Body Scroll Lock
    if (window.lockBodyScroll) {
      window.lockBodyScroll(false);
    } else {
      document.body.classList.remove('modal-scroll-locked');
      document.documentElement.classList.remove('modal-scroll-locked');
    }

    setTimeout(() => {
      if (this.imgEl) this.imgEl.src = '';
      if (this.captionEl) this.captionEl.textContent = '';
      if (this.modalEl) this.modalEl.style.backgroundColor = '';
    }, 250);
  }
};

window.Lightbox = Lightbox;

// Self-init when DOM ready if not called by app.js
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (window.Lightbox && !window.Lightbox.modalEl) window.Lightbox.init();
  });
} else {
  if (window.Lightbox && !window.Lightbox.modalEl) window.Lightbox.init();
}
