/**
 * KOKORO (心) — CUSTOM DATE & TIME PICKER MODULE
 * Architecture: Clean Component, Zero-coupling with Editor controller.
 * Features: Mini calendar date selector, tactile touch time spinners,
 * Now shortcut, and ISO-8601 standard output.
 */

const KokoroDateTimePicker = (() => {
  let modalEl = null;
  let closeBtn = null;
  let cancelBtn = null;
  let confirmBtn = null;
  let nowBtn = null;

  let monthTitleEl = null;
  let prevMonthBtn = null;
  let nextMonthBtn = null;
  let daysGridEl = null;

  let nativeTimeInputEl = null;
  let timeDigitsEl = null;

  // Internal state
  let selectedYear = new Date().getFullYear();
  let selectedMonth = new Date().getMonth(); // 0-11
  let selectedDay = new Date().getDate();
  let selectedHour = new Date().getHours();
  let selectedMinute = new Date().getMinutes();

  let viewYear = selectedYear;
  let viewMonth = selectedMonth;

  let onConfirmCallback = null;

  const pad = (n) => String(n).padStart(2, '0');

  const formatDisplay = (y, m, d, h, min) => {
    return `${pad(d)}/${pad(m + 1)}/${y}, ${pad(h)}:${pad(min)}`;
  };

  const getDaysInMonth = (y, m) => new Date(y, m + 1, 0).getDate();
  const getFirstDayOfWeek = (y, m) => {
    const day = new Date(y, m, 1).getDay();
    // Convert Sunday=0 to Monday=0 (Mon=0, Tue=1 ... Sun=6)
    return day === 0 ? 6 : day - 1;
  };

  const renderCalendar = () => {
    if (!monthTitleEl || !daysGridEl) return;

    const monthNames = [
      'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4',
      'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8',
      'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
    ];
    monthTitleEl.textContent = `${monthNames[viewMonth]} ${viewYear}`;

    const totalDays = getDaysInMonth(viewYear, viewMonth);
    const startOffset = getFirstDayOfWeek(viewYear, viewMonth);
    const prevMonthTotalDays = getDaysInMonth(viewYear, viewMonth - 1);

    let html = '';

    // Previous month filler days
    for (let i = startOffset - 1; i >= 0; i--) {
      const d = prevMonthTotalDays - i;
      html += `<div class="dt-day-cell other-month">${d}</div>`;
    }

    // Current month days
    const today = new Date();
    for (let d = 1; d <= totalDays; d++) {
      const isSelected = (viewYear === selectedYear && viewMonth === selectedMonth && d === selectedDay);
      const isToday = (viewYear === today.getFullYear() && viewMonth === today.getMonth() && d === today.getDate());

      let classes = ['dt-day-cell'];
      if (isSelected) classes.push('selected');
      if (isToday) classes.push('today');

      html += `<div class="${classes.join(' ')}" data-day="${d}">${d}</div>`;
    }

    // Next month filler days to complete grid (up to 42 cells)
    const filledCells = startOffset + totalDays;
    const remaining = (7 - (filledCells % 7)) % 7;
    for (let d = 1; d <= remaining; d++) {
      html += `<div class="dt-day-cell other-month">${d}</div>`;
    }

    daysGridEl.innerHTML = html;

    // Attach day click handlers
    daysGridEl.querySelectorAll('.dt-day-cell:not(.other-month)').forEach((cell) => {
      cell.addEventListener('click', () => {
        selectedYear = viewYear;
        selectedMonth = viewMonth;
        selectedDay = Number(cell.dataset.day);
        renderCalendar();
      });
    });
  };

  const updateTimeInputs = () => {
    const timeFormatted = `${pad(selectedHour)}:${pad(selectedMinute)}`;
    if (timeDigitsEl) timeDigitsEl.textContent = timeFormatted;
    if (nativeTimeInputEl) nativeTimeInputEl.value = timeFormatted;
  };

  const setNow = () => {
    const now = new Date();
    selectedYear = now.getFullYear();
    selectedMonth = now.getMonth();
    selectedDay = now.getDate();
    selectedHour = now.getHours();
    selectedMinute = now.getMinutes();

    viewYear = selectedYear;
    viewMonth = selectedMonth;

    renderCalendar();
    updateTimeInputs();
  };

  const parseIsoString = (isoStr) => {
    if (!isoStr) return new Date();
    const parsed = new Date(isoStr);
    return isNaN(parsed.getTime()) ? new Date() : parsed;
  };

  const buildResult = () => {
    const entryDate = `${selectedYear}-${pad(selectedMonth + 1)}-${pad(selectedDay)}`;
    const createdAt = `${entryDate}T${pad(selectedHour)}:${pad(selectedMinute)}:00`;
    const displayDate = formatDisplay(selectedYear, selectedMonth, selectedDay, selectedHour, selectedMinute);
    return {
      entryDate,
      createdAt,
      displayDate,
      year: selectedYear,
      month: selectedMonth + 1,
      day: selectedDay,
      hour: selectedHour,
      minute: selectedMinute
    };
  };

  const init = () => {
    modalEl = document.getElementById('datetime-picker-modal');
    closeBtn = document.getElementById('datetime-picker-close-btn');
    cancelBtn = document.getElementById('dt-btn-cancel');
    confirmBtn = document.getElementById('dt-btn-confirm');
    nowBtn = document.getElementById('dt-btn-now');

    monthTitleEl = document.getElementById('dt-cal-month-title');
    prevMonthBtn = document.getElementById('dt-cal-prev-btn');
    nextMonthBtn = document.getElementById('dt-cal-next-btn');
    daysGridEl = document.getElementById('dt-cal-days-grid');

    nativeTimeInputEl = document.getElementById('dt-native-time-input');
    timeDigitsEl = document.getElementById('dt-time-digits-display');

    if (!modalEl) return;

    // Month Navigation
    if (prevMonthBtn) {
      prevMonthBtn.addEventListener('click', () => {
        viewMonth--;
        if (viewMonth < 0) {
          viewMonth = 11;
          viewYear--;
        }
        renderCalendar();
      });
    }

    if (nextMonthBtn) {
      nextMonthBtn.addEventListener('click', () => {
        viewMonth++;
        if (viewMonth > 11) {
          viewMonth = 0;
          viewYear++;
        }
        renderCalendar();
      });
    }

    // Native Time Input (iOS/Android Smooth Wheel Spinner)
    const handleTimeChange = (e) => {
      const val = e.target.value;
      if (!val) return;
      const parts = val.split(':');
      if (parts.length >= 2) {
        selectedHour = parseInt(parts[0], 10) || 0;
        selectedMinute = parseInt(parts[1], 10) || 0;
        if (timeDigitsEl) {
          timeDigitsEl.textContent = `${pad(selectedHour)}:${pad(selectedMinute)}`;
        }
      }
    };

    if (nativeTimeInputEl) {
      nativeTimeInputEl.addEventListener('input', handleTimeChange);
      nativeTimeInputEl.addEventListener('change', handleTimeChange);
    }

    // Shortcut Buttons
    if (nowBtn) nowBtn.addEventListener('click', () => setNow());

    // Modal Control
    if (closeBtn) closeBtn.addEventListener('click', () => close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => close());

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => {
        const result = buildResult();
        if (typeof onConfirmCallback === 'function') {
          onConfirmCallback(result);
        }
        close();
      });
    }

    // Click outside to close
    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) close();
    });
  };

  const open = (initialIsoString = null, callback = null) => {
    if (!modalEl) init();
    onConfirmCallback = callback;

    const dateObj = parseIsoString(initialIsoString);
    selectedYear = dateObj.getFullYear();
    selectedMonth = dateObj.getMonth();
    selectedDay = dateObj.getDate();
    selectedHour = dateObj.getHours();
    selectedMinute = dateObj.getMinutes();

    viewYear = selectedYear;
    viewMonth = selectedMonth;

    renderCalendar();
    updateTimeInputs();

    if (modalEl) {
      modalEl.classList.add('active');
    }
  };

  const close = () => {
    if (modalEl) {
      modalEl.classList.remove('active');
    }
  };

  return {
    init,
    open,
    close,
    getValue: buildResult,
    formatDisplay
  };
})();

window.KokoroDateTimePicker = KokoroDateTimePicker;
