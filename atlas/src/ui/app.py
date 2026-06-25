import customtkinter as ctk

from config import WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from src.database.connection import Database
from src.core.engine import SearchEngine
from src.ui.theme import configure_appearance, BG_DARK
from src.ui.components.sidebar import Sidebar
from src.ui.pages.home import HomePage
from src.ui.pages.search import SearchPage
from src.ui.pages.advanced import AdvancedSearchPage
from src.ui.pages.document import DocumentPage
from src.ui.pages.analytics import AnalyticsPage
from src.ui.pages.history import HistoryPage
from src.ui.pages.indexing import IndexingPage
from src.ui.pages.about import AboutPage


class AtlasApp(ctk.CTk):
    """Application principale Atlas."""

    def __init__(self):
        super().__init__()
        configure_appearance()

        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=BG_DARK)

        self.db = Database()
        self.engine = SearchEngine(self.db)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self._navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self._pages = {}
        self._current_page = None

        self._init_pages()
        self._load_initial_data()
        self._navigate("Accueil")

    def _load_initial_data(self):
        """Charge les documents de démonstration et indexe si nécessaire."""
        row = self.db.fetchone("SELECT COUNT(*) as cnt FROM documents")
        if not row or row["cnt"] == 0:
            from reset_data import DOCUMENTS_AFRICAINS
            from src.database.database import insert_document

            conn = self.db._get_connection()
            try:
                for doc in DOCUMENTS_AFRICAINS:
                    insert_document(
                        conn,
                        titre=doc["titre"],
                        contenu=doc["contenu"],
                        fichier=doc["fichier"],
                        auteur=doc["auteur"],
                        source=doc["source"],
                        periode=doc["periode"],
                        region=doc["region"],
                        type_doc=doc["type_doc"],
                        date_publication=doc["date_pub"],
                        pages=doc["pages"],
                    )
            finally:
                conn.close()

        chunks = self.db.fetchone("SELECT COUNT(*) as cnt FROM chunks")
        if not chunks or chunks["cnt"] == 0:
            from src.core.indexer import DocumentIndexer
            DocumentIndexer(self.db).index_all()
            self.engine._load_vocab_cache()

    def _init_pages(self):
        self._pages["Accueil"] = HomePage(
            self.content, on_search=self._handle_search
        )
        self._pages["Recherche"] = SearchPage(
            self.content, on_search=self._handle_search,
            on_result_click=self._open_document
        )
        self._pages["Recherche avancée"] = AdvancedSearchPage(
            self.content, on_search=self._handle_advanced_search
        )
        self._pages["Analyse"] = AnalyticsPage(
            self.content, engine=self.engine
        )
        self._pages["Historique"] = HistoryPage(
            self.content, engine=self.engine
        )
        self._pages["Indexation"] = IndexingPage(
            self.content, db=self.db
        )
        self._pages["À propos"] = AboutPage(self.content)

        self._pages["Document"] = DocumentPage(
            self.content, on_back=lambda: self._navigate("Recherche")
        )

    def _navigate(self, page_name: str):
        if self._current_page:
            self._current_page.grid_forget()

        page = self._pages.get(page_name)
        if page:
            page.grid(row=0, column=0, sticky="nsew")
            self._current_page = page
            self.sidebar.set_active(page_name)

            if page_name == "Accueil":
                stats = self.engine.get_stats()
                page.update_stats(stats)
            elif page_name == "Analyse":
                page.refresh()
            elif page_name == "Historique":
                page.refresh()

    def _handle_search(self, query: str, page: int = 1):
        per_page = 10
        offset = (page - 1) * per_page
        results, total, elapsed = self.engine.search(query, limit=per_page, offset=offset)

        self.engine.log_search(query, {}, total, elapsed)

        self._pages["Recherche"].search_bar.set_query(query)
        self._pages["Recherche"].show_results(results, total, elapsed, page, per_page)
        self._navigate("Recherche")

    def _handle_advanced_search(self, query: str, **filters):
        results, total, elapsed = self.engine.search(query, **filters)

        self.engine.log_search(query, filters, total, elapsed)

        self._pages["Recherche"].search_bar.set_query(query)
        self._pages["Recherche"].show_results(results, total, elapsed)
        self._navigate("Recherche")

    def _open_document(self, result: dict):
        doc_id = result.get("document_id")
        if doc_id:
            self._pages["Document"].load_from_db(self.db, doc_id)
            self._navigate("Document")
