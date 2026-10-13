import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from app.config import Config

logger = logging.getLogger("kokoro.database")

# Initialize Threaded Connection Pool
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
        )
    return _pool

@contextmanager
def get_db():
    """Context manager for acquiring a database connection from the pool."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except (psycopg2.Error, Exception) as err:
        conn.rollback()
        logger.error("[Database] Giao dịch bị rollback do lỗi: %s", err, exc_info=True)
        raise
    finally:
        pool.putconn(conn)

@contextmanager
def get_cursor(cursor_factory=RealDictCursor):
    """Context manager for acquiring a database cursor returning dict-like rows."""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()

def check_db_connection() -> tuple[bool, str]:
    """
    Check database connectivity health without exposing cursors or raw SQL to callers.
    Returns (True, "connected") if healthy, or (False, error_message) on failure.
    """
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1;")
        return True, "connected"
    except psycopg2.Error as e:
        logger.error("Database connection check failed (psycopg2): %s", e)
        return False, str(e)
    except Exception as e:
        logger.exception("Database connection check failed (unexpected): %s", e)
        return False, str(e)

DEFAULT_CATEGORIES = [
    {"name": "Bình yên", "icon": "🌸", "color": "#ec4899", "sort_order": 0},
    {"name": "Ấm áp", "icon": "☕", "color": "#f59e0b", "sort_order": 1},
    {"name": "Chiêm nghiệm", "icon": "🌙", "color": "#8b5cf6", "sort_order": 2},
    {"name": "Biết ơn", "icon": "🍵", "color": "#10b981", "sort_order": 3},
    {"name": "Năng lượng", "icon": "⚡", "color": "#3b82f6", "sort_order": 4},
]

def seed_default_categories(user_id: int, cur=None):
    """Seed initial 5 default categories for a user if they have none."""
    query = """
        INSERT INTO categories (user_id, name, icon, color, sort_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, name) DO NOTHING;
    """
    if cur is not None:
        for cat in DEFAULT_CATEGORIES:
            cur.execute(query, (user_id, cat["name"], cat["icon"], cat["color"], cat["sort_order"]))
    else:
        with get_db() as conn:
            with conn.cursor() as local_cur:
                for cat in DEFAULT_CATEGORIES:
                    local_cur.execute(query, (user_id, cat["name"], cat["icon"], cat["color"], cat["sort_order"]))

def seed_mock_users_for_testing():
    """Explicitly seed mock development users Aria Tanaka & Kenji Sato for automated test suites."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO users (google_id, email, name, avatar_url)
            VALUES 
                ('mock_google_id_001', 'aria.tanaka@kokoro.me', 'Aria Tanaka (心)', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'),
                ('mock_google_id_002', 'kenji.sato@kokoro.me', 'Kenji Sato (Zen)', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80')
            ON CONFLICT (google_id) DO UPDATE 
            SET last_login = CURRENT_TIMESTAMP
            RETURNING id;
            """)
            rows = cur.fetchall()
            for r in rows:
                seed_default_categories(r[0], cur=cur)

def clean_mock_users_after_testing():
    """Remove transient mock development users created for automated test suites."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE google_id LIKE 'mock_%' OR email LIKE '%@kokoro.me';")

def init_db():
    """Initialize PostgreSQL schema with all required tables, indexes, and migrations."""
    schema_sql = """
    -- 1. USERS TABLE
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        google_id VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        avatar_url TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. ENTRIES TABLE
    CREATE TABLE IF NOT EXISTS entries (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title VARCHAR(255),
        content TEXT NOT NULL,
        mood VARCHAR(50) DEFAULT 'serene',
        weather VARCHAR(50) DEFAULT 'sunny',
        entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
        is_pinned BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 3. ENTRY PHOTOS TABLE
    CREATE TABLE IF NOT EXISTS entry_photos (
        id SERIAL PRIMARY KEY,
        entry_id INT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        file_path TEXT NOT NULL,
        thumb_path TEXT NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_size INT NOT NULL,
        width INT,
        height INT,
        sort_order INT DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 4. TAGS TABLE
    CREATE TABLE IF NOT EXISTS tags (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, name)
    );

    -- 5. ENTRY_TAGS M-N TABLE
    CREATE TABLE IF NOT EXISTS entry_tags (
        entry_id INT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        tag_id INT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (entry_id, tag_id)
    );

    -- 6. CATEGORIES TABLE (v1.6.0)
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        icon VARCHAR(50) DEFAULT '📁',
        color VARCHAR(50) DEFAULT '#ec4899',
        sort_order INT DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, name)
    );

    -- MIGRATION: ALTER ENTRIES ADD category_id (v1.6.0)
    ALTER TABLE entries ADD COLUMN IF NOT EXISTS category_id INT REFERENCES categories(id) ON DELETE SET NULL;

    -- INDEXES FOR PERFORMANCE
    CREATE INDEX IF NOT EXISTS idx_entries_user_date ON entries(user_id, entry_date DESC);
    CREATE INDEX IF NOT EXISTS idx_entries_pinned_date ON entries(user_id, is_pinned DESC, entry_date DESC, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_entries_user_mood ON entries(user_id, mood);
    CREATE INDEX IF NOT EXISTS idx_entries_user_cat ON entries(user_id, category_id);
    CREATE INDEX IF NOT EXISTS idx_entry_photos_entry ON entry_photos(entry_id, sort_order ASC);
    CREATE INDEX IF NOT EXISTS idx_tags_user ON tags(user_id);
    CREATE INDEX IF NOT EXISTS idx_entry_tags_tag_id ON entry_tags(tag_id);
    CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id, sort_order ASC);
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)


            # Clean legacy dummy categories ('Đời thường', 'Công việc', 'Tình cảm', 'Du lịch', 'Học tập') that have no entries
            legacy_names = ('Đời thường', 'Công việc', 'Tình cảm', 'Du lịch', 'Học tập')
            cur.execute("""
                DELETE FROM categories 
                WHERE name IN %s 
                  AND id NOT IN (SELECT category_id FROM entries WHERE category_id IS NOT NULL);
            """, (legacy_names,))

            # Seed default 5 moods for all users if missing
            cur.execute("SELECT id FROM users;")
            user_rows = cur.fetchall()
            for u in user_rows:
                uid = u[0] if isinstance(u, (tuple, list)) else u["id"]
                seed_default_categories(uid, cur=cur)

    logger.info("PostgreSQL database tables, indexes, and categories initialized successfully.")

def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
