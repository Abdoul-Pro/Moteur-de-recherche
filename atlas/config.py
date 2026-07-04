"""
config.py — Configuration centralisée de l'application Atlas.

Fournit les chemins et constantes partagés par toutes les couches
(core, database, UI Windows, UI Android).
"""

import sys
from pathlib import Path

# ── Chemins multiplateformes ─────────────────────────────────────────
if sys.platform == "android":
    try:
        from android.storage import app_storage_path
        BASE_DIR = Path(app_storage_path())
    except ImportError:
        BASE_DIR = Path("/data/data/com.atlas.app")
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "index"
DATABASE_PATH = DATA_DIR / "atlas.db"
BACKUPS_DIR = DATA_DIR / "backups"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# ── Encodage et formats ──────────────────────────────────────────────
DEFAULT_ENCODING = "utf-8"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".pdf", ".docx"}

# ── Indexation TF-IDF ───────────────────────────────────────────────
CHUNK_SIZE = 500
MAX_RESULTS = 100
MIN_WORD_LENGTH = 2
TOP_N_TFIDF = 50000

# ── Base de données ──────────────────────────────────────────────────
DB_POOL_SIZE = 5
DB_TIMEOUT = 30

# ── Interface Windows (CustomTkinter) ────────────────────────────────
WINDOW_TITLE = "Atlas"
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 800
