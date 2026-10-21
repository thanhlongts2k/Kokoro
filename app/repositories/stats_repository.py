"""
Kokoro (心) Statistics Repository
Persistence abstraction isolating database operations for summary analytics and mood metrics.
Complies with AGENTS.md Layer Isolation rules.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.database import get_cursor
from app.schemas.stats import StatsSummaryDTO


class StatsRepository:
    """DAO for computing summary statistics and user streaks in PostgreSQL."""

    @staticmethod
    def calculate_streak_days(entry_dates: list) -> int:
        """Calculate consecutive active writing streak based on distinct dates."""
        if not entry_dates:
            return 0

        today = datetime.now().date()
        date_set = set()
        for d in entry_dates:
            if isinstance(d, datetime):
                date_set.add(d.date())
            elif hasattr(d, "year"):
                date_set.add(d)
            elif isinstance(d, str):
                try:
                    date_set.add(datetime.strptime(d[:10], "%Y-%m-%d").date())
                except ValueError:
                    pass

        if not date_set:
            return 0

        # If wrote today: streak starts today.
        # If didn't write today but wrote yesterday: streak is still active, starting yesterday.
        current_check = today
        if current_check not in date_set:
            current_check = today - timedelta(days=1)
            if current_check not in date_set:
                return 0

        streak = 0
        while current_check in date_set:
            streak += 1
            current_check -= timedelta(days=1)

        return streak

    MOOD_MAP: Dict[str, str] = {
        "serene": "serene", "bình yên": "serene",
        "cozy": "cozy", "ấm áp": "cozy",
        "reflective": "reflective", "chiêm nghiệm": "reflective",
        "grateful": "grateful", "biết ơn": "grateful",
        "energetic": "energetic", "năng lượng": "energetic"
    }

    @classmethod
    def get_stats_summary(cls, user_id: int) -> StatsSummaryDTO:
        """Calculate summary statistics strictly scoped to the authenticated user."""
        with get_cursor() as cur:
            # 1. Total entries
            cur.execute("SELECT count(*) as total FROM entries WHERE user_id = %s;", (user_id,))
            total = cur.fetchone()["total"]

            # 2. Total photos
            cur.execute("""
                SELECT count(*) as total_photos 
                FROM entry_photos ep 
                JOIN entries e ON ep.entry_id = e.id 
                WHERE e.user_id = %s;
            """, (user_id,))
            total_photos = cur.fetchone()["total_photos"]

            # 3. Mood breakdown for 5 standard moods (normalized via MOOD_MAP)
            cur.execute("""
                SELECT e.mood, c.name as category_name, count(*) as count 
                FROM entries e 
                LEFT JOIN categories c ON e.category_id = c.id 
                WHERE e.user_id = %s 
                GROUP BY e.mood, c.name;
            """, (user_id,))
            raw_rows = cur.fetchall()

            raw_moods: Dict[str, int] = {}
            mapped_counts: Dict[str, int] = {
                "serene": 0, "cozy": 0, "reflective": 0, "grateful": 0, "energetic": 0
            }

            for r in raw_rows:
                mood_raw = r.get("mood")
                count = r.get("count", 0)
                if mood_raw:
                    raw_moods[mood_raw] = raw_moods.get(mood_raw, 0) + count

                clean_mood = (mood_raw or "").strip().lower()
                clean_cat = (r.get("category_name") or "").strip().lower()

                target_key = cls.MOOD_MAP.get(clean_mood) or cls.MOOD_MAP.get(clean_cat)
                if target_key and target_key in mapped_counts:
                    mapped_counts[target_key] += count

            all_moods = ["serene", "cozy", "reflective", "grateful", "energetic"]
            mood_breakdown = {}
            for m in all_moods:
                cnt = mapped_counts.get(m, 0)
                pct = round((cnt / total * 100), 1) if total > 0 else 0
                mood_breakdown[m] = {"count": cnt, "percent": pct}

            serene_percent = mood_breakdown["serene"]["percent"]
            combined_mood_counts = {**raw_moods, **mapped_counts}

            # 4. Streak calculation
            cur.execute("""
                SELECT DISTINCT entry_date 
                FROM entries 
                WHERE user_id = %s 
                ORDER BY entry_date DESC;
            """, (user_id,))
            entry_dates = [r["entry_date"] for r in cur.fetchall()]
            streak_days = cls.calculate_streak_days(entry_dates)

            return StatsSummaryDTO(
                total_entries=total,
                total_photos=total_photos,
                streak_days=streak_days,
                serene_percent=serene_percent,
                mood_breakdown=mood_breakdown,
                mood_counts=combined_mood_counts
            )
