"""
connection.py — Gestionnaire de connexion SQLite thread-safe pour Atlas.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from config import DATABASE_PATH, DB_TIMEOUT


class Database:
    """Gestionnaire de connexion SQLite thread-safe."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self._keeper: Optional[sqlite3.Connection] = None

        if str(self.db_path) == ":memory:":
            memory_uri = "file:atlas_memory?mode=memory&cache=shared"
            self._keeper = sqlite3.connect(memory_uri, uri=True, timeout=DB_TIMEOUT)
            self._keeper.row_factory = sqlite3.Row
            self._keeper.execute("PRAGMA foreign_keys=ON")
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._keeper is not None:
            return self._keeper

        conn = sqlite3.connect(str(self.db_path), timeout=DB_TIMEOUT)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT DEFAULT '',
                    source TEXT DEFAULT '',
                    period TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    language TEXT DEFAULT 'Français',
                    doc_type TEXT DEFAULT 'Texte',
                    date_publication TEXT DEFAULT '',
                    total_pages INTEGER DEFAULT 1,
                    file_path TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tfidf_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id INTEGER NOT NULL,
                    term TEXT NOT NULL,
                    tfidf_value REAL NOT NULL,
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT NOT NULL UNIQUE,
                    document_frequency INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    filters TEXT DEFAULT '{}',
                    result_count INTEGER DEFAULT 0,
                    search_time_ms REAL DEFAULT 0,
                    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS index_stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_documents INTEGER DEFAULT 0,
                    total_chunks INTEGER DEFAULT 0,
                    total_terms INTEGER DEFAULT 0,
                    last_indexed_at TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_tfidf_chunk ON tfidf_index(chunk_id);
                CREATE INDEX IF NOT EXISTS idx_tfidf_term ON tfidf_index(term);
                CREATE INDEX IF NOT EXISTS idx_vocabulary_term ON vocabulary(term);
                CREATE INDEX IF NOT EXISTS idx_history_date ON search_history(searched_at);
            """)
            conn.commit()
        finally:
            if self._keeper is None:
                conn.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._get_connection()
        if self._keeper is not None:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def fetchall(self, query: str, params: tuple = ()) -> list:
        conn = self._get_connection()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            if self._keeper is None:
                conn.close()

    def fetchone(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        try:
            return conn.execute(query, params).fetchone()
        finally:
            if self._keeper is None:
                conn.close()

    def executemany(self, query: str, data: list):
        conn = self._get_connection()
        try:
            conn.executemany(query, data)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
