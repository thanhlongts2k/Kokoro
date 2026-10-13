"""
Kokoro (心) Category Repository
Persistence abstraction isolating database operations for categories/mood taxonomy.
Complies with AGENTS.md Layer Isolation rules.
"""

from typing import List, Optional
from app.database import get_cursor
from app.schemas.category import CategoryDTO, CategoryCreateDTO, CategoryUpdateDTO
from app.exceptions import CategoryDuplicateError, CategoryNotFoundError


class CategoryRepository:
    """DAO for managing categories and mood mappings in PostgreSQL."""

    @classmethod
    def get_categories(cls, user_id: int) -> List[CategoryDTO]:
        """
        Retrieve all categories for a user with calculated usage_count.
        Matches entries by category_id or legacy mood name.
        """
        with get_cursor() as cur:
            cur.execute("""
                SELECT c.id, c.user_id, c.name, c.icon, c.color, c.sort_order, c.created_at,
                       COUNT(DISTINCT e.id) AS usage_count
                FROM categories c
                LEFT JOIN entries e ON (
                    e.user_id = %s AND (
                        e.category_id = c.id
                        OR LOWER(e.mood) = LOWER(c.name)
                        OR (c.name = 'Bình yên' AND e.mood = 'serene')
                        OR (c.name = 'Ấm áp' AND e.mood = 'cozy')
                        OR (c.name = 'Chiêm nghiệm' AND e.mood = 'reflective')
                        OR (c.name = 'Biết ơn' AND e.mood = 'grateful')
                        OR (c.name = 'Năng lượng' AND e.mood = 'energetic')
                    )
                )
                WHERE c.user_id = %s
                GROUP BY c.id
                ORDER BY c.sort_order ASC, c.id ASC;
            """, (user_id, user_id))
            rows = cur.fetchall()
            categories = []
            for r in rows:
                created_str = r["created_at"].isoformat() if r.get("created_at") else None
                categories.append(CategoryDTO(
                    id=r["id"],
                    user_id=r["user_id"],
                    name=r["name"],
                    icon=r["icon"],
                    color=r["color"],
                    sort_order=r["sort_order"],
                    created_at=created_str,
                    usage_count=r["usage_count"]
                ))
            return categories

    @classmethod
    def get_by_id(cls, cat_id: int, user_id: int) -> Optional[CategoryDTO]:
        """Retrieve a category by id owned by user."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, name, icon, color, sort_order, created_at
                FROM categories 
                WHERE id = %s AND user_id = %s;
            """, (cat_id, user_id))
            r = cur.fetchone()
            if not r:
                return None
            created_str = r["created_at"].isoformat() if r.get("created_at") else None
            return CategoryDTO(
                id=r["id"],
                user_id=r["user_id"],
                name=r["name"],
                icon=r["icon"],
                color=r["color"],
                sort_order=r["sort_order"],
                created_at=created_str,
                usage_count=0
            )

    find_by_id = get_by_id

    @classmethod
    def find_by_name(cls, user_id: int, name: str) -> Optional[CategoryDTO]:
        """Find category by name owned by user (case-insensitive)."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, name, icon, color, sort_order, created_at
                FROM categories
                WHERE user_id = %s AND LOWER(name) = LOWER(%s);
            """, (user_id, name))
            r = cur.fetchone()
            if not r:
                return None
            created_str = r["created_at"].isoformat() if r.get("created_at") else None
            return CategoryDTO(
                id=r["id"],
                user_id=r["user_id"],
                name=r["name"],
                icon=r["icon"],
                color=r["color"],
                sort_order=r["sort_order"],
                created_at=created_str,
                usage_count=0
            )

    @classmethod
    def check_duplicate_name(cls, user_id: int, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if category name already exists for user (case-insensitive)."""
        with get_cursor() as cur:
            if exclude_id is not None:
                cur.execute(
                    "SELECT id FROM categories WHERE user_id = %s AND LOWER(name) = LOWER(%s) AND id != %s;",
                    (user_id, name, exclude_id)
                )
            else:
                cur.execute(
                    "SELECT id FROM categories WHERE user_id = %s AND LOWER(name) = LOWER(%s);",
                    (user_id, name)
                )
            return cur.fetchone() is not None

    @classmethod
    def create_category(cls, user_id: int, dto: CategoryCreateDTO) -> CategoryDTO:
        """Create a new category in PostgreSQL."""
        if cls.check_duplicate_name(user_id, dto.name):
            raise CategoryDuplicateError(dto.name)

        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO categories (user_id, name, icon, color, sort_order)
                VALUES (%s, %s, %s, %s, COALESCE((SELECT MAX(sort_order) + 1 FROM categories WHERE user_id = %s), 0))
                RETURNING id, user_id, name, icon, color, sort_order, created_at;
            """, (user_id, dto.name, dto.icon, dto.color, user_id))
            r = cur.fetchone()
            created_str = r["created_at"].isoformat() if r.get("created_at") else None
            return CategoryDTO(
                id=r["id"],
                user_id=r["user_id"],
                name=r["name"],
                icon=r["icon"],
                color=r["color"],
                sort_order=r["sort_order"],
                created_at=created_str,
                usage_count=0
            )

    @classmethod
    def update_category(cls, user_id: int, cat_id: int, dto: CategoryUpdateDTO, old_name: Optional[str] = None) -> CategoryDTO:
        """Update category and synchronize entries.mood if name changed."""
        if old_name is None:
            existing = cls.get_by_id(cat_id, user_id)
            if existing:
                old_name = existing.name

        with get_cursor() as cur:
            cur.execute("""
                UPDATE categories
                SET name = COALESCE(%s, name),
                    icon = COALESCE(%s, icon),
                    color = COALESCE(%s, color),
                    sort_order = COALESCE(%s, sort_order)
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, name, icon, color, sort_order, created_at;
            """, (dto.name, dto.icon, dto.color, dto.sort_order, cat_id, user_id))
            r = cur.fetchone()

            # Sync entries.mood if name changed
            if dto.name and dto.name != old_name:
                cur.execute("""
                    UPDATE entries 
                    SET mood = %s 
                    WHERE user_id = %s AND (category_id = %s OR mood = %s);
                """, (dto.name, user_id, cat_id, old_name))

            # Calculate current usage count
            cur.execute("""
                SELECT COUNT(DISTINCT id) AS count FROM entries 
                WHERE user_id = %s AND (
                    category_id = %s 
                    OR LOWER(mood) = LOWER(%s)
                );
            """, (user_id, cat_id, r["name"]))
            usage_cnt = cur.fetchone()["count"]

            created_str = r["created_at"].isoformat() if r.get("created_at") else None
            return CategoryDTO(
                id=r["id"],
                user_id=r["user_id"],
                name=r["name"],
                icon=r["icon"],
                color=r["color"],
                sort_order=r["sort_order"],
                created_at=created_str,
                usage_count=usage_cnt
            )

    @classmethod
    def delete_category(cls, user_id: int, cat_id: int) -> Optional[str]:
        """Delete category, reassign related entries to NULL / 'serene', and return deleted name."""
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories WHERE id = %s AND user_id = %s;", (cat_id, user_id))
            r = cur.fetchone()
            if not r:
                return None
            cat_name = r["name"]

            cur.execute("""
                UPDATE entries 
                SET category_id = NULL, mood = 'serene' 
                WHERE user_id = %s AND (category_id = %s OR mood = %s);
            """, (user_id, cat_id, cat_name))

            cur.execute("DELETE FROM categories WHERE id = %s AND user_id = %s;", (cat_id, user_id))
            return cat_name
