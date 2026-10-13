/**
 * KOKORO (心) — CALENDAR VIEW COMPONENT
 * Handles monthly calendar calculations, mini calendar widget,
 * full-month grid with mood dots, and selected date entries rendering.
 * Complies with AGENTS.md: Modular Layered Architecture & Single Responsibility Principle.
 */

const CalendarView = {
  MONTH_NAMES: [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ],

  MOOD_COLOR_MAP: {
    serene: 'var(--mood-serene)',
    cozy: 'var(--mood-cozy)',
    reflective: 'var(--mood-reflective)',
    grateful: 'var(--mood-grateful)',
    energetic: 'var(--mood-energetic)',
    melancholy: 'var(--mood-melancholy)'
  },

  /**
   * Render Mini Calendar Widget (in Desktop Sidebar or Navigation panel)
   */
  renderMiniCalendar(options) {
    const { gridEl, monthTitleEl, entries, activeDateFilter, onSelectDate } = options;
    if (!gridEl) return;

    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();

    if (monthTitleEl) {
      monthTitleEl.textContent = `${this.MONTH_NAMES[currentMonth]} ${currentYear}`;
    }

    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay(); // 0: Sun
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    const datesWithEntries = new Set((entries || []).map((e) => e.entryDate));

    let html = `
      <div class="cal-day-label">CN</div>
      <div class="cal-day-label">T2</div>
      <div class="cal-day-label">T3</div>
      <div class="cal-day-label">T4</div>
      <div class="cal-day-label">T5</div>
      <div class="cal-day-label">T6</div>
      <div class="cal-day-label">T7</div>
    `;

    // Empty spaces before first day
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<div class="cal-day-cell empty"></div>`;
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = day === today.getDate();
      const hasEntry = datesWithEntries.has(dateStr);
      const isSelected = activeDateFilter === dateStr;

      html += `
        <div class="cal-day-cell ${isToday ? 'today' : ''} ${hasEntry ? 'has-entry' : ''} ${isSelected ? 'selected' : ''}" 
             data-date="${dateStr}">
          <span>${day}</span>
        </div>
      `;
    }

    gridEl.innerHTML = html;

    gridEl.querySelectorAll('.cal-day-cell[data-date]').forEach((cell) => {
      cell.addEventListener('click', (e) => {
        const d = e.currentTarget.dataset.date;
        if (onSelectDate) onSelectDate(d);
      });
    });
  },

  /**
   * Render Interactive Full Month Calendar with Mood Dots
   */
  renderFullCalendar(options) {
    const { gridEl, monthTitleEl, entries, calYear, calMonth, selectedCalDate, onSelectDate } = options;
    if (!gridEl) return;

    const currentYear = calYear;
    const currentMonth = calMonth;

    if (monthTitleEl) {
      monthTitleEl.textContent = `${this.MONTH_NAMES[currentMonth]} ${currentYear}`;
    }

    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay(); // 0: Sun
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    // Map dates to moods array
    const dateToMoods = {};
    (entries || []).forEach((e) => {
      if (e.entryDate) {
        if (!dateToMoods[e.entryDate]) dateToMoods[e.entryDate] = [];
        if (e.mood && !dateToMoods[e.entryDate].includes(e.mood)) {
          dateToMoods[e.entryDate].push(e.mood);
        }
      }
    });

    let html = `
      <div class="c-calendar-weekday">CN</div>
      <div class="c-calendar-weekday">T2</div>
      <div class="c-calendar-weekday">T3</div>
      <div class="c-calendar-weekday">T4</div>
      <div class="c-calendar-weekday">T5</div>
      <div class="c-calendar-weekday">T6</div>
      <div class="c-calendar-weekday">T7</div>
    `;

    // Empty spaces before first day
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<div class="c-calendar-day empty"></div>`;
    }

    // Days in Month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = dateStr === todayStr;
      const isSelected = dateStr === selectedCalDate;
      const dayMoods = dateToMoods[dateStr] || [];
      const hasEntries = dayMoods.length > 0;

      let dotsHtml = '';
      if (hasEntries) {
        dotsHtml = dayMoods
          .slice(0, 4)
          .map((m) => `<span class="c-calendar-dot" style="background: ${this.MOOD_COLOR_MAP[m] || 'var(--sakura-400)'};"></span>`)
          .join('');
      }

      html += `
        <div class="c-calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''} ${hasEntries ? 'has-entry' : ''}" 
             data-full-date="${dateStr}">
          <span class="c-calendar-day-num">${day}</span>
          <div class="c-calendar-dots">${dotsHtml}</div>
        </div>
      `;
    }

    gridEl.innerHTML = html;

    gridEl.querySelectorAll('.c-calendar-day[data-full-date]').forEach((cell) => {
      cell.addEventListener('click', (e) => {
        const d = e.currentTarget.dataset.fullDate;
        if (onSelectDate) onSelectDate(d);
      });
    });
  },

  /**
   * Render list of entries for selected calendar date
   */
  renderSelectedDateEntries(options) {
    const { listEl, headingEl, entries, selectedCalDate, cardBuilder, attachCardActions } = options;
    if (!listEl) return;

    if (headingEl && selectedCalDate) {
      const parts = selectedCalDate.split('-');
      if (parts.length === 3) {
        headingEl.textContent = `Khoảnh khắc ngày ${parts[2]}/${parts[1]}/${parts[0]} 🌸`;
      }
    }

    const matchedEntries = (entries || []).filter((e) => e.entryDate === selectedCalDate);

    if (matchedEntries.length === 0) {
      listEl.innerHTML = `
        <div class="glass-panel" style="padding: 32px 20px; text-align: center; border-radius: var(--radius-lg);">
          <div style="font-size: 32px; margin-bottom: 8px;">🍃</div>
          <div style="font-size: 14.5px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">Chưa có khoảnh khắc nào trong ngày này</div>
          <div style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 16px;">Lắng đọng tâm trí và ghi lại những điều nhẹ nhàng của bạn nhé.</div>
          <button class="c-btn c-btn--primary" onclick="if(window.Editor){ window.Editor.open(); }">
            <i class="bi bi-pencil-square"></i> + Ghi nhật ký cho ngày này
          </button>
        </div>
      `;
      return;
    }

    listEl.innerHTML = matchedEntries.map((e) => cardBuilder(e)).join('');
    if (attachCardActions) {
      attachCardActions(listEl);
    }
  }
};

window.CalendarView = CalendarView;

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CalendarView };
}
