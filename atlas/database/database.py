"""
database.py — Opérations CRUD sur la base SQLite Atlas.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import DATABASE_PATH
from utils.datetime import now_local_str

SCHEMA_SQL = """
-- Table principale des documents historiques
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    author          TEXT    NOT NULL DEFAULT '',
    source          TEXT    NOT NULL DEFAULT '',
    period          TEXT    NOT NULL DEFAULT '',
    region          TEXT    NOT NULL DEFAULT '',
    language        TEXT    NOT NULL DEFAULT 'Français',
    doc_type        TEXT    NOT NULL DEFAULT 'Livre',
    date_publication TEXT   NOT NULL DEFAULT '',
    total_pages     INTEGER NOT NULL DEFAULT 1,
    file_path       TEXT    NOT NULL UNIQUE,
    content         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Table des passages chunkés
CREATE TABLE IF NOT EXISTS chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT    NOT NULL,
    token_count     INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

-- Table de l'index TF-IDF
CREATE TABLE IF NOT EXISTS tfidf_index (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id        INTEGER NOT NULL,
    term            TEXT    NOT NULL,
    tfidf_value     REAL    NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

-- Table du vocabulaire
CREATE TABLE IF NOT EXISTS vocabulary (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    term                TEXT    NOT NULL UNIQUE,
    document_frequency  INTEGER NOT NULL DEFAULT 0
);

-- Table de l'historique des recherches
CREATE TABLE IF NOT EXISTS search_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    query           TEXT    NOT NULL,
    filters         TEXT    NOT NULL DEFAULT '{}',
    result_count    INTEGER NOT NULL DEFAULT 0,
    search_time_ms  REAL    NOT NULL DEFAULT 0.0,
    searched_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Table des statistiques globales
CREATE TABLE IF NOT EXISTS index_stats (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    total_documents INTEGER NOT NULL DEFAULT 0,
    total_chunks    INTEGER NOT NULL DEFAULT 0,
    total_terms     INTEGER NOT NULL DEFAULT 0,
    last_indexed_at TEXT
);

-- Index pour performances
CREATE INDEX IF NOT EXISTS idx_chunks_document    ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_tfidf_chunk        ON tfidf_index(chunk_id);
CREATE INDEX IF NOT EXISTS idx_tfidf_term         ON tfidf_index(term);
CREATE INDEX IF NOT EXISTS idx_vocabulary_term    ON vocabulary(term);
CREATE INDEX IF NOT EXISTS idx_history_date       ON search_history(searched_at);
CREATE INDEX IF NOT EXISTS idx_history_query      ON search_history(query);
"""


def create_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def insert_document(
    conn: sqlite3.Connection,
    titre: str = "",
    contenu: str = "",
    fichier: str = "",
    auteur: str = "",
    source: str = "",
    periode: str = "",
    region: str = "",
    langue: str = "Francais",
    type_doc: str = "Livre",
    date_publication: str = "",
    pages: int = 1,
    title: str = "",
    content: str = "",
    file_path: str = "",
    author: str = "",
    period: str = "",
    doc_type: str = "",
    total_pages: int = 0,
    created_at: Optional[str] = None,
) -> int:
    t_titre = titre or title
    t_contenu = contenu or content
    t_fichier = fichier or file_path
    t_auteur = auteur or author
    t_periode = periode or period
    t_type = type_doc or doc_type or "Livre"
    t_pages = pages or total_pages or 1
    t_created_at = created_at if created_at is not None else now_local_str()

    curseur = conn.execute(
        """
        INSERT INTO documents
            (title, author, source, period, region, language,
             doc_type, date_publication, total_pages, file_path, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (t_titre, t_auteur, source, t_periode, region, langue,
         t_type, date_publication, t_pages, t_fichier, t_contenu, t_created_at),
    )
    conn.commit()
    return curseur.lastrowid


def insert_chunks(
    conn: sqlite3.Connection,
    document_id: int,
    chunks: List[Dict[str, Any]],
) -> List[int]:
    ids = []
    for i, chunk in enumerate(chunks):
        cursor = conn.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, content, token_count)
            VALUES (?, ?, ?, ?)
            """,
            (document_id, i, chunk["content"], chunk.get("token_count", 0)),
        )
        ids.append(cursor.lastrowid)
    conn.commit()
    return ids


def insert_tfidf_entries(
    conn: sqlite3.Connection,
    entries: List[Dict[str, Any]],
) -> None:
    conn.executemany(
        """
        INSERT INTO tfidf_index (chunk_id, term, tfidf_value)
        VALUES (:chunk_id, :term, :tfidf_value)
        """,
        entries,
    )
    conn.commit()


def insert_vocabulary(
    conn: sqlite3.Connection,
    term: str,
    document_frequency: int = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO vocabulary (term, document_frequency)
        VALUES (?, ?)
        ON CONFLICT(term) DO UPDATE SET
            document_frequency = document_frequency + excluded.document_frequency
        """,
        (term, document_frequency),
    )
    conn.commit()


def get_documents(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
    period: Optional[str] = None,
    region: Optional[str] = None,
    author: Optional[str] = None,
) -> List[sqlite3.Row]:
    query = "SELECT * FROM documents WHERE 1=1"
    params: list = []

    if period:
        query += " AND period LIKE ?"
        params.append(f"%{period}%")
    if region:
        query += " AND region LIKE ?"
        params.append(f"%{region}%")
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return conn.execute(query, params).fetchall()


def get_document_by_id(conn: sqlite3.Connection, doc_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()


def get_chunks_by_document(conn: sqlite3.Connection, document_id: int) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
        (document_id,),
    ).fetchall()


def save_search(
    conn: sqlite3.Connection,
    query: str,
    result_count: int,
    search_time_ms: float = 0.0,
    filters: str = "{}",
    searched_at: Optional[str] = None,
) -> int:
    t_searched_at = searched_at if searched_at is not None else now_local_str()
    cursor = conn.execute(
        """
        INSERT INTO search_history (query, filters, result_count, search_time_ms, searched_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (query, filters, result_count, search_time_ms, t_searched_at),
    )
    conn.commit()
    return cursor.lastrowid


def get_search_history(
    conn: sqlite3.Connection,
    limit: int = 50,
    offset: int = 0,
) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()


def get_vocabulary(
    conn: sqlite3.Connection,
    limit: int = 100,
    min_df: int = 1,
) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM vocabulary WHERE document_frequency >= ? ORDER BY document_frequency DESC LIMIT ?",
        (min_df, limit),
    ).fetchall()


def get_index_stats(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM index_stats WHERE id = 1").fetchone()


def update_index_stats(conn: sqlite3.Connection) -> None:
    docs = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
    chunks = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()["cnt"]
    terms = conn.execute("SELECT COUNT(*) as cnt FROM vocabulary").fetchone()["cnt"]
    t_last_indexed = now_local_str()

    conn.execute(
        """
        INSERT INTO index_stats (id, total_documents, total_chunks, total_terms, last_indexed_at)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            total_documents = excluded.total_documents,
            total_chunks    = excluded.total_chunks,
            total_terms     = excluded.total_terms,
            last_indexed_at = excluded.last_indexed_at
        """,
        (docs, chunks, terms, t_last_indexed),
    )
    conn.commit()


def delete_document(conn: sqlite3.Connection, doc_id: int) -> bool:
    cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    return cursor.rowcount > 0


def reset_index(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        DELETE FROM tfidf_index;
        DELETE FROM chunks;
        DELETE FROM vocabulary;
        DELETE FROM index_stats;
    """)
    conn.commit()


def search_documents(
    conn: sqlite3.Connection,
    terms: List[str],
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    placeholders = ",".join("?" for _ in terms)
    rows = conn.execute(
        f"""
        SELECT
            t.chunk_id,
            c.document_id,
            d.title,
            c.content,
            SUM(t.tfidf_value) as score
        FROM tfidf_index t
        JOIN chunks c ON t.chunk_id = c.id
        JOIN documents d ON c.document_id = d.id
        WHERE t.term IN ({placeholders})
        GROUP BY t.chunk_id
        ORDER BY score DESC
        LIMIT ? OFFSET ?
        """,
        (*terms, limit, offset),
    ).fetchall()

    return [
        {
            "chunk_id": r["chunk_id"],
            "document_id": r["document_id"],
            "title": r["title"],
            "content": r["content"][:300] + "..." if len(r["content"]) > 300 else r["content"],
            "score": round(r["score"], 4),
        }
        for r in rows
    ]


def get_total_count(conn: sqlite3.Connection, table: str) -> int:
    allowed = {"documents", "chunks", "tfidf_index", "vocabulary", "search_history"}
    if table not in allowed:
        return 0
    return conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()["cnt"]


def reset_database(conn: sqlite3.Connection, keep_schema: bool = True) -> dict:
    """Supprime toutes les données de la base de données.

    Args:
        conn: Connexion SQLite active.
        keep_schema: Si True, conserve les tables (vidées). Si False, supprime tout.

    Returns:
        Dict avec le nombre de lignes supprimées par table.
    """
    stats = {}

    tables = ["tfidf_index", "chunks", "vocabulary", "search_history", "index_stats", "documents"]

    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()["cnt"]
            conn.execute(f"DELETE FROM {table}")
            stats[table] = count
        except Exception:
            stats[table] = 0

    conn.commit()

    # Réinitialiser les compteurs auto-increment
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('documents', 'chunks', 'tfidf_index', 'vocabulary', 'search_history')")
        conn.commit()
    except Exception:
        pass

    return stats


def reset_documents_only(conn: sqlite3.Connection) -> dict:
    """Supprime uniquement les documents et leur index, conserve l'historique.

    Returns:
        Dict avec le nombre de lignes supprimées par table.
    """
    stats = {}

    tables = ["tfidf_index", "chunks", "vocabulary", "documents"]

    for table in tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()["cnt"]
            conn.execute(f"DELETE FROM {table}")
            stats[table] = count
        except Exception:
            stats[table] = 0

    conn.commit()

    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('documents', 'chunks', 'tfidf_index', 'vocabulary')")
        conn.commit()
    except Exception:
        pass

    return stats
