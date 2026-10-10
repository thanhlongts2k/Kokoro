/**
 * KOKORO (心) — DIARY ENTRY EDITOR (MODAL & BOTTOM SHEET)
 * Handles client-side photo previews, form data packaging,
 * multipart upload, auto-save drafts (localStorage),
 * and safe offline queueing (IndexedDB).
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
  draftBannerEl: null,
  draftTextEl: null,
  discardDraftBtn: null,
  modalTitleEl: null,
  saveBtnTextEl: null,

  editingEntryId: null,
  selectedMood: 'serene',
  selectedMoodLabel: 'Serene 🌸',
  selectedFiles: [], // Array of real File objects to be uploaded
  draftTimeout: null,

  getCurrentUserId() {
    return window.KokoroAuth && window.KokoroAuth.currentUser ? window.KokoroAuth.currentUser.id : null;
  },

  init() {
    this.overlayEl = document.getElementById('editor-modal-overlay');
    this.titleInput = document.getElementById('editor-title-input');
    this.contentInput = document.getElementById('editor-content-input');
    this.tagInput = document.getElementById('editor-tag-input');
    this.dropzoneEl = document.getElementById('editor-dropzone');
    this.fileInput = document.getElementById('editor-file-input');
    this.previewsContainer = document.getElementById('editor-previews-grid');
    this.saveBtn = document.getElementById('editor-save-btn');
    this.draftBannerEl = document.getElementById('editor-draft-banner');
    this.draftTextEl = document.getElementById('editor-draft-text');
    this.discardDraftBtn = document.getElementById('editor-discard-draft-btn');
    this.modalTitleEl = document.getElementById('editor-modal-title');
    this.saveBtnTextEl = document.getElementById('editor-save-btn-text');

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
        this.scheduleDraftSave();
      });
    });

    // Auto-save listeners on input changes (Debounce 1s)
    [this.titleInput, this.contentInput, this.tagInput].forEach((input) => {
      if (input) {
        input.addEventListener('input', () => this.scheduleDraftSave());
      }
    });

    // Discard draft button
    if (this.discardDraftBtn) {
      this.discardDraftBtn.addEventListener('click', () => this.discardDraft());
    }

    // File input change
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        this.handleFiles(e.target.files);
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

  scheduleDraftSave() {
    if (this.editingEntryId) return; // Do not auto-save draft when editing an existing entry
    clearTimeout(this.draftTimeout);
    this.draftTimeout = setTimeout(() => {
      const title = this.titleInput ? this.titleInput.value.trim() : '';
      const content = this.contentInput ? this.contentInput.value.trim() : '';
      const tags = this.tagInput ? this.tagInput.value.trim() : '';

      if (content || title) {
        const userId = this.getCurrentUserId();
        window.KokoroAPI.saveDraft(userId, {
          title,
          content,
          mood: this.selectedMood,
          tags
        });
        if (this.draftBannerEl && this.draftTextEl) {
          this.draftBannerEl.style.display = 'flex';
          const timeStr = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          this.draftTextEl.textContent = `Đã tự động lưu nháp lúc ${timeStr} 🌸`;
        }
      }
    }, 1000);
  },

  checkAndRestoreDraft() {
    const userId = this.getCurrentUserId();
    const draft = window.KokoroAPI.getDraft(userId);

    if (draft && (draft.content || draft.title)) {
      if (this.titleInput) this.titleInput.value = draft.title || '';
      if (this.contentInput) this.contentInput.value = draft.content || '';
      if (this.tagInput) this.tagInput.value = draft.tags || '';

      if (draft.mood) {
        const chip = document.querySelector(`.mood-option-chip[data-mood="${draft.mood}"]`);
        if (chip) chip.click();
      }

      if (this.draftBannerEl && this.draftTextEl) {
        this.draftBannerEl.style.display = 'flex';
        this.draftTextEl.textContent = 'Đã tự động khôi phục bản nháp chưa lưu ✨';
      }
      return true;
    } else {
      if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';
      return false;
    }
  },

  discardDraft() {
    const userId = this.getCurrentUserId();
    window.KokoroAPI.clearDraft(userId);
    this.resetForm();
    if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';
    if (window.KokoroApp) {
      window.KokoroApp.showToast('Đã xóa bản nháp thành công 🌸');
    }
  },

  open(entry = null) {
    if (!this.overlayEl) return;
    this.resetForm();

    if (entry) {
      // EDIT MODE
      this.editingEntryId = entry.id;
      this.editingEntryDate = entry.entryDate || entry.entry_date || null;
      if (this.modalTitleEl) this.modalTitleEl.textContent = 'Chỉnh Sửa Nhật Ký 🌸';
      if (this.saveBtnTextEl) this.saveBtnTextEl.textContent = 'Cập nhật bài viết ✨';

      if (this.titleInput) this.titleInput.value = entry.title || '';
      if (this.contentInput) this.contentInput.value = entry.content || '';
      if (this.tagInput) this.tagInput.value = (entry.tags || []).join(' ');

      if (entry.mood) {
        const chip = document.querySelector(`.mood-option-chip[data-mood="${entry.mood}"]`);
        if (chip) chip.click();
      }

      if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';

      // Previews of existing photos
      if (entry.photos && entry.photos.length > 0 && this.previewsContainer) {
        this.previewsContainer.innerHTML = entry.photos.map((p) => {
          const thumbUrl = window.KokoroAPI.resolveMediaUrl(p.thumbUrl || p.url);
          return `
            <div class="preview-item" title="Ảnh đã lưu" style="position: relative;">
              <img src="${thumbUrl}" alt="Existing Photo" />
              <div style="position: absolute; bottom: 2px; right: 4px; font-size: 9px; background: rgba(0,0,0,0.65); color: white; border-radius: 4px; padding: 1px 4px;">Đã lưu</div>
            </div>
          `;
        }).join('');
      }
    } else {
      // CREATE MODE
      this.editingEntryId = null;
      this.editingEntryDate = null;
      if (this.modalTitleEl) this.modalTitleEl.textContent = 'Ghi Lại Khoảnh Khắc 🌸';
      if (this.saveBtnTextEl) this.saveBtnTextEl.textContent = 'Lưu nhật ký ✨';
      this.checkAndRestoreDraft();
    }

    this.overlayEl.classList.add('active');
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      if (this.contentInput) this.contentInput.focus();
    }, 150);
  },

  close() {
    if (!this.overlayEl) return;
    clearTimeout(this.draftTimeout);
    this.editingEntryId = null;
    this.editingEntryDate = null;
    this.overlayEl.classList.remove('active');
    document.body.style.overflow = '';
  },

  resetForm() {
    if (this.titleInput) this.titleInput.value = '';
    if (this.contentInput) this.contentInput.value = '';
    if (this.tagInput) this.tagInput.value = '';
    this.selectedFiles = [];
    this.renderPreviews();

    const defaultChip = document.querySelector('.mood-option-chip[data-mood="serene"]');
    if (defaultChip) defaultChip.click();

    if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';
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
      this.saveBtn.innerHTML = `<span class="btn-spinner"></span> Đang xử lý...`;
    } else {
      this.saveBtn.disabled = false;
      const btnText = this.editingEntryId ? 'Cập nhật bài viết ✨' : 'Lưu nhật ký ✨';
      this.saveBtn.innerHTML = `<i class="bi bi-check2-circle"></i> <span id="editor-save-btn-text">${btnText}</span>`;
      this.saveBtnTextEl = document.getElementById('editor-save-btn-text');
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
    const targetDate = this.editingEntryId && this.editingEntryDate ? this.editingEntryDate : today;

    // CASE 1: OFFLINE MODE (No Internet Connection)
    if (!navigator.onLine) {
      this.setLoading(true);
      try {
        await window.KokoroAPI.saveOfflineEntry({
          title: title || 'Khoảnh khắc tĩnh lặng',
          content,
          mood: this.selectedMood,
          weather: 'sunny',
          entry_date: targetDate,
          tags: rawTags,
          photos: this.selectedFiles // Safely preserved as native Blobs in IndexedDB
        });

        const userId = this.getCurrentUserId();
        window.KokoroAPI.clearDraft(userId);

        if (window.KokoroApp) {
          window.KokoroApp.showToast('Đang ngoại tuyến. Bài viết đã được lưu vào hàng đợi và sẽ tự động đồng bộ khi có mạng! 🌸', 'info');
        }
        this.close();
      } catch (err) {
        console.error('[Editor] Lưu ngoại tuyến thất bại:', err);
        if (window.KokoroApp) {
          window.KokoroApp.showToast('Lỗi lưu ngoại tuyến: ' + err.message, 'error');
        }
      } finally {
        this.setLoading(false);
      }
      return;
    }

    // CASE 2: ONLINE MODE (Normal Multipart Upload)
    const formData = new FormData();
    formData.append('title', title || 'Khoảnh khắc tĩnh lặng');
    formData.append('content', content);
    formData.append('mood', this.selectedMood);
    formData.append('weather', 'sunny');
    formData.append('entry_date', targetDate);
    formData.append('tags', rawTags);

    this.selectedFiles.forEach((file) => {
      formData.append('photos', file);
    });

    try {
      this.setLoading(true);

      if (this.editingEntryId) {
        await window.KokoroAPI.updateEntry(this.editingEntryId, formData);
        if (window.KokoroApp) {
          window.KokoroApp.showToast('Đã cập nhật bài viết thành công! ✨');
          await window.KokoroApp.loadEntries();
          await window.KokoroApp.loadStats();
        }
      } else {
        await window.KokoroAPI.createEntry(formData);
        const userId = this.getCurrentUserId();
        window.KokoroAPI.clearDraft(userId);
        if (window.KokoroApp) {
          window.KokoroApp.showToast('Đã lưu nhật ký thành công! ✨');
          await window.KokoroApp.loadEntries();
          await window.KokoroApp.loadStats();
        }
      }

      this.close();
    } catch (err) {
      console.error('[Editor] Lưu nhật ký thất bại:', err);

      // Network fallback: If network dropped mid-request, save to IndexedDB queue safely
      const isNetworkError = !navigator.onLine || 
                             err.message.includes('Failed to fetch') || 
                             err.message.includes('Network') ||
                             err.message.includes('Load failed');

      if (isNetworkError) {
        try {
          await window.KokoroAPI.saveOfflineEntry({
            title: title || 'Khoảnh khắc tĩnh lặng',
            content,
            mood: this.selectedMood,
            weather: 'sunny',
            entry_date: today,
            tags: rawTags,
            photos: this.selectedFiles
          });
          const userId = this.getCurrentUserId();
          window.KokoroAPI.clearDraft(userId);
          if (window.KokoroApp) {
            window.KokoroApp.showToast('Mất kết nối máy chủ. Bài viết đã được chuyển vào hàng đợi ngoại tuyến an toàn! 🌸', 'warning');
          }
          this.close();
          return;
        } catch (offlineErr) {
          console.error('[Editor] Fallback offline save error:', offlineErr);
        }
      }

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
