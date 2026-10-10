/**
 * KOKORO (心) — ZEN AMBIENT SOUND PLAYER
 * Calming background natural soundscapes: Rain, Furin Chimes, Waves, Zen Stream
 * Seamless Loop, Volume Slider & Soft Fade-In/Out
 */

const ZenAudio = {
  tracks: {
    rain: {
      key: 'rain',
      name: 'Mưa Rơi Mái Hiên',
      desc: 'Tiếng mưa rào êm đềm bên hiên chùa',
      file: './audio/rain.mp3',
      emoji: '🌧️',
      icon: 'bi-cloud-rain'
    },
    furin: {
      key: 'furin',
      name: 'Chuông Gió Furin',
      desc: 'Chuông gió Nhật Bản trong gió hạ',
      file: './audio/furin.mp3',
      emoji: '🎐',
      icon: 'bi-bell'
    },
    waves: {
      key: 'waves',
      name: 'Sóng Biển Đêm',
      desc: 'Sóng vỗ bờ cát nhẹ nhàng thư thái',
      file: './audio/waves.mp3',
      emoji: '🌊',
      icon: 'bi-water'
    },
    stream: {
      key: 'stream',
      name: 'Suối Thiền Zen',
      desc: 'Tiếng suối nước róc rách & ống tre',
      file: './audio/stream.mp3',
      emoji: '🎍',
      icon: 'bi-flower2'
    }
  },

  audioEl: null,
  currentTrackKey: 'rain',
  isPlaying: false,
  isMuted: false,
  volume: 0.5,
  fadeInterval: null,

  init() {
    // Restore preferences
    const savedTrack = localStorage.getItem('kokoro_zen_sound');
    if (savedTrack && this.tracks[savedTrack]) {
      this.currentTrackKey = savedTrack;
    }

    const savedVol = localStorage.getItem('kokoro_zen_volume');
    if (savedVol !== null) {
      this.volume = parseFloat(savedVol);
    }

    const savedMute = localStorage.getItem('kokoro_zen_muted');
    if (savedMute === 'true') {
      this.isMuted = true;
    }

    this.createAudioElement();
    this.bindEvents();
    this.renderTrackOptions();
    this.updateUi();
  },

  resolveAudioUrl(path) {
    // Safe relative resolution
    return path;
  },

  createAudioElement() {
    if (this.audioEl) {
      this.audioEl.pause();
      this.audioEl.src = '';
    }

    this.audioEl = new Audio();
    this.audioEl.loop = true;
    this.audioEl.volume = this.isMuted ? 0 : this.volume;
    this.audioEl.preload = 'none';

    const track = this.tracks[this.currentTrackKey];
    this.audioEl.src = this.resolveAudioUrl(track.file);

    this.audioEl.addEventListener('error', (e) => {
      console.warn('[ZenAudio] Audio playback error:', e);
    });
  },

  async play() {
    if (!this.audioEl) this.createAudioElement();

    try {
      // Smooth fade-in
      const targetVol = this.isMuted ? 0 : this.volume;
      this.audioEl.volume = 0;
      await this.audioEl.play();
      this.isPlaying = true;
      this.updateUi();

      this.fadeVolume(0, targetVol, 350);
    } catch (err) {
      console.warn('[ZenAudio] Autoplay or playback rejected:', err);
      this.isPlaying = false;
      this.updateUi();
    }
  },

  pause() {
    if (!this.audioEl || !this.isPlaying) return;

    // Smooth fade-out before pausing
    const currentVol = this.audioEl.volume;
    this.fadeVolume(currentVol, 0, 250, () => {
      this.audioEl.pause();
      this.isPlaying = false;
      this.updateUi();
    });
  },

  toggle() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  },

  switchTrack(trackKey) {
    if (!this.tracks[trackKey]) return;
    this.currentTrackKey = trackKey;
    localStorage.setItem('kokoro_zen_sound', trackKey);

    const wasPlaying = this.isPlaying;
    if (this.audioEl) {
      this.audioEl.pause();
    }

    this.createAudioElement();

    if (wasPlaying) {
      this.play();
    } else {
      this.updateUi();
    }
  },

  setVolume(vol) {
    this.volume = Math.max(0, Math.min(1, vol));
    localStorage.setItem('kokoro_zen_volume', String(this.volume));
    if (!this.isMuted && this.audioEl) {
      this.audioEl.volume = this.volume;
    }
    this.updateUi();
  },

  toggleMute() {
    this.isMuted = !this.isMuted;
    localStorage.setItem('kokoro_zen_muted', String(this.isMuted));
    if (this.audioEl) {
      this.audioEl.volume = this.isMuted ? 0 : this.volume;
    }
    this.updateUi();
  },

  fadeVolume(from, to, durationMs, onComplete = null) {
    if (this.fadeInterval) clearInterval(this.fadeInterval);
    const steps = 15;
    const stepTime = durationMs / steps;
    const diff = to - from;
    let currentStep = 0;

    this.fadeInterval = setInterval(() => {
      currentStep++;
      const current = from + (diff * (currentStep / steps));
      if (this.audioEl) {
        this.audioEl.volume = Math.max(0, Math.min(1, current));
      }

      if (currentStep >= steps) {
        clearInterval(this.fadeInterval);
        this.fadeInterval = null;
        if (this.audioEl) this.audioEl.volume = to;
        if (onComplete) onComplete();
      }
    }, stepTime);
  },

  renderTrackOptions() {
    const listEl = document.getElementById('zen-track-chips');
    if (!listEl) return;

    listEl.innerHTML = Object.values(this.tracks).map((t) => {
      const active = t.key === this.currentTrackKey ? 'active' : '';
      return `
        <button type="button" class="zen-chip ${active}" data-zen-track="${t.key}" title="${t.desc}">
          <span>${t.emoji}</span>
          <span>${t.name}</span>
        </button>
      `;
    }).join('');

    listEl.querySelectorAll('[data-zen-track]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const key = e.currentTarget.dataset.zenTrack;
        this.switchTrack(key);
      });
    });
  },

  updateUi() {
    // 1. Play / Pause button in header or widget
    const toggleBtn = document.getElementById('zen-toggle-btn');
    const playIcon = document.getElementById('zen-toggle-icon');
    const waveEl = document.getElementById('zen-soundwave');
    const trackNameEl = document.getElementById('zen-current-track-name');

    const track = this.tracks[this.currentTrackKey];

    if (toggleBtn) {
      toggleBtn.classList.toggle('playing', this.isPlaying);
      toggleBtn.title = this.isPlaying ? `Đang phát: ${track.name} (Bấm để tạm dừng)` : 'Phát âm thanh thư giãn Zen';
    }

    if (playIcon) {
      playIcon.className = this.isPlaying ? 'bi bi-pause-fill' : 'bi bi-play-fill';
    }

    if (waveEl) {
      waveEl.classList.toggle('active', this.isPlaying);
    }

    if (trackNameEl) {
      trackNameEl.textContent = `${track.emoji} ${track.name}`;
    }

    // 2. Volume slider & mute icon
    const volSlider = document.getElementById('zen-volume-slider');
    const muteBtnIcon = document.getElementById('zen-mute-icon');

    if (volSlider) {
      volSlider.value = Math.round(this.volume * 100);
    }

    if (muteBtnIcon) {
      if (this.isMuted || this.volume === 0) {
        muteBtnIcon.className = 'bi bi-volume-mute-fill text-muted';
      } else if (this.volume < 0.5) {
        muteBtnIcon.className = 'bi bi-volume-down-fill text-sakura';
      } else {
        muteBtnIcon.className = 'bi bi-volume-up-fill text-sakura';
      }
    }

    // 3. Highlight active track chip
    document.querySelectorAll('[data-zen-track]').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.zenTrack === this.currentTrackKey);
    });
  },

  bindEvents() {
    // Play/Pause button
    const toggleBtn = document.getElementById('zen-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggle());
    }

    // Toggle expansion of player panel
    const expandBtn = document.getElementById('zen-expand-btn');
    const panel = document.getElementById('zen-player-panel');
    if (expandBtn && panel) {
      expandBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('active');
      });
      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && !expandBtn.contains(e.target)) {
          panel.classList.remove('active');
        }
      });
    }

    // Volume Slider input
    const volSlider = document.getElementById('zen-volume-slider');
    if (volSlider) {
      volSlider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value) / 100;
        this.setVolume(val);
      });
    }

    // Mute button
    const muteBtn = document.getElementById('zen-mute-btn');
    if (muteBtn) {
      muteBtn.addEventListener('click', () => this.toggleMute());
    }
  }
};

window.ZenAudio = ZenAudio;
