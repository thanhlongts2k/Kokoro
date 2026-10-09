/**
 * KOKORO (心) — DIARY ENTRY EDITOR (MODAL & BOTTOM SHEET)
 * Handles client-side photo previews, form data packaging,
 * and multipart/form-data upload to PostgreSQL via KokoroAPI.
 */

const Editor = {
  overlayEl: null,
  titleInput: null,
  contentInput: null,
  tagInput: null,
  dropzoneEl: null,
  fileInput: null,
  previewsContainer: null,
  saveBtn: null,

  selectedMood: 'serene',
  selectedMoodLabel: 'Serene 🌸',
  selectedFiles: [], // Array of real File objects to be uploaded

  init() {
    this.overlayEl = document.getElementById('editor-modal-overlay');
    this.titleInput = document.getElementById('editor-title-input');
    this.contentInput = document.getElementById('editor-content-input');
    this.tagInput = document.getElementById('editor-tag-input');
    this.dropzoneEl = document.getElementById('editor-dropzone');
    this.fileInput = document.getElementById('editor-file-input');
    this.previewsContainer = document.getElementById('editor-previews-grid');
    this.saveBtn = document.getElementById('editor-save-btn');

    if (!this.overlayEl) return;

    // Close buttons
    const closeBtn = document.getElementById('editor-close-btn');
    const cancelBtn = document.getElementById('editor-cancel-btn');
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());

    // Click outside overlay to close
    this.overlayEl.addEventListener('click', (e) => {
      if (e.target === this.overlayEl) this.close();
    });

    // Mood Selector chips
    const moodChips = document.querySelectorAll('.mood-option-chip');
    moodChips.forEach((chip) => {
      chip.addEventListener('click', () => {
        moodChips.forEach((c) => c.classList.remove('selected'));
        chip.classList.add('selected');
        this.selectedMood = chip.dataset.mood;
        this.selectedMoodLabel = chip.dataset.label;
      });
    });

    // File input change
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        this.handleFiles(e.target.files);
        // Reset file input value so re-selecting same file fires change event
        this.fileInput.value = '';
      });
    }

    // Drag and Drop
    if (this.dropzoneEl) {
      this.dropzoneEl.addEventListener('click', () => this.fileInput.click());
      this.dropzoneEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.dropzoneEl.style.borderColor = 'var(--sakura-500)';
      });
      this.dropzoneEl.addEventListener('dragleave', () => {
        this.dropzoneEl.style.borderColor = 'var(--sakura-300)';
      });
      this.dropzoneEl.addEventListener('drop', (e) => {
        e.preventDefault();
        this.dropzoneEl.style.borderColor = 'var(--sakura-300)';
        if (e.dataTransfer.files) {
          this.handleFiles(e.dataTransfer.files);
        }
      });
    }

    // Save button
    if (this.saveBtn) {
      this.saveBtn.addEventListener('click', () => this.save());
    }
  },

  open() {
    if (!this.overlayEl) return;
    this.resetForm();
    this.overlayEl.classList.add('active');
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      if (this.titleInput) this.titleInput.focus();
    }, 150);
  },

  close() {
    if (!this.overlayEl) return;
    this.overlayEl.classList.remove('active');
    document.body.style.overflow = '';
  },

  resetForm() {
    if (this.titleInput) this.titleInput.value = '';
    if (this.contentInput) this.contentInput.value = '';
    if (this.tagInput) this.tagInput.value = '';
    this.selectedFiles = [];
    this.renderPreviews();

    // Reset mood to serene
    const defaultChip = document.querySelector('.mood-option-chip[data-mood="serene"]');
    if (defaultChip) defaultChip.click();

    this.setLoading(false);
  },

  handleFiles(files) {
    if (!files || files.length === 0) return;

    Array.from(files).forEach((file) => {
      if (!file.type.startsWith('image/')) return;
      this.selectedFiles.push(file);
    });

    this.renderPreviews();
  },

  renderPreviews() {
    if (!this.previewsContainer) return;
    this.previewsContainer.innerHTML = '';

    this.selectedFiles.forEach((file, idx) => {
      const box = document.createElement('div');
      box.className = 'preview-thumb-box';

      const img = document.createElement('img');
      img.alt = file.name;
      const objectUrl = URL.createObjectURL(file);
      img.src = objectUrl;

      // Clean up objectUrl once image loads to prevent memory leaks
      img.onload = () => URL.revokeObjectURL(objectUrl);

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'preview-remove-btn';
      removeBtn.innerHTML = '&times;';
      removeBtn.title = 'Xóa ảnh';
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectedFiles.splice(idx, 1);
        this.renderPreviews();
      });

      box.appendChild(img);
      box.appendChild(removeBtn);
      this.previewsContainer.appendChild(box);
    });
  },

  setLoading(isLoading) {
    if (!this.saveBtn) return;
    if (isLoading) {
      this.saveBtn.disabled = true;
      this.saveBtn.innerHTML = `<span class="btn-spinner"></span> Đang tải ảnh & lưu...`;
    } else {
      this.saveBtn.disabled = false;
      this.saveBtn.innerHTML = `<i class="bi bi-check2-circle"></i> Lưu nhật ký`;
    }
  },

  async save() {
    const title = this.titleInput ? this.titleInput.value.trim() : '';
    const content = this.contentInput ? this.contentInput.value.trim() : '';

    if (!content) {
      if (window.KokoroApp) {
        window.KokoroApp.showToast('Vui lòng viết một chút cảm xúc vào nhật ký nhé! 🌸', 'warning');
      } else {
        alert('Vui lòng viết một chút cảm xúc vào nhật ký nhé! 🌸');
      }
      if (this.contentInput) this.contentInput.focus();
      return;
    }

    const rawTags = this.tagInput ? this.tagInput.value.trim() : '';
    const today = new Date().toISOString().split('T')[0];

    // Build FormData for multipart POST request
    const formData = new FormData();
    formData.append('title', title || 'Khoảnh khắc tĩnh lặng');
    formData.append('content', content);
    formData.append('mood', this.selectedMood);
    formData.append('weather', 'sunny');
    formData.append('entry_date', today);
    formData.append('tags', rawTags);

    // Append real photo files
    this.selectedFiles.forEach((file) => {
      formData.append('photos', file);
    });

    try {
      this.setLoading(true);

      const result = await window.KokoroAPI.createEntry(formData);

      if (window.KokoroApp) {
        window.KokoroApp.showToast('Đã lưu nhật ký thành công! ✨');
        await window.KokoroApp.loadEntries();
      }

      this.close();
    } catch (err) {
      console.error('[Editor] Lưu nhật ký thất bại:', err);
      if (window.KokoroApp) {
        window.KokoroApp.showToast(err.message || 'Lỗi khi lưu bài viết', 'error');
      } else {
        alert('Lỗi: ' + (err.message || 'Không thể lưu nhật ký'));
      }
    } finally {
      this.setLoading(false);
    }
  }
};

window.Editor = Editor;
