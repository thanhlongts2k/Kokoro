"""
Kokoro (心) In-Memory Mock Database Engine
Provides transparent PostgreSQL emulation via SQLite for automated testing,
CI/CD environments, and offline development when PostgreSQL is unavailable.
"""

import sqlite3
import json
import re
from datetime import datetime, date


class Row(dict):
    """Dual-access row wrapper supporting both r['id'] and r[0]."""
    def __init__(self, data, cols):
        super().__init__(data)
        self._cols = cols
        self._values = [data[c] for c in cols]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    def get(self, key, default=None):
        if isinstance(key, int):
            return self._values[key] if 0 <= key < len(self._values) else default
        return super().get(key, default)


class MockCursor:
    """Cursor that translates PostgreSQL syntax to SQLite and emulates psycopg2 RealDictCursor."""
    def __init__(self, cur, conn):
        self._cur = cur
        self._conn = conn

    def execute(self, sql, params=None):
        clean_sql = sql
        # Replace %s with ?
        clean_sql = re.sub(r'%s', '?', clean_sql)
        # Replace ILIKE with LIKE
        clean_sql = re.sub(r'\bILIKE\b', 'LIKE', clean_sql, flags=re.IGNORECASE)
        # Replace NOW() with CURRENT_TIMESTAMP
        clean_sql = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', clean_sql, flags=re.IGNORECASE)
        # Handle DISTINCT in array_agg and json_agg
        clean_sql = re.sub(r'array_agg\(DISTINCT\s+([^)]+)\)', r'array_agg(\1)', clean_sql, flags=re.IGNORECASE)
        clean_sql = re.sub(r'json_agg\(DISTINCT\s+([^)]+)\)', r'json_agg(\1)', clean_sql, flags=re.IGNORECASE)

        # Handle ANY(?)
        if params is not None and re.search(r'=\s*ANY\s*\(\s*\?\s*\)', clean_sql, flags=re.IGNORECASE):
            clean_sql, params = self._transform_any(clean_sql, params)

        # Handle multiple statements in schema migration (e.g., init_db)
        statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
        if len(statements) > 1 and params is None:
            for s in statements:
                try:
                    if re.match(r'^\s*ALTER\s+TABLE\s+.*ADD\s+COLUMN\s+(IF\s+NOT\s+EXISTS\s+)?(\w+)', s, flags=re.IGNORECASE):
                        continue
                    self._cur.execute(s)
                except sqlite3.OperationalError:
                    pass
            return self

        if params is None:
            try:
                return self._cur.execute(clean_sql)
            except sqlite3.OperationalError:
                if "ALTER TABLE" in clean_sql:
                    return self
                raise
        else:
            p_list = []
            for p in params:
                if isinstance(p, bool):
                    p_list.append(1 if p else 0)
                elif isinstance(p, (datetime, date)):
                    p_list.append(str(p))
                else:
                    p_list.append(p)
            return self._cur.execute(clean_sql, tuple(p_list))

    def _transform_any(self, sql, params):
        pattern = re.compile(r'(\b\w+\b)\s*=\s*ANY\s*\(\s*\?\s*\)', re.IGNORECASE)
        flat = []
        new_sql = sql
        match = pattern.search(new_sql)
        while match:
            prefix = new_sql[:match.start()]
            q_count = prefix.count('?')
            p_val = params[q_count]
            if isinstance(p_val, (list, tuple, set)):
                p_list = list(p_val)
                if p_list:
                    placeholders = ', '.join(['?'] * len(p_list))
                    sub = f"{match.group(1)} IN ({placeholders})"
                else:
                    sub = f"{match.group(1)} IN (NULL)"
            else:
                sub = f"{match.group(1)} = ?"
            new_sql = new_sql[:match.start()] + sub + new_sql[match.end():]
            match = pattern.search(new_sql)

        for p in params:
            if isinstance(p, (list, tuple, set)):
                flat.extend(p)
            else:
                flat.append(p)
        return new_sql, tuple(flat)

    def fetchone(self):
        r = self._cur.fetchone()
        if r is None:
            return None
        cols = [desc[0] for desc in self._cur.description] if self._cur.description else list(dict(r).keys())
        d = dict(r)
        self._format_dict_row(d)
        return Row(d, cols)

    def fetchall(self):
        rows = self._cur.fetchall()
        cols = [desc[0] for desc in self._cur.description] if self._cur.description else []
        result = []
        for r in rows:
            d = dict(r)
            self._format_dict_row(d)
            result.append(Row(d, cols if cols else list(d.keys())))
        return result

    def _format_dict_row(self, d):
        if "photos" in d and isinstance(d["photos"], str):
            try:
                d["photos"] = json.loads(d["photos"])
            except Exception:
                d["photos"] = []
        if "tags" in d and isinstance(d["tags"], str):
            try:
                d["tags"] = json.loads(d["tags"])
            except Exception:
                d["tags"] = []

        for k in ("created_at", "updated_at", "last_login"):
            if k in d and isinstance(d[k], str):
                try:
                    d[k] = datetime.fromisoformat(d[k].replace(" ", "T"))
                except Exception:
                    pass
        if "entry_date" in d and isinstance(d["entry_date"], str):
            try:
                d["entry_date"] = date.fromisoformat(d["entry_date"][:10])
            except Exception:
                pass

    @property
    def rowcount(self):
        return self._cur.rowcount

    @property
    def description(self):
        return self._cur.description

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockConnection:
    """Wrapper around sqlite3.Connection with psycopg2 interface."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, cursor_factory=None):
        return MockCursor(self._conn.cursor(), self._conn)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


class MockPool:
    """ThreadedConnectionPool emulator serving the mock connection."""
    _shared_conn = None

    def __init__(self):
        if MockPool._shared_conn is None:
            MockPool._shared_conn = create_mock_db()

    def getconn(self):
        return MockPool._shared_conn

    def putconn(self, conn):
        pass

    def closeall(self):
        pass


def create_mock_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    class JsonAgg:
        def __init__(self):
            self.items = []
        def step(self, val):
            if val is not None:
                if isinstance(val, str) and (val.startswith('{') or val.startswith('[')):
                    try:
                        self.items.append(json.loads(val))
                    except Exception:
                        self.items.append(val)
                else:
                    self.items.append(val)
        def finalize(self):
            return json.dumps(self.items)

    conn.create_aggregate("json_agg", 1, JsonAgg)

    class ArrayAgg:
        def __init__(self):
            self.items = []
        def step(self, val):
            if val is not None and val not in self.items:
                self.items.append(val)
        def finalize(self):
            return json.dumps(self.items)

    conn.create_aggregate("array_agg", 1, ArrayAgg)

    def json_build_obj(*args):
        d = {}
        for i in range(0, len(args), 2):
            d[args[i]] = args[i+1]
        return json.dumps(d)

    conn.create_function("json_build_object", -1, json_build_obj)
    conn.create_function("jsonb_build_object", -1, json_build_obj)

    def to_char(val, fmt):
        if val is None:
            return None
        val_str = str(val).strip()
        try:
            if " " in val_str:
                dt = datetime.fromisoformat(val_str.split("+")[0])
            else:
                dt = date.fromisoformat(val_str)
            py_fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d").replace("HH24", "%H").replace("MI", "%M").replace("SS", "%S")
            return dt.strftime(py_fmt)
        except Exception:
            return str(val)

    conn.create_function("TO_CHAR", 2, to_char)
    conn.create_function("NOW", 0, lambda: datetime.now().isoformat())

    # Initialize schema
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        avatar_url TEXT,
        bio TEXT DEFAULT '',
        custom_avatar_url TEXT,
        use_custom_profile INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '📁',
        color TEXT DEFAULT '#ec4899',
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, name)
    );
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        title TEXT,
        content TEXT NOT NULL,
        mood TEXT DEFAULT 'serene',
        weather TEXT DEFAULT 'sunny',
        entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
        is_pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS entry_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        file_path TEXT NOT NULL,
        thumb_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        width INTEGER,
        height INTEGER,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, name)
    );
    CREATE TABLE IF NOT EXISTS entry_tags (
        entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
        tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (entry_id, tag_id)
    );
    CREATE INDEX IF NOT EXISTS idx_entries_pinned_date ON entries(user_id, is_pinned, entry_date, created_at);
    CREATE VIEW IF NOT EXISTS pg_indexes AS
    SELECT name AS indexname, tbl_name AS tablename FROM sqlite_master WHERE type = 'index';
    """
    conn.executescript(schema)

    # Seed User 38 and Mock Users
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (id, google_id, email, name, avatar_url)
        VALUES (38, 'google_user_38', 'thanhlongts2k@gmail.com', 'Thành Long', 'https://images.unsplash.com/photo-1534528741775?w=150')
        ON CONFLICT (id) DO NOTHING;
    """)
    cur.execute("""
        INSERT INTO users (id, google_id, email, name, avatar_url)
        VALUES 
            (1, 'mock_google_id_001', 'aria.tanaka@kokoro.me', 'Aria Tanaka (心)', 'https://images.unsplash.com/photo-1534528741775?w=150'),
            (2, 'mock_google_id_002', 'kenji.sato@kokoro.me', 'Kenji Sato (Zen)', 'https://images.unsplash.com/photo-1507003211169?w=150')
        ON CONFLICT (id) DO NOTHING;
    """)

    # Seed initial entry for user 38
    cur.execute("""
        INSERT INTO entries (id, user_id, title, content, mood, weather, entry_date)
        VALUES (1, 38, 'Khoảnh khắc an yên', 'Ghi chú bình yên cùng Kokoro 🌸', 'serene', 'sunny', CURRENT_DATE)
        ON CONFLICT (id) DO NOTHING;
    """)

    # Seed default categories (both modern v1.8.0 names and classic mood names)
    default_cats = [
        ("Bình yên", "🌸", "#ec4899", 0),
        ("Ấm áp", "☕", "#3b82f6", 1),
        ("Chiêm nghiệm", "🌙", "#f43f5e", 2),
        ("Biết ơn", "🍵", "#10b981", 3),
        ("Năng lượng", "⚡", "#8b5cf6", 4),
        ("Đời thường", "🌸", "#ec4899", 5),
        ("Công việc", "💼", "#3b82f6", 6),
        ("Tình cảm", "💌", "#f43f5e", 7),
        ("Du lịch", "✈️", "#10b981", 8),
        ("Học tập", "📚", "#8b5cf6", 9),
    ]
    for uid in (38, 1, 2):
        for name, icon, color, sort_order in default_cats:
            cur.execute("""
                INSERT INTO categories (user_id, name, icon, color, sort_order)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (user_id, name) DO NOTHING;
            """, (uid, name, icon, color, sort_order))

    conn.commit()
    return MockConnection(conn)
