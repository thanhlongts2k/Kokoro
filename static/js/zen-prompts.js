/**
 * KOKORO (心) — DAILY ZEN PROMPT REPOSITORY & ENGINE (v1.6.2)
 * 100% Offline-First Mindful Journaling Prompts.
 * Uses local client date (YYYY-MM-DD via getLocalDateString) for deterministic daily rollover at 00:00 midnight.
 * Provides curated prompts across 4 mindful pillars:
 * 1. Gratitude & Simplicity (Biết ơn & Giản dị)
 * 2. Letting Go & Self-Compassion (Buông bỏ & Tự trắc ẩn)
 * 3. Presence & Observation (Hiện diện & Chiêm nghiệm)
 * 4. Hope & Inner Growth (Ước vọng & Năng lượng)
 */

(function () {
  'use strict';

  const ZEN_PROMPTS = [
    // Pillar 1: Biết ơn & Giản dị (Gratitude & Simplicity)
    {
      id: 1,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Một tách trà, một ngọn gió hay một ánh mắt ấm áp nào đã vô tình sưởi ấm bạn hôm nay?',
      suggestedMood: 'grateful',
      icon: '🍵'
    },
    {
      id: 2,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Điều giản dị nào trong ngày đã bất chợt khiến bạn mỉm cười nhẹ nhõm?',
      suggestedMood: 'grateful',
      icon: '🌸'
    },
    {
      id: 3,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Ai là người bạn muốn gửi lời cảm ơn thầm lặng nhất vào lúc này, và vì điều gì?',
      suggestedMood: 'grateful',
      icon: '🙏'
    },
    {
      id: 4,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Một góc nhỏ quen thuộc nào trong ngôi nhà hoặc trên đường đi làm khiến bạn cảm thấy an yên?',
      suggestedMood: 'cozy',
      icon: '🏡'
    },
    {
      id: 5,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Bữa ăn hôm nay có hương vị hay khoảnh khắc nào làm bạn cảm thấy được nuôi dưỡng?',
      suggestedMood: 'cozy',
      icon: '☕'
    },
    {
      id: 6,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Một bài hát, một giai điệu hay một âm thanh êm dịu nào đã đồng hành cùng bạn suốt ngày qua?',
      suggestedMood: 'serene',
      icon: '🎵'
    },
    {
      id: 7,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Điều may mắn nhỏ bé nào đã ghé thăm bạn hôm nay mà suýt nữa bạn đã bỏ quên?',
      suggestedMood: 'grateful',
      icon: '✨'
    },
    {
      id: 8,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Một người lạ nào đó đã mang lại cho bạn sự tử tế hoặc cảm giác an tâm hôm nay?',
      suggestedMood: 'grateful',
      icon: '🌿'
    },
    {
      id: 9,
      pillar: 'gratitude',
      pillarName: 'Biết ơn & Giản dị',
      text: 'Nếu được chọn một khoảnh khắc đẹp nhất để đóng khung cất vào ký ức ngày hôm nay, bạn chọn gì?',
      suggestedMood: 'cozy',
      icon: '🖼️'
    },

    // Pillar 2: Buông bỏ & Tự trắc ẩn (Letting Go & Self-Compassion)
    {
      id: 10,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Có điều gì đang đè nặng trong lòng mà hôm nay bạn sẵn sàng buông nhẹ một chút không?',
      suggestedMood: 'serene',
      icon: '🍃'
    },
    {
      id: 11,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Nếu được bao dung với chính mình hôm nay, bạn sẽ vỗ về và tha thứ cho điều gì?',
      suggestedMood: 'serene',
      icon: '🤍'
    },
    {
      id: 12,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Áp lực nào hôm nay thực chất xuất phát từ việc bạn đang quá khắt khe với chính mình?',
      suggestedMood: 'melancholy',
      icon: '🌧️'
    },
    {
      id: 13,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Nỗi muộn phiền nào hôm nay nhắc nhở bạn rằng bạn cũng chỉ là một con người cần nghỉ ngơi?',
      suggestedMood: 'melancholy',
      icon: '🕯️'
    },
    {
      id: 14,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Bạn có đang ôm giữ một kỳ vọng nào quá sức không? Bạn có thể cho phép mình thở ra lúc này chứ?',
      suggestedMood: 'serene',
      icon: '🌬️'
    },
    {
      id: 15,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Hãy viết ra một điều bạn không thể thay đổi hôm nay, và nhẹ nhàng nói: "Không sao cả, mọi chuyện sẽ qua".',
      suggestedMood: 'serene',
      icon: '🌸'
    },
    {
      id: 16,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Cảm xúc tiêu cực nào đã ghé thăm bạn hôm nay? Nếu coi nó như vị khách qua đường, bạn sẽ lắng nghe nó thế nào?',
      suggestedMood: 'melancholy',
      icon: '🚪'
    },
    {
      id: 17,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Điều gì bạn đã cố gắng hết sức hôm nay dù kết quả chưa trọn vẹn? Hãy tự ôm lấy nỗ lực đó.',
      suggestedMood: 'serene',
      icon: '🫂'
    },
    {
      id: 18,
      pillar: 'letting_go',
      pillarName: 'Buông bỏ & Tự trắc ẩn',
      text: 'Nếu ngày hôm nay là một trang sách khép lại, bạn muốn để lại điều gì ở phía sau mà không mang sang ngày mai?',
      suggestedMood: 'serene',
      icon: '📖'
    },

    // Pillar 3: Hiện diện & Chiêm nghiệm (Presence & Mindful Observation)
    {
      id: 19,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Khoảnh khắc nào trong ngày hôm nay bạn cảm nhận được mình thực sự hiện diện và đang sống trọn vẹn?',
      suggestedMood: 'reflective',
      icon: '🌙'
    },
    {
      id: 20,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Cơ thể và từng nhịp thở của bạn ngay lúc này đang thì thầm điều gì với bạn?',
      suggestedMood: 'reflective',
      icon: '🧘'
    },
    {
      id: 21,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Bầu trời ngoài ô cửa sổ lúc này trông như thế nào? Bạn đã dừng lại ngắm mây trời bao nhiêu giây hôm nay?',
      suggestedMood: 'serene',
      icon: '☁️'
    },
    {
      id: 22,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Điều gì đã thu hút trọn vẹn sự chú ý của bạn hôm nay mà không liên quan đến màn hình điện thoại?',
      suggestedMood: 'reflective',
      icon: '👁️'
    },
    {
      id: 23,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Một cuộc trò chuyện nào hôm nay khiến bạn cảm thấy được lắng nghe và thực sự thấu cảm?',
      suggestedMood: 'cozy',
      icon: '💬'
    },
    {
      id: 24,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Khoảnh khắc tĩnh lặng nhất trong ngày của bạn diễn ra vào lúc nào và bạn cảm thấy ra sao?',
      suggestedMood: 'serene',
      icon: '🌌'
    },
    {
      id: 25,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Hôm nay bạn đã đưa ra quyết định nhỏ nào dựa trên sự lắng nghe tiếng lòng của chính mình?',
      suggestedMood: 'reflective',
      icon: '🧭'
    },
    {
      id: 26,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Một mùi hương, một ngọn gió hay một cảm giác xúc giác nào đã neo giữ bạn lại với hiện tại?',
      suggestedMood: 'serene',
      icon: '🍂'
    },
    {
      id: 27,
      pillar: 'presence',
      pillarName: 'Hiện diện & Chiêm nghiệm',
      text: 'Nếu tâm trí bạn là một mặt hồ, mặt hồ lúc này đang gợn sóng hay phẳng lặng trong veo?',
      suggestedMood: 'reflective',
      icon: '🌊'
    },

    // Pillar 4: Ước vọng & Năng lượng (Hope & Inner Growth)
    {
      id: 28,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Hành động tử tế nhỏ bé nào bạn đã dành cho người khác hoặc cho chính bản thân mình hôm nay?',
      suggestedMood: 'energetic',
      icon: '⚡'
    },
    {
      id: 29,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Hôm nay bạn đã học được một điều gì mới mẻ về cuộc sống hay về chính tâm hồn mình?',
      suggestedMood: 'reflective',
      icon: '🌱'
    },
    {
      id: 30,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Bạn muốn gửi gắm năng lượng và lời chúc lành nào cho bình minh ngày mai?',
      suggestedMood: 'energetic',
      icon: '🌅'
    },
    {
      id: 31,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Điều gì đã tiếp thêm dũng khí cho bạn để bước qua một thử thách nhỏ hôm nay?',
      suggestedMood: 'energetic',
      icon: '🔥'
    },
    {
      id: 32,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Một mục tiêu hay giấc mơ nhỏ bé nào đang nhen nhóm khiến trái tim bạn rạo rực?',
      suggestedMood: 'energetic',
      icon: '⭐'
    },
    {
      id: 33,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Hôm nay bạn đã làm được điều gì khiến phiên bản tương lai của bạn phải thầm cảm ơn?',
      suggestedMood: 'cozy',
      icon: '🎯'
    },
    {
      id: 34,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Nếu được gửi một lời khuyên chân thành cho chính mình vào sáng mai, bạn sẽ nhắn nhủ điều gì?',
      suggestedMood: 'reflective',
      icon: '💌'
    },
    {
      id: 35,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Nguồn năng lượng tích cực nào hôm nay bạn muốn tiếp tục nuôi dưỡng trong những ngày tới?',
      suggestedMood: 'energetic',
      icon: '☀️'
    },
    {
      id: 36,
      pillar: 'growth',
      pillarName: 'Ước vọng & Năng lượng',
      text: 'Hãy viết ra một câu khẳng định tích cực để khép lại ngày hôm nay bằng sự bình yên.',
      suggestedMood: 'serene',
      icon: '🌸'
    }
  ];

  const KokoroZenPrompt = {
    prompts: ZEN_PROMPTS,

    /**
     * Get Local Date in YYYY-MM-DD format based on client local time (Avoids UTC rollover trap)
     */
    getLocalDateString(date = new Date()) {
      const y = date.getFullYear();
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const d = String(date.getDate()).padStart(2, '0');
      return `${y}-${m}-${d}`;
    },

    /**
     * Deterministic 32-bit hash function for string
     */
    hashDate(dateStr) {
      let hash = 0;
      if (!dateStr || dateStr.length === 0) return 0;
      for (let i = 0; i < dateStr.length; i++) {
        hash = (hash << 5) - hash + dateStr.charCodeAt(i);
        hash |= 0;
      }
      return Math.abs(hash);
    },

    _getStorage(key) {
      try {
        if (typeof localStorage !== 'undefined') {
          return localStorage.getItem(key);
        }
      } catch (e) {
        console.warn('[ZenPrompts] localStorage read access error:', e);
      }
      return null;
    },

    _setStorage(key, val) {
      try {
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(key, val);
        }
      } catch (e) {
        console.warn('[ZenPrompts] localStorage write access error:', e);
      }
    },

    _removeStorage(key) {
      try {
        if (typeof localStorage !== 'undefined') {
          localStorage.removeItem(key);
        }
      } catch (e) {
        console.warn('[ZenPrompts] localStorage remove access error:', e);
      }
    },

    /**
     * Return today's deterministic prompt or user's shuffled active prompt
     */
    getDailyPrompt(dateStr = null) {
      const today = dateStr || this.getLocalDateString();
      const activeId = this._getStorage(`kokoro_zen_active_${today}`);
      if (activeId) {
        const found = this.prompts.find((p) => p.id === Number(activeId));
        if (found) return found;
      }
      const idx = this.hashDate(today) % this.prompts.length;
      return this.prompts[idx];
    },

    /**
     * Return a random prompt different from currentId, and persist it for today
     */
    getRandomPrompt(currentId = null) {
      const candidates = this.prompts.filter((p) => p.id !== currentId);
      const chosen = candidates[Math.floor(Math.random() * candidates.length)] || this.prompts[0];
      const today = this.getLocalDateString();
      this._setStorage(`kokoro_zen_active_${today}`, String(chosen.id));
      return chosen;
    },

    /**
     * Check if prompt card is dismissed today
     */
    isDismissed(dateStr = null) {
      const today = dateStr || this.getLocalDateString();
      return this._getStorage(`kokoro_zen_dismissed_${today}`) === 'true';
    },

    /**
     * Set dismissal state for today
     */
    setDismissed(dateStr = null, val = true) {
      const today = dateStr || this.getLocalDateString();
      if (val) {
        this._setStorage(`kokoro_zen_dismissed_${today}`, 'true');
      } else {
        this._removeStorage(`kokoro_zen_dismissed_${today}`);
      }
    }
  };

  // Export to window
  window.KokoroZenPrompt = KokoroZenPrompt;

  // Also support CommonJS/Node module environment for testing
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ZEN_PROMPTS, KokoroZenPrompt };
  }
})();
