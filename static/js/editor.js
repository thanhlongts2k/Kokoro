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

  // Weather Picker elements & state (v1.6.1)
  weatherPickerContainer: null,
  weatherInput: null,
  selectedWeather: 'sunny',

  editingEntryId: null,
  selectedCategoryId: null,
  categories: [],
  moodPickerContainer: null,
  manageCategoriesLink: null,
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

    // Mood & Category Picker elements
    this.moodPickerContainer = document.getElementById('editor-mood-picker-list');
    this.manageCategoriesLink = document.getElementById('editor-manage-categories-link');
    if (this.manageCategoriesLink) {
      this.manageCategoriesLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.KokoroTagManager) {
          window.KokoroTagManager.openManagerModal('categories');
        }
      });
    }

    // Datetime Picker integration
    this.datetimeBtn = document.getElementById('editor-datetime-btn');
    this.datetimeDisplay = document.getElementById('editor-datetime-display');
    this.entryDateInput = document.getElementById('editor-entry-date-input');
    this.createdAtInput = document.getElementById('editor-created-at-input');

    // Weather Picker integration (v1.6.1)
    this.weatherPickerContainer = document.getElementById('editor-weather-picker-list');
    this.weatherInput = document.getElementById('editor-weather-input');
    if (this.weatherPickerContainer) {
      this.weatherPickerContainer.querySelectorAll('.weather-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
          this.setWeather(chip.dataset.weather);
          this.scheduleDraftSave();
        });
      });
    }

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

  setWeather(weather = 'sunny') {
    const w = weather || 'sunny';
    this.selectedWeather = w;
    if (this.weatherInput) this.weatherInput.value = w;
    if (this.weatherPickerContainer) {
      this.weatherPickerContainer.querySelectorAll('.weather-chip').forEach((chip) => {
        if (chip.dataset.weather === w) {
          chip.classList.add('active');
        } else {
          chip.classList.remove('active');
        }
      });
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
          category_id: this.selectedCategoryId,
          weather: this.selectedWeather,
          tags,
          created_at: this.selectedCreatedAt,
          entry_date: this.selectedEntryDate
        });
        if (this.draftBannerEl && this.draftTextEl) {
          const timeStr = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          this.draftTextEl.textContent = `Đã tự động lưu nháp lúc ${timeStr} 🌸`;
          this.draftBannerEl.style.display = 'flex';
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

      if (draft.category_id || draft.mood) {
        this.renderCategoryChips(draft.category_id, draft.mood);
      }

      if (draft.weather) {
        this.setWeather(draft.weather);
      } else {
        this.setWeather('sunny');
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

  async loadCategories(targetCategoryId = null, targetMood = null) {
    if (!this.moodPickerContainer || !window.KokoroAPI) return;
    try {
      const res = await window.KokoroAPI.getCategories();
      if (res && res.status === 'success' && Array.isArray(res.categories)) {
        this.categories = res.categories;
      }
    } catch (err) {
      console.warn('[Editor] Không thể tải danh mục:', err);
    }

    if (!this.categories || this.categories.length === 0) {
      this.categories = [
        { id: null, name: 'Bình yên', icon: '🌸', color: '#ec4899' },
        { id: null, name: 'Ấm áp', icon: '☕', color: '#f59e0b' },
        { id: null, name: 'Chiêm nghiệm', icon: '🌙', color: '#8b5cf6' },
        { id: null, name: 'Biết ơn', icon: '🍵', color: '#10b981' },
        { id: null, name: 'Năng lượng', icon: '⚡', color: '#3b82f6' }
      ];
    }

    this.renderCategoryChips(targetCategoryId, targetMood);
  },

  renderCategoryChips(targetCategoryId = null, targetMood = null) {
    if (!this.moodPickerContainer) return;

    // Determine active category
    let activeCat = null;
    if (targetCategoryId) {
      activeCat = this.categories.find((c) => c.id === Number(targetCategoryId));
    }
    if (!activeCat && targetMood) {
      const lowerMood = String(targetMood).toLowerCase();
      activeCat = this.categories.find((c) =>
        c.name.toLowerCase() === lowerMood ||
        (c.name === 'Bình yên' && lowerMood === 'serene') ||
        (c.name === 'Ấm áp' && lowerMood === 'cozy') ||
        (c.name === 'Chiêm nghiệm' && lowerMood === 'reflective') ||
        (c.name === 'Biết ơn' && lowerMood === 'grateful') ||
        (c.name === 'Năng lượng' && lowerMood === 'energetic')
      );
    }
    if (!activeCat) {
      activeCat = this.categories[0];
    }

    this.selectedCategoryId = activeCat ? activeCat.id : null;
    this.selectedMood = activeCat ? activeCat.name : 'serene';
    this.selectedMoodLabel = activeCat ? `${activeCat.icon} ${activeCat.name}` : '🌸 Bình yên';

    const catInput = document.getElementById('editor-category-id-input');
    if (catInput) catInput.value = this.selectedCategoryId || '';

    this.moodPickerContainer.innerHTML = this.categories.map((c) => {
      const isSelected = activeCat && (activeCat.id === c.id || (!activeCat.id && !c.id && activeCat.name === c.name));
      const safeName = window.escapeHtml(c.name);
      const safeIcon = window.escapeHtml(c.icon || '🌸');
      const safeColor = window.escapeHtml(c.color || '#ec4899');
      return `
        <button type="button" 
                class="mood-option-chip category-option-chip ${isSelected ? 'selected' : ''}" 
                data-category-id="${c.id || ''}" 
                data-mood="${safeName}" 
                data-icon="${safeIcon}" 
                data-color="${safeColor}"
                style="--chip-color: ${safeColor};">
          <span>${safeIcon}</span>
          <span>${safeName}</span>
        </button>
      `;
    }).join('');

    // Bind chip clicks
    this.moodPickerContainer.querySelectorAll('.mood-option-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        this.moodPickerContainer.querySelectorAll('.mood-option-chip').forEach((c) => c.classList.remove('selected'));
        chip.classList.add('selected');
        const catId = chip.dataset.categoryId ? Number(chip.dataset.categoryId) : null;
        this.selectedCategoryId = catId;
        this.selectedMood = chip.dataset.mood;
        this.selectedMoodLabel = `${chip.dataset.icon} ${chip.dataset.mood}`;
        if (catInput) catInput.value = catId || '';
        this.scheduleDraftSave();
      });
    });
  },

  async open(entry = null) {
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

      await this.loadCategories(entry.categoryId || entry.category_id, entry.mood);
      this.setWeather(entry.weather || 'sunny');

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
      this.setWeather('sunny');
      await this.loadCategories();
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
    this.selectedCategoryId = null;
    if (this.categories && this.categories.length > 0) {
      this.renderCategoryChips();
    }

    this.updateDatetimeState(new Date());
    this.setWeather('sunny');

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
          const safeFileName = window.escapeHtml ? window.escapeHtml(file.name) : file.name;
          placeholder.innerHTML = `<i class="bi bi-camera-fill text-sakura" style="font-size: 20px; margin-bottom: 2px;"></i><span style="overflow: hidden; text-overflow: ellipsis; max-width: 90%; white-space: nowrap;">${safeFileName}</span>`;
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
          category_id: this.selectedCategoryId,
          weather: this.selectedWeather || 'sunny',
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
    if (this.selectedCategoryId) {
      formData.append('category_id', String(this.selectedCategoryId));
    }
    formData.append('weather', this.selectedWeather || 'sunny');
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
