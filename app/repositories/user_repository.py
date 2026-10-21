"""
Kokoro (心) User Repository
Persistence abstraction isolating database operations for users and authentication.
Complies with AGENTS.md Layer Isolation and Strict Typing rules.
"""

from typing import List, Optional
from psycopg2.extras import RealDictCursor
from app.database import get_db, get_cursor, seed_default_categories
from app.schemas.user import UserDTO


class UserRepository:
    """DAO for managing user entities in PostgreSQL."""

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional[UserDTO]:
        """Retrieve full user profile by primary key id."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login
                FROM users
                WHERE id = %s;
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return cls._row_to_dto(dict(row))

    @classmethod
    def get_first_user(cls) -> Optional[UserDTO]:
        """Retrieve the first registered user (used for mock dev login fallback)."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login
                FROM users
                ORDER BY id ASC
                LIMIT 1;
            """)
            row = cur.fetchone()
            if not row:
                return None
            return cls._row_to_dto(dict(row))

    @classmethod
    def list_all_users(cls) -> List[UserDTO]:
        """Retrieve all users in database ordered by id ASC."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login
                FROM users
                ORDER BY id ASC;
            """)
            rows = cur.fetchall()
            return [cls._row_to_dto(dict(r)) for r in rows]

    @classmethod
    def list_mock_users(cls) -> List[UserDTO]:
        """Retrieve ONLY mock development accounts. NEVER leak real/private users."""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login
                FROM users
                WHERE google_id LIKE 'mock_%' OR email LIKE '%@kokoro.me'
                ORDER BY id ASC;
            """)
            rows = cur.fetchall()
            return [cls._row_to_dto(dict(r)) for r in rows]

    @classmethod
    def upsert_user(
        cls,
        google_id: str,
        email: str,
        name: str,
        avatar_url: Optional[str] = None
    ) -> UserDTO:
        """
        Insert or update user details in PostgreSQL upon Google or OAuth login.
        If new user is created, automatically seeds default categories.
        """
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Check if user already exists by google_id or email
                cur.execute("""
                    SELECT id FROM users WHERE google_id = %s OR email = %s LIMIT 1;
                """, (google_id, email))
                existing = cur.fetchone()

                if existing:
                    cur.execute("""
                        UPDATE users 
                        SET google_id = %s,
                            email = %s,
                            name = %s,
                            avatar_url = COALESCE(%s, avatar_url),
                            last_login = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login;
                    """, (google_id, email, name, avatar_url, existing["id"]))
                    user_row = cur.fetchone()
                else:
                    cur.execute("""
                        INSERT INTO users (google_id, email, name, avatar_url, last_login)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login;
                    """, (google_id, email, name, avatar_url))
                    user_row = cur.fetchone()
                    seed_default_categories(user_row["id"], cur=cur)

                return cls._row_to_dto(dict(user_row))

    @classmethod
    def update_profile(
        cls,
        user_id: int,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        custom_avatar_url: Optional[str] = None,
        use_custom_profile: Optional[bool] = None
    ) -> Optional[UserDTO]:
        """
        Update user profile personalization fields (name, bio, custom_avatar_url, use_custom_profile).
        """
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login
                    FROM users WHERE id = %s;
                """, (user_id,))
                current = cur.fetchone()
                if not current:
                    return None

                new_name = name if name is not None else current["name"]
                new_bio = bio if bio is not None else current.get("bio")
                new_custom_avatar = custom_avatar_url if custom_avatar_url is not None else current.get("custom_avatar_url")
                new_use_custom = use_custom_profile if use_custom_profile is not None else current.get("use_custom_profile", False)

                cur.execute("""
                    UPDATE users
                    SET name = %s,
                        bio = %s,
                        custom_avatar_url = %s,
                        use_custom_profile = %s
                    WHERE id = %s
                    RETURNING id, google_id, email, name, avatar_url, bio, custom_avatar_url, use_custom_profile, created_at, last_login;
                """, (new_name, new_bio, new_custom_avatar, new_use_custom, user_id))
                updated = cur.fetchone()
                return cls._row_to_dto(dict(updated))

    @staticmethod
    def _row_to_dto(row: dict) -> UserDTO:
        """Helper to convert database row into UserDTO."""
        created_str = row["created_at"].isoformat() if row.get("created_at") else None
        login_str = row["last_login"].isoformat() if row.get("last_login") else None
        return UserDTO(
            id=row["id"],
            email=row["email"],
            name=row["name"],
            google_id=row.get("google_id"),
            avatar_url=row.get("avatar_url"),
            bio=row.get("bio"),
            custom_avatar_url=row.get("custom_avatar_url"),
            use_custom_profile=bool(row.get("use_custom_profile", False)),
            created_at=created_str,
            last_login=login_str
        )
