"""
database — Couche d'accès aux données SQLite pour Atlas.
"""

from database.connection import Database
from database.database import (
    create_db,
    insert_document,
    get_documents,
    get_document_by_id,
    save_search,
    get_search_history,
    delete_document,
    reset_index,
    search_documents,
)
