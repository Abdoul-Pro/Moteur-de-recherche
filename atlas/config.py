import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "index"
DATABASE_PATH = DATA_DIR / "atlas.db"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

DEFAULT_ENCODING = "utf-8"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml", ".html"}

CHUNK_SIZE = 500
MAX_RESULTS = 100
MIN_WORD_LENGTH = 2
TOP_N_TFIDF = 50000

DB_POOL_SIZE = 5
DB_TIMEOUT = 30

WINDOW_TITLE = "Atlas"
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 800
