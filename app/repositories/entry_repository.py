"""
Kokoro (心) Entry Repository
Persistence abstraction isolating database operations for journal entries, tags, and photos.
Complies with AGENTS.md Layer Isolation and Strict Typing rules.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from app.database import get_db, get_cursor
from app.schemas.entry import EntryCreateDTO, EntryUpdateDTO, EntryFilterDTO

MOOD_LABELS = {
    "serene": "Serene 🌸",
    "cozy": "Cozy ☕",
    "reflective": "Reflective 🌙",
    "grateful": "Grateful 🍵",
    "energetic": "Energetic ⚡",
    "melancholy": "Melancholy 🌧️"
}


class EntryRepository:
    """DAO for managing diary entries and associations in PostgreSQL."""

    @classmethod
    def get_entries(cls, user_id: int, filters: EntryFilterDTO) -> List[Dict[str, Any]]:
        """Retrieve filtered entries strictly scoped to the authenticated user."""
        sql = """
            SELECT e.id, e.user_id, e.category_id,
                   c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
                   e.title, e.content, e.mood, e.weather, 
                   e.entry_date, e.is_pinned, e.created_at, e.updated_at,
                   COALESCE(
                       json_agg(DISTINCT jsonb_build_object(
                           'id', p.id,
                           'url', p.file_path,
                           'thumbUrl', p.thumb_path,
                           'name', p.file_name,
                           'order', p.sort_order
                       )) FILTER (WHERE p.id IS NOT NULL), '[]'
                   ) AS photos,
                   COALESCE(
                       array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{}'
                   ) AS tags
            FROM entries e
            LEFT JOIN categories c ON e.category_id = c.id
            LEFT JOIN entry_photos p ON e.id = p.entry_id
            LEFT JOIN entry_tags et ON e.id = et.entry_id
            LEFT JOIN tags t ON et.tag_id = t.id
            WHERE e.user_id = %s
        """
        params: List[Any] = [user_id]

        if filters.mood and filters.mood != "all":
            sql += " AND e.mood = %s"
            params.append(filters.mood)

        if filters.category_param and filters.category_param != "all":
            if filters.category_param in ("uncategorized", "null", "none"):
                sql += " AND e.category_id IS NULL"
            else:
                try:
                    cat_id = int(filters.category_param)
                    sql += " AND e.category_id = %s"
                    params.append(cat_id)
                except (ValueError, TypeError):
                    pass

        if filters.tag:
            clean_tag = filters.tag if filters.tag.startswith("#") else f"#{filters.tag}"
            sql += " AND t.name = %s"
            params.append(clean_tag)

        if filters.month:
            sql += " AND TO_CHAR(e.entry_date, 'YYYY-MM') = %s"
            params.append(filters.month)

        if filters.search:
            clean_search = filters.search.strip()
            tag_search = clean_search if clean_search.startswith("#") else f"#{clean_search}"
            sql += " AND (e.title ILIKE %s OR e.content ILIKE %s OR t.name ILIKE %s OR t.name ILIKE %s)"
            params.extend([f"%{clean_search}%", f"%{clean_search}%", f"%{clean_search}%", f"%{tag_search}%"])

        sql += """
            GROUP BY e.id, c.id
            ORDER BY e.is_pinned DESC, e.entry_date DESC, e.created_at DESC
        """

        if filters.limit:
            try:
                limit_val = max(1, min(int(filters.limit), 500))
                sql += " LIMIT %s"
                params.append(limit_val)
            except (ValueError, TypeError):
                pass

        if filters.offset:
            try:
                offset_val = max(0, int(filters.offset))
                sql += " OFFSET %s"
                params.append(offset_val)
            except (ValueError, TypeError):
                pass

        with get_cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            return [cls._format_entry_row(dict(r)) for r in rows]

    @classmethod
    def get_by_id(cls, entry_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single entry strictly owned by user."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT e.id, e.user_id, e.category_id,
                       c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
                       e.title, e.content, e.mood, e.weather, 
                       e.entry_date, e.is_pinned, e.created_at, e.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', p.id,
                                   'url', p.file_path,
                                   'thumbUrl', p.thumb_path,
                                   'filename', p.file_name,
                                   'size', p.file_size,
                                   'width', p.width,
                                   'height', p.height
                               ) ORDER BY p.sort_order
                           ) FILTER (WHERE p.id IS NOT NULL), '[]'
                       ) AS photos,
                       COALESCE(
                           array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL), '{}'
                       ) AS tags
                FROM entries e
                LEFT JOIN categories c ON e.category_id = c.id
                LEFT JOIN entry_photos p ON e.id = p.entry_id
                LEFT JOIN entry_tags et ON e.id = et.entry_id
                LEFT JOIN tags t ON et.tag_id = t.id
                WHERE e.id = %s AND e.user_id = %s
                GROUP BY e.id, c.id;
            """, (entry_id, user_id))
            row = cur.fetchone()
            if not row:
                return None
            return cls._format_entry_row(dict(row))

    @classmethod
    def create_entry(
        cls,
        user_id: int,
        dto: EntryCreateDTO,
        processed_photos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new journal entry with tags and photos in a single atomic transaction."""
        entry_date = datetime.now().date()
        if dto.entry_date:
            try:
                entry_date = datetime.strptime(dto.entry_date, "%Y-%m-%d").date()
            except ValueError:
                entry_date = datetime.now().date()

        custom_created_at = None
        if dto.created_at:
            try:
                custom_created_at = datetime.fromisoformat(dto.created_at)
            except Exception:
                custom_created_at = None

        with get_db() as conn:
            with conn.cursor() as cur:
                if custom_created_at:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, is_pinned, created_at, updated_at;
                    """, (
                        user_id,
                        dto.category_id,
                        dto.title or "Khoảnh khắc tĩnh lặng",
                        dto.content,
                        dto.mood,
                        dto.weather,
                        entry_date,
                        custom_created_at,
                        custom_created_at
                    ))
                else:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, is_pinned, created_at, updated_at;
                    """, (
                        user_id,
                        dto.category_id,
                        dto.title or "Khoảnh khắc tĩnh lặng",
                        dto.content,
                        dto.mood,
                        dto.weather,
                        entry_date
                    ))

                row = cur.fetchone()
                entry_id = row[0] if isinstance(row, (tuple, list)) else row["id"]
                is_pinned = row[1] if isinstance(row, (tuple, list)) else row["is_pinned"]
                created_at = row[2] if isinstance(row, (tuple, list)) else row["created_at"]
                updated_at = row[3] if isinstance(row, (tuple, list)) else row["updated_at"]

                # Associate tags
                tag_names = []
                for t in dto.tags:
                    clean = t.strip()
                    if clean:
                        clean_tag = clean if clean.startswith("#") else f"#{clean}"
                        tag_names.append(clean_tag)
                        cur.execute("""
                            INSERT INTO tags (user_id, name)
                            VALUES (%s, %s)
                            ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id;
                        """, (user_id, clean_tag))
                        t_row = cur.fetchone()
                        tag_id = t_row[0] if isinstance(t_row, (tuple, list)) else t_row["id"]
                        cur.execute("""
                            INSERT INTO entry_tags (entry_id, tag_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (entry_id, tag_id))

                # Insert photos
                saved_photos = []
                for idx, p in enumerate(processed_photos):
                    cur.execute("""
                        INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (
                        entry_id,
                        p["file_path"],
                        p["thumb_path"],
                        p["file_name"],
                        p.get("file_size", 0),
                        p.get("width", 0),
                        p.get("height", 0),
                        idx
                    ))
                    p_row = cur.fetchone()
                    photo_id = p_row[0] if isinstance(p_row, (tuple, list)) else p_row["id"]
                    saved_photos.append({
                        "id": photo_id,
                        "url": p["file_path"],
                        "thumbUrl": p["thumb_path"],
                        "name": p["file_name"],
                        "order": idx
                    })

                # Fetch category metadata if assigned
                category_meta = {"name": None, "icon": None, "color": None}
                if dto.category_id:
                    cur.execute("SELECT name, icon, color FROM categories WHERE id = %s;", (dto.category_id,))
                    cat_row = cur.fetchone()
                    if cat_row:
                        if isinstance(cat_row, (tuple, list)):
                            category_meta = {"name": cat_row[0], "icon": cat_row[1], "color": cat_row[2]}
                        else:
                            category_meta = dict(cat_row)

        created_item = {
            "id": entry_id,
            "userId": user_id,
            "categoryId": dto.category_id,
            "category_id": dto.category_id,
            "categoryName": category_meta.get("name"),
            "category_name": category_meta.get("name"),
            "categoryIcon": category_meta.get("icon"),
            "category_icon": category_meta.get("icon"),
            "categoryColor": category_meta.get("color"),
            "category_color": category_meta.get("color"),
            "title": dto.title or "Khoảnh khắc tĩnh lặng",
            "content": dto.content,
            "mood": dto.mood,
            "weather": dto.weather,
            "entryDate": entry_date.isoformat(),
            "entry_date": entry_date.isoformat(),
            "displayDate": f"{entry_date.strftime('%d/%m/%Y')}, {created_at.strftime('%H:%M')}",
            "isPinned": is_pinned,
            "createdAt": created_at.isoformat(),
            "created_at": created_at.isoformat(),
            "updatedAt": updated_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "photos": saved_photos,
            "tags": tag_names,
            "moodLabel": MOOD_LABELS.get(dto.mood, dto.mood.capitalize())
        }
        return created_item

    @classmethod
    def update_entry(
        cls,
        entry_id: int,
        user_id: int,
        dto: EntryUpdateDTO,
        new_photos: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """Update entry metadata, reconcile photos, and synchronize tags."""
        with get_db() as conn:
            with conn.cursor() as cur:
                # 1. Verify ownership
                cur.execute("SELECT id FROM entries WHERE id = %s AND user_id = %s;", (entry_id, user_id))
                if not cur.fetchone():
                    return None, []

                # 2. Check content or remaining photos validation
                cur.execute("SELECT id FROM entry_photos WHERE entry_id = %s;", (entry_id,))
                existing_rows = cur.fetchall()
                existing_pids = [(r[0] if isinstance(r, (tuple, list)) else r["id"]) for r in existing_rows]
                remaining_count = len([pid for pid in existing_pids if pid not in dto.deleted_photo_ids]) + len(new_photos)

                if not dto.content and remaining_count == 0:
                    raise ValueError("Vui lòng nhập nội dung hoặc đính kèm ít nhất một hình ảnh 🌸")

                # 3. Parse dates
                entry_date = datetime.now().date()
                if dto.entry_date:
                    try:
                        entry_date = datetime.strptime(dto.entry_date, "%Y-%m-%d").date()
                    except ValueError:
                        pass

                custom_created_at = None
                if dto.created_at:
                    try:
                        custom_created_at = datetime.fromisoformat(dto.created_at)
                    except Exception:
                        custom_created_at = None

                # 4. Update entry record
                if dto.update_category:
                    if custom_created_at:
                        cur.execute("""
                            UPDATE entries
                            SET category_id = %s, title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, created_at = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (dto.category_id, dto.title, dto.content, dto.mood, dto.weather, entry_date, custom_created_at, entry_id, user_id))
                    else:
                        cur.execute("""
                            UPDATE entries
                            SET category_id = %s, title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (dto.category_id, dto.title, dto.content, dto.mood, dto.weather, entry_date, entry_id, user_id))
                else:
                    if custom_created_at:
                        cur.execute("""
                            UPDATE entries
                            SET title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, created_at = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (dto.title, dto.content, dto.mood, dto.weather, entry_date, custom_created_at, entry_id, user_id))
                    else:
                        cur.execute("""
                            UPDATE entries
                            SET title = %s, content = %s, mood = %s, weather = %s, entry_date = %s, updated_at = NOW()
                            WHERE id = %s AND user_id = %s;
                        """, (dto.title, dto.content, dto.mood, dto.weather, entry_date, entry_id, user_id))

                # 5. Delete removed photos
                deleted_paths: List[str] = []
                if dto.deleted_photo_ids:
                    cur.execute("""
                        SELECT file_path, thumb_path 
                        FROM entry_photos 
                        WHERE entry_id = %s AND id = ANY(%s);
                    """, (entry_id, dto.deleted_photo_ids))
                    for r in cur.fetchall():
                        if isinstance(r, (tuple, list)):
                            if r[0]: deleted_paths.append(r[0])
                            if r[1]: deleted_paths.append(r[1])
                        else:
                            if r.get("file_path"): deleted_paths.append(r["file_path"])
                            if r.get("thumb_path"): deleted_paths.append(r["thumb_path"])

                    cur.execute("""
                        DELETE FROM entry_photos 
                        WHERE entry_id = %s AND id = ANY(%s);
                    """, (entry_id, dto.deleted_photo_ids))

                # 6. Insert new photos
                for p in new_photos:
                    cur.execute("""
                        INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        entry_id,
                        p["file_path"],
                        p["thumb_path"],
                        p["file_name"],
                        p.get("file_size", 0),
                        p.get("width", 0),
                        p.get("height", 0),
                        p.get("sort_order", 0)
                    ))

                # 7. Update tags
                cur.execute("DELETE FROM entry_tags WHERE entry_id = %s;", (entry_id,))
                for t in dto.tags:
                    clean = t.strip()
                    if clean:
                        clean_tag = clean if clean.startswith("#") else f"#{clean}"
                        cur.execute("""
                            INSERT INTO tags (user_id, name)
                            VALUES (%s, %s)
                            ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING id;
                        """, (user_id, clean_tag))
                        t_row = cur.fetchone()
                        tag_id = t_row[0] if isinstance(t_row, (tuple, list)) else t_row["id"]
                        cur.execute("""
                            INSERT INTO entry_tags (entry_id, tag_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (entry_id, tag_id))

                # Clean orphaned tags for this user
                cur.execute("""
                    DELETE FROM tags 
                    WHERE user_id = %s 
                      AND id NOT IN (SELECT tag_id FROM entry_tags WHERE tag_id IS NOT NULL);
                """, (user_id,))

        # Return refreshed entry and paths for cleanup
        return cls.get_by_id(entry_id, user_id), deleted_paths

    @classmethod
    def get_photo_paths_for_entry(cls, entry_id: int, user_id: int) -> List[str]:
        """Retrieve all file and thumb paths associated with entry for user."""
        photo_paths = []
        with get_cursor() as cur:
            cur.execute("""
                SELECT p.file_path, p.thumb_path 
                FROM entry_photos p
                JOIN entries e ON p.entry_id = e.id
                WHERE e.id = %s AND e.user_id = %s;
            """, (entry_id, user_id))
            rows = cur.fetchall()
            for r in rows:
                if r["file_path"]:
                    photo_paths.append(r["file_path"])
                if r["thumb_path"]:
                    photo_paths.append(r["thumb_path"])
        return photo_paths

    @classmethod
    def delete_entry(cls, entry_id: int, user_id: int) -> bool:
        """Delete an entry and cleanup orphaned tags for user."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM entries WHERE id = %s AND user_id = %s RETURNING id;", (entry_id, user_id))
                deleted = cur.fetchone()
                if not deleted:
                    return False

                cur.execute("""
                    DELETE FROM tags 
                    WHERE user_id = %s 
                      AND id NOT IN (SELECT tag_id FROM entry_tags WHERE tag_id IS NOT NULL);
                """, (user_id,))
                return True

    @classmethod
    def toggle_pin(cls, entry_id: int, user_id: int) -> Optional[bool]:
        """Toggle is_pinned status of an entry."""
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE entries 
                    SET is_pinned = NOT is_pinned, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    RETURNING id, is_pinned;
                """, (entry_id, user_id))
                res = cur.fetchone()
                if not res:
                    return None
                is_pinned = res[1] if isinstance(res, (tuple, list)) else res["is_pinned"]
                return is_pinned

    @classmethod
    def export_data(cls, user_id: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Retrieve all categories and entries for full backup export."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, name, icon, color, sort_order
                FROM categories
                WHERE user_id = %s
                ORDER BY sort_order ASC, id ASC;
            """, (user_id,))
            cat_rows = cur.fetchall()
            categories_list = [dict(c) for c in cat_rows]

            cur.execute("""
                SELECT e.id, e.category_id,
                       c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
                       e.title, e.content, e.mood, e.weather,
                       e.entry_date, e.is_pinned, e.created_at, e.updated_at,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'id', ep.id,
                                   'file_path', ep.file_path,
                                   'thumb_path', ep.thumb_path,
                                   'file_name', ep.file_name,
                                   'file_size', ep.file_size,
                                   'width', ep.width,
                                   'height', ep.height,
                                   'sort_order', ep.sort_order
                               ) ORDER BY ep.sort_order
                           ) FILTER (WHERE ep.id IS NOT NULL), '[]'
                       ) AS photos
                FROM entries e
                LEFT JOIN categories c ON e.category_id = c.id
                LEFT JOIN entry_photos ep ON e.id = ep.entry_id
                WHERE e.user_id = %s
                GROUP BY e.id, c.id
                ORDER BY e.entry_date DESC, e.id DESC;
            """, (user_id,))
            raw_entries = cur.fetchall()

            cur.execute("""
                SELECT et.entry_id, t.name as tag_name
                FROM entry_tags et
                JOIN tags t ON et.tag_id = t.id
                JOIN entries e ON et.entry_id = e.id
                WHERE e.user_id = %s;
            """, (user_id,))
            tag_rows = cur.fetchall()

        tag_map: Dict[int, List[str]] = {}
        for tr in tag_rows:
            tag_map.setdefault(tr["entry_id"], []).append(tr["tag_name"])

        entries_list = []
        for r in raw_entries:
            item = dict(r)
            if item.get("entry_date"):
                item["entry_date"] = str(item["entry_date"])
            if item.get("created_at"):
                item["created_at"] = item["created_at"].isoformat()
            if item.get("updated_at"):
                item["updated_at"] = item["updated_at"].isoformat()
            item["tags"] = tag_map.get(item["id"], [])
            entries_list.append(item)

        return categories_list, entries_list

    @classmethod
    def import_data(
        cls,
        user_id: int,
        raw_cats: List[Dict[str, Any]],
        entries_to_import: List[Dict[str, Any]]
    ) -> int:
        """Reconcile categories and restore backup entries."""
        imported_count = 0
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories WHERE user_id = %s;", (user_id,))
            existing_cats = {r["name"]: r["id"] for r in cur.fetchall()}

            cat_id_mapping = {}
            cat_name_mapping = {}

            if raw_cats:
                for cat in raw_cats:
                    cat_name = (cat.get("name") or "").strip()
                    if not cat_name:
                        continue
                    old_id = cat.get("id")
                    icon = cat.get("icon") or "📁"
                    color = cat.get("color") or "#ec4899"
                    sort_order = cat.get("sort_order") if cat.get("sort_order") is not None else 0

                    if cat_name in existing_cats:
                        new_cat_id = existing_cats[cat_name]
                    else:
                        cur.execute("SELECT id FROM categories WHERE user_id = %s AND name = %s;", (user_id, cat_name))
                        found_cat = cur.fetchone()
                        if found_cat:
                            new_cat_id = found_cat["id"]
                        else:
                            cur.execute("""
                                INSERT INTO categories (user_id, name, icon, color, sort_order)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (user_id, name) DO UPDATE SET icon = EXCLUDED.icon, color = EXCLUDED.color
                                RETURNING id;
                            """, (user_id, cat_name, icon, color, sort_order))
                            new_cat_id = cur.fetchone()["id"]
                        existing_cats[cat_name] = new_cat_id

                    if old_id is not None:
                        cat_id_mapping[old_id] = new_cat_id
                    cat_name_mapping[cat_name] = new_cat_id

            for item in entries_to_import:
                title = item.get("title") or "Nhật ký không tên"
                content = item.get("content") or ""
                mood = item.get("mood") or "serene"
                weather = item.get("weather") or "sunny"
                entry_date = item.get("entry_date") or datetime.now().date().isoformat()
                is_pinned = bool(item.get("is_pinned", False))

                custom_created_at = None
                if item.get("created_at"):
                    try:
                        custom_created_at = datetime.fromisoformat(item["created_at"])
                    except Exception:
                        custom_created_at = None

                custom_updated_at = None
                if item.get("updated_at"):
                    try:
                        custom_updated_at = datetime.fromisoformat(item["updated_at"])
                    except Exception:
                        custom_updated_at = None

                old_cat_id = item.get("category_id")
                cat_name = (item.get("category_name") or "").strip()
                resolved_cat_id = None

                if old_cat_id is not None and old_cat_id in cat_id_mapping:
                    resolved_cat_id = cat_id_mapping[old_cat_id]
                elif cat_name and cat_name in cat_name_mapping:
                    resolved_cat_id = cat_name_mapping[cat_name]
                elif cat_name and cat_name in existing_cats:
                    resolved_cat_id = existing_cats[cat_name]
                elif old_cat_id is not None and old_cat_id in existing_cats.values():
                    resolved_cat_id = old_cat_id

                if custom_created_at:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, is_pinned, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    """, (user_id, resolved_cat_id, title, content, mood, weather, entry_date, is_pinned, custom_created_at, custom_updated_at or custom_created_at))
                else:
                    cur.execute("""
                        INSERT INTO entries (user_id, category_id, title, content, mood, weather, entry_date, is_pinned, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id;
                    """, (user_id, resolved_cat_id, title, content, mood, weather, entry_date, is_pinned))

                new_entry_id = cur.fetchone()["id"]
                imported_count += 1

                tags = item.get("tags") or []
                for t in tags:
                    tag_name = t.strip()
                    if not tag_name.startswith("#"):
                        tag_name = f"#{tag_name}"
                    cur.execute("""
                        INSERT INTO tags (user_id, name)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id;
                    """, (user_id, tag_name))
                    tag_id = cur.fetchone()["id"]
                    cur.execute("""
                        INSERT INTO entry_tags (entry_id, tag_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (new_entry_id, tag_id))

                photos = item.get("photos") or []
                for p in photos:
                    file_path = p.get("file_path")
                    thumb_path = p.get("thumb_path")
                    if file_path:
                        cur.execute("""
                            INSERT INTO entry_photos (entry_id, file_path, thumb_path, file_name, file_size, width, height, sort_order)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            new_entry_id,
                            file_path,
                            thumb_path or file_path,
                            p.get("file_name", "photo.webp"),
                            p.get("file_size", 0),
                            p.get("width", 0),
                            p.get("height", 0),
                            p.get("sort_order", 0)
                        ))

        return imported_count

    @staticmethod
    def _format_entry_row(entry: dict) -> dict:
        """Enrich entry dict with ISO dates, displayDate, camelCase aliases and moodLabel."""
        if entry.get("entry_date"):
            d = entry["entry_date"]
            created = entry.get("created_at")
            time_str = created.strftime("%H:%M") if created and hasattr(created, "strftime") else "08:00"
            date_str = d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else str(d)
            entry["displayDate"] = f"{date_str}, {time_str}"
            entry["entryDate"] = d.isoformat() if hasattr(d, "isoformat") else str(d)
            entry["entry_date"] = entry["entryDate"]

        if entry.get("created_at"):
            c = entry["created_at"]
            entry["createdAt"] = c.isoformat() if hasattr(c, "isoformat") else str(c)
            entry["created_at"] = entry["createdAt"]

        if entry.get("updated_at"):
            u = entry["updated_at"]
            entry["updatedAt"] = u.isoformat() if hasattr(u, "isoformat") else str(u)
            entry["updated_at"] = entry["updatedAt"]

        entry["categoryId"] = entry.get("category_id")
        entry["categoryName"] = entry.get("category_name")
        entry["categoryIcon"] = entry.get("category_icon")
        entry["categoryColor"] = entry.get("category_color")

        mood = entry.get("mood", "serene")
        entry["moodLabel"] = MOOD_LABELS.get(mood, mood.capitalize() if mood else "Serene 🌸")
        return entry
