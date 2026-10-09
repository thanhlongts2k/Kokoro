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
    except Exception:
        conn.rollback()
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

def init_db():
    """Initialize PostgreSQL schema with all required tables and indexes."""
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

    -- INDEXES FOR PERFORMANCE
    CREATE INDEX IF NOT EXISTS idx_entries_user_date ON entries(user_id, entry_date DESC);
    CREATE INDEX IF NOT EXISTS idx_entries_user_mood ON entries(user_id, mood);
    CREATE INDEX IF NOT EXISTS idx_entry_photos_entry ON entry_photos(entry_id, sort_order ASC);
    CREATE INDEX IF NOT EXISTS idx_tags_user ON tags(user_id);
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)

            # Insert default Mock User for development if MOCK_AUTH is enabled
            if Config.MOCK_AUTH:
                cur.execute("""
                INSERT INTO users (google_id, email, name, avatar_url)
                VALUES ('mock_google_id_001', 'aria.tanaka@kokoro.me', 'Aria Tanaka (心)', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80')
                ON CONFLICT (google_id) DO UPDATE 
                SET last_login = CURRENT_TIMESTAMP;
                """)

    logger.info("PostgreSQL database tables and indexes initialized successfully.")

def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
