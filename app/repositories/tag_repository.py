"""
Kokoro (心) Tag Repository
Persistence abstraction isolating database operations for tags.
Complies with AGENTS.md Layer Isolation rules.
"""

from typing import List, Optional, Tuple, Union
from app.database import get_cursor
from app.schemas.tag import TagDTO, TagCreateDTO, TagUpdateDTO


class TagRepository:
    """DAO for managing tags and tag-entry associations in PostgreSQL."""

    @classmethod
    def get_tags(cls, user_id: int) -> List[TagDTO]:
        """Retrieve tags strictly scoped to authenticated user with usage counts."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.id, t.name, COUNT(DISTINCT e.id) AS usage_count
                FROM tags t
                LEFT JOIN entry_tags et ON t.id = et.tag_id
                LEFT JOIN entries e ON et.entry_id = e.id AND e.user_id = %s
                WHERE t.user_id = %s
                GROUP BY t.id, t.name
                ORDER BY usage_count DESC, t.name ASC;
            """, (user_id, user_id))
            rows = cur.fetchall()
            return [
                TagDTO(id=r["id"], name=r["name"], usage_count=r["usage_count"])
                for r in rows
            ]

    @classmethod
    def get_by_id(cls, tag_id: int, user_id: int) -> Optional[TagDTO]:
        """Retrieve tag by id owned by user."""
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            r = cur.fetchone()
            if not r:
                return None
            return TagDTO(id=r["id"], name=r["name"], usage_count=0)

    find_by_id = get_by_id

    @classmethod
    def create_tag(cls, user_id: int, name: Union[str, TagCreateDTO]) -> TagDTO:
        """Create or return existing tag for user."""
        if isinstance(name, TagCreateDTO):
            raw_name = name.name
        else:
            raw_name = str(name)

        clean_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"
        clean_name = "#" + clean_name.lstrip("#").strip()

        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO tags (user_id, name)
                VALUES (%s, %s)
                ON CONFLICT (user_id, name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id, name, created_at;
            """, (user_id, clean_name))
            r = cur.fetchone()

            cur.execute("SELECT COUNT(DISTINCT entry_id) AS usage_count FROM entry_tags WHERE tag_id = %s;", (r["id"],))
            usage_cnt = cur.fetchone()["usage_count"]

            created_str = r["created_at"].isoformat() if r.get("created_at") else None
            return TagDTO(id=r["id"], name=r["name"], usage_count=usage_cnt, created_at=created_str)

    @classmethod
    def rename_or_merge_tag(cls, user_id: int, tag_id: int, new_name: Union[str, TagUpdateDTO]) -> Optional[Tuple[int, str]]:
        """
        Rename an existing tag. If new name already exists, merges associations
        into target tag and removes source tag. Returns (final_id, new_name) or None if tag not found.
        """
        if isinstance(new_name, TagUpdateDTO):
            raw_name = new_name.name
        else:
            raw_name = str(new_name)

        clean_name = raw_name if raw_name.startswith("#") else f"#{raw_name}"

        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            tag_row = cur.fetchone()
            if not tag_row:
                return None

            cur.execute("SELECT id FROM tags WHERE user_id = %s AND name = %s AND id != %s;", (user_id, clean_name, tag_id))
            target_row = cur.fetchone()

            if target_row:
                target_id = target_row["id"]
                cur.execute("""
                    INSERT INTO entry_tags (entry_id, tag_id)
                    SELECT entry_id, %s FROM entry_tags WHERE tag_id = %s
                    ON CONFLICT (entry_id, tag_id) DO NOTHING;
                """, (target_id, tag_id))
                cur.execute("DELETE FROM entry_tags WHERE tag_id = %s;", (tag_id,))
                cur.execute("DELETE FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
                final_id = target_id
            else:
                cur.execute("UPDATE tags SET name = %s WHERE id = %s AND user_id = %s;", (clean_name, tag_id, user_id))
                final_id = tag_id

            return final_id, clean_name

    @classmethod
    def update_tag(cls, user_id: int, tag_id: int, new_name: Union[str, TagUpdateDTO]) -> Optional[TagDTO]:
        """Update/merge tag and return TagDTO."""
        res = cls.rename_or_merge_tag(user_id, tag_id, new_name)
        if not res:
            return None
        final_id, name = res
        return TagDTO(id=final_id, name=name, usage_count=0)

    @classmethod
    def delete_tag(cls, user_id: int, tag_id: int) -> bool:
        """Delete tag and all its associations. Returns True if deleted, False if not found."""
        with get_cursor() as cur:
            cur.execute("SELECT id FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            if not cur.fetchone():
                return False

            cur.execute("DELETE FROM entry_tags WHERE tag_id = %s;", (tag_id,))
            cur.execute("DELETE FROM tags WHERE id = %s AND user_id = %s;", (tag_id, user_id))
            return True

    @classmethod
    def cleanup_orphan_tags(cls, user_id: int) -> int:
        """Delete all tags with 0 associations for user. Returns deleted count."""
        with get_cursor() as cur:
            cur.execute("""
                DELETE FROM tags
                WHERE user_id = %s
                  AND id NOT IN (
                      SELECT et.tag_id
                      FROM entry_tags et
                      JOIN entries e ON et.entry_id = e.id
                      WHERE e.user_id = %s
                  );
            """, (user_id, user_id))
            return cur.rowcount
