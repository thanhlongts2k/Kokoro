/**
 * KOKORO (心) — DIARY ENTRY EDITOR (MODAL & BOTTOM SHEET)
 * Controller for creating and updating diary entries.
 * Decoupled from Tag Management and DateTime Picker.
 * Handles client-side photo previews, multipart upload,
 * draft auto-save, and offline queueing.
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
  suggestedTagsContainer: null,

  // Datetime Picker elements & state
  datetimeBtn: null,
  datetimeDisplay: null,
  entryDateInput: null,
  createdAtInput: null,
  selectedEntryDate: null,
  selectedCreatedAt: null,

  editingEntryId: null,
  selectedMood: 'serene',
  selectedMoodLabel: 'Serene 🌸',
  existingPhotos: [], // Array of { id, url, thumbUrl } for saved photos from server
  deletedPhotoIds: [], // Array of photo IDs to delete on server
  selectedFiles: [], // Array of real File objects to be uploaded
  draftTimeout: null,
  isSaving: false,

  getCurrentUserId() {
    return window.KokoroAuth && window.KokoroAuth.currentUser ? window.KokoroAuth.currentUser.id : null;
  },

  showToast(msg, type = 'success') {
    if (window.KokoroToast) {
      window.KokoroToast.show(msg, type);
    } else if (window.KokoroApp && window.KokoroApp.showToast) {
      window.KokoroApp.showToast(msg, type);
    }
  },

  init() {
    this.overlayEl = document.getElementById('editor-modal-overlay');
    this.titleInput = document.getElementById('editor-title-input');
    this.contentInput = document.getElementById('editor-content-input');
    this.tagInput = document.getElementById('editor-tag-input');
    this.suggestedTagsContainer = document.getElementById('editor-suggested-tags');
    this.dropzoneEl = document.getElementById('editor-dropzone');
    this.fileInput = document.getElementById('editor-file-input');
    this.previewsContainer = document.getElementById('editor-previews-grid');
    this.saveBtn = document.getElementById('editor-save-btn');
    this.draftBannerEl = document.getElementById('editor-draft-banner');
    this.draftTextEl = document.getElementById('editor-draft-text');
    this.discardDraftBtn = document.getElementById('editor-discard-draft-btn');
    this.modalTitleEl = document.getElementById('editor-modal-title');
    this.saveBtnTextEl = document.getElementById('editor-save-btn-text');

    // Datetime Picker integration
    this.datetimeBtn = document.getElementById('editor-datetime-btn');
    this.datetimeDisplay = document.getElementById('editor-datetime-display');
    this.entryDateInput = document.getElementById('editor-entry-date-input');
    this.createdAtInput = document.getElementById('editor-created-at-input');

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

    // Datetime Picker button click
    if (this.datetimeBtn) {
      this.datetimeBtn.addEventListener('click', () => {
        if (window.KokoroDateTimePicker) {
          window.KokoroDateTimePicker.open(this.selectedCreatedAt, (res) => {
            this.selectedEntryDate = res.entryDate;
            this.selectedCreatedAt = res.createdAt;
            if (this.datetimeDisplay) {
              this.datetimeDisplay.textContent = res.displayDate;
            }
            if (this.entryDateInput) this.entryDateInput.value = res.entryDate;
            if (this.createdAtInput) this.createdAtInput.value = res.createdAt;
            this.scheduleDraftSave();
          });
        }
      });
    }

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

    // Tag synchronization with TagManager
    if (this.tagInput) {
      this.tagInput.addEventListener('input', () => {
        if (window.KokoroTagManager) {
          window.KokoroTagManager.updateSuggestedChipsSelection(this.suggestedTagsContainer, this.tagInput);
        }
      });
    }

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

  updateDatetimeState(dateOrIso) {
    let dateObj = new Date();
    if (dateOrIso) {
      const parsed = new Date(dateOrIso);
      if (!isNaN(parsed.getTime())) {
        dateObj = parsed;
      }
    }

    const pad = (n) => String(n).padStart(2, '0');
    const y = dateObj.getFullYear();
    const m = pad(dateObj.getMonth() + 1);
    const d = pad(dateObj.getDate());
    const h = pad(dateObj.getHours());
    const min = pad(dateObj.getMinutes());

    this.selectedEntryDate = `${y}-${m}-${d}`;
    this.selectedCreatedAt = `${this.selectedEntryDate}T${h}:${min}:00`;

    const displayStr = `${d}/${m}/${y}, ${h}:${min}`;
    if (this.datetimeDisplay) {
      this.datetimeDisplay.textContent = displayStr;
    }
    if (this.entryDateInput) this.entryDateInput.value = this.selectedEntryDate;
    if (this.createdAtInput) this.createdAtInput.value = this.selectedCreatedAt;
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
          tags,
          created_at: this.selectedCreatedAt,
          entry_date: this.selectedEntryDate
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

      if (draft.created_at) {
        this.updateDatetimeState(draft.created_at);
      } else {
        this.updateDatetimeState(new Date());
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
    this.showToast('Đã xóa bản nháp thành công 🌸');
  },

  open(entry = null) {
    if (!this.overlayEl) return;
    this.resetForm();

    if (entry) {
      // EDIT MODE
      this.editingEntryId = entry.id;
      if (this.modalTitleEl) this.modalTitleEl.textContent = 'Chỉnh Sửa Nhật Ký 🌸';
      if (this.saveBtnTextEl) this.saveBtnTextEl.textContent = 'Cập nhật bài viết ✨';

      if (this.titleInput) this.titleInput.value = entry.title || '';
      if (this.contentInput) this.contentInput.value = entry.content || '';
      if (this.tagInput) this.tagInput.value = (entry.tags || []).join(' ');

      if (entry.mood) {
        const chip = document.querySelector(`.mood-option-chip[data-mood="${entry.mood}"]`);
        if (chip) chip.click();
      }

      // Populate datetime from existing entry
      const dtSource = entry.createdAt || entry.created_at || (entry.entryDate || entry.entry_date ? `${entry.entryDate || entry.entry_date}T12:00:00` : new Date());
      this.updateDatetimeState(dtSource);

      if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';

      // Load existing photos into state
      this.existingPhotos = (entry.photos || []).map((p) => ({
        id: p.id,
        url: p.url,
        thumbUrl: p.thumbUrl || p.url
      }));
      this.deletedPhotoIds = [];
      this.selectedFiles = [];
      this.renderAllPreviews();
    } else {
      // CREATE MODE
      this.editingEntryId = null;
      this.existingPhotos = [];
      this.deletedPhotoIds = [];
      this.selectedFiles = [];
      this.renderAllPreviews();
      if (this.modalTitleEl) this.modalTitleEl.textContent = 'Ghi Lại Khoảnh Khắc 🌸';
      if (this.saveBtnTextEl) this.saveBtnTextEl.textContent = 'Lưu nhật ký ✨';

      this.updateDatetimeState(new Date());
      this.checkAndRestoreDraft();
    }

    // Load suggested tags via decoupled TagManager
    if (window.KokoroTagManager) {
      window.KokoroTagManager.loadSuggestedChips(this.suggestedTagsContainer, this.tagInput, () => {
        this.scheduleDraftSave();
      });
    }

    this.overlayEl.classList.add('active');
    if (window.lockBodyScroll) window.lockBodyScroll(true);
    setTimeout(() => {
      if (this.contentInput) this.contentInput.focus();
    }, 150);
  },

  close() {
    if (!this.overlayEl) return;
    clearTimeout(this.draftTimeout);
    this.isSaving = false;
    this.editingEntryId = null;
    this.overlayEl.classList.remove('active');
    if (window.lockBodyScroll) window.lockBodyScroll(false);
  },

  resetForm() {
    this.isSaving = false;
    if (this.titleInput) this.titleInput.value = '';
    if (this.contentInput) this.contentInput.value = '';
    if (this.tagInput) this.tagInput.value = '';
    if (window.KokoroTagManager) {
      window.KokoroTagManager.updateSuggestedChipsSelection(this.suggestedTagsContainer, this.tagInput);
    }
    this.existingPhotos = [];
    this.deletedPhotoIds = [];
    this.selectedFiles = [];
    this.renderAllPreviews();

    const defaultChip = document.querySelector('.mood-option-chip[data-mood="serene"]');
    if (defaultChip) defaultChip.click();

    this.updateDatetimeState(new Date());

    if (this.draftBannerEl) this.draftBannerEl.style.display = 'none';
    this.setLoading(false);
  },

  handleFiles(files) {
    if (!files || files.length === 0) return;

    Array.from(files).forEach((file) => {
      const ext = (file.name || '').split('.').pop().toLowerCase();
      const isImage = (file.type && file.type.startsWith('image/')) || 
                      ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'].includes(ext);
      if (!isImage) return;
      this.selectedFiles.push(file);
    });

    this.renderAllPreviews();
  },

  renderAllPreviews() {
    if (!this.previewsContainer) return;
    this.previewsContainer.innerHTML = '';

    // 1. Render existing photos from server with "Đã lưu" badge and remove button
    this.existingPhotos.forEach((photo, idx) => {
      const box = document.createElement('div');
      box.className = 'preview-thumb-box';
      box.setAttribute('data-photo-id', photo.id);

      const img = document.createElement('img');
      img.src = window.KokoroAPI.resolveMediaUrl(photo.thumbUrl || photo.url);
      img.alt = 'Ảnh đã lưu';

      const badge = document.createElement('div');
      badge.className = 'preview-saved-badge';
      badge.textContent = 'Đã lưu';

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'preview-remove-btn';
      removeBtn.innerHTML = '&times;';
      removeBtn.title = 'Xóa ảnh này';
      removeBtn.setAttribute('aria-label', 'Xóa ảnh này');
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deletedPhotoIds.push(photo.id);
        this.existingPhotos.splice(idx, 1);
        this.renderAllPreviews();
      });

      box.appendChild(img);
      box.appendChild(badge);
      box.appendChild(removeBtn);
      this.previewsContainer.appendChild(box);
    });

    // 2. Render newly selected files with remove button
    this.selectedFiles.forEach((file, idx) => {
      const box = document.createElement('div');
      box.className = 'preview-thumb-box';

      const img = document.createElement('img');
      img.alt = file.name;
      const objectUrl = URL.createObjectURL(file);
      img.src = objectUrl;
      img.onload = () => URL.revokeObjectURL(objectUrl);

      const ext = (file.name || '').split('.').pop().toLowerCase();
      const isHeic = ext === 'heic' || ext === 'heif';

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'preview-remove-btn';
      removeBtn.innerHTML = '&times;';
      removeBtn.title = 'Hủy chọn ảnh mới';
      removeBtn.setAttribute('aria-label', 'Hủy chọn ảnh mới');
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectedFiles.splice(idx, 1);
        this.renderAllPreviews();
      });

      // Gracefully handle HEIC format preview failure on browsers without native HEIC decoding
      if (isHeic) {
        img.onerror = () => {
          img.style.display = 'none';
          const placeholder = document.createElement('div');
          placeholder.className = 'preview-heic-placeholder';
          placeholder.style.cssText = 'width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,183,197,0.18); color: var(--text-muted); font-size: 10px; padding: 4px; text-align: center; border-radius: 12px;';
          placeholder.innerHTML = `<i class="bi bi-camera-fill text-sakura" style="font-size: 20px; margin-bottom: 2px;"></i><span style="overflow: hidden; text-overflow: ellipsis; max-width: 90%; white-space: nowrap;">${file.name}</span>`;
          box.insertBefore(placeholder, removeBtn);
        };
      }

      box.appendChild(img);
      box.appendChild(removeBtn);
      this.previewsContainer.appendChild(box);
    });
  },

  renderPreviews() {
    this.renderAllPreviews();
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
    if (this.isSaving) return;

    const title = this.titleInput ? this.titleInput.value.trim() : '';
    const content = this.contentInput ? this.contentInput.value.trim() : '';
    const hasPhotos = (this.existingPhotos && this.existingPhotos.length > 0) || 
                      (this.selectedFiles && this.selectedFiles.length > 0);

    // Edge case: Allow photo-only entries if photos exist. Require content only if NO photos attached.
    if (!content && !hasPhotos) {
      this.showToast('Vui lòng viết nội dung hoặc chọn ít nhất một hình ảnh nhé! 🌸', 'warning');
      if (this.contentInput) this.contentInput.focus();
      return;
    }

    const rawTags = this.tagInput ? this.tagInput.value.trim() : '';
    const targetDate = this.selectedEntryDate || new Date().toISOString().split('T')[0];
    const targetCreatedAt = this.selectedCreatedAt || new Date().toISOString();

    this.isSaving = true;

    // CASE 1: OFFLINE MODE (No Internet Connection)
    if (!navigator.onLine) {
      this.setLoading(true);
      try {
        const userId = this.getCurrentUserId();
        await window.KokoroAPI.saveOfflineEntry({
          user_id: userId,
          title: title || 'Khoảnh khắc tĩnh lặng',
          content,
          mood: this.selectedMood,
          weather: 'sunny',
          entry_date: targetDate,
          created_at: targetCreatedAt,
          tags: rawTags,
          photos: this.selectedFiles // Safely preserved as native Blobs in IndexedDB
        });

        window.KokoroAPI.clearDraft(userId);
        this.showToast('Đang ngoại tuyến. Bài viết đã được lưu vào hàng đợi và sẽ tự động đồng bộ khi có mạng! 🌸', 'info');
        this.close();
      } catch (err) {
        console.error('[Editor] Lưu ngoại tuyến thất bại:', err);
        this.showToast('Lỗi lưu ngoại tuyến: ' + err.message, 'error');
      } finally {
        this.isSaving = false;
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
    formData.append('created_at', targetCreatedAt);
    formData.append('tags', rawTags);

    if (this.deletedPhotoIds.length > 0) {
      formData.append('deleted_photo_ids', JSON.stringify(this.deletedPhotoIds));
    }

    this.selectedFiles.forEach((file) => {
      formData.append('photos', file);
    });

    try {
      this.setLoading(true);

      if (this.editingEntryId) {
        await window.KokoroAPI.updateEntry(this.editingEntryId, formData);
        this.showToast('Đã cập nhật bài viết thành công! ✨');
        if (window.KokoroApp) {
          await window.KokoroApp.loadEntries();
          await window.KokoroApp.loadStats();
        }
      } else {
        await window.KokoroAPI.createEntry(formData);
        const userId = this.getCurrentUserId();
        window.KokoroAPI.clearDraft(userId);
        this.showToast('Đã lưu nhật ký thành công! ✨');
        if (window.KokoroApp) {
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
          const userId = this.getCurrentUserId();
          await window.KokoroAPI.saveOfflineEntry({
            user_id: userId,
            title: title || 'Khoảnh khắc tĩnh lặng',
            content,
            mood: this.selectedMood,
            weather: 'sunny',
            entry_date: targetDate,
            created_at: targetCreatedAt,
            tags: rawTags,
            photos: this.selectedFiles
          });
          window.KokoroAPI.clearDraft(userId);
          this.showToast('Mất kết nối máy chủ. Bài viết đã được chuyển vào hàng đợi ngoại tuyến an toàn! 🌸', 'warning');
          this.close();
          return;
        } catch (offlineErr) {
          console.error('[Editor] Fallback offline save error:', offlineErr);
        }
      }

      this.showToast(err.message || 'Lỗi khi lưu bài viết', 'error');
    } finally {
      this.isSaving = false;
      this.setLoading(false);
    }
  }
};

window.Editor = Editor;
