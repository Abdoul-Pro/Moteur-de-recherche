"""
search.py — Page de recherche de l'interface Windows.
"""

import customtkinter as ctk

from windows.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_BODY, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_button,
)
from windows.components.widgets import SearchBar, ResultCard, Pagination


class SearchPage(ctk.CTkFrame):
    def __init__(self, parent, on_search=None, on_result_click=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._on_search = on_search
        self._on_result_click = on_result_click
        self._last_query = ""

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        self._build_header()

        self.results_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_scroll.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=(0, PAD_Y))
        self.results_scroll.columnconfigure(0, weight=1)
        self.results_scroll.rowconfigure(0, weight=1)

        self.results_frame = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        self.results_frame.grid(row=0, column=0, sticky="nsew")
        self.results_frame.columnconfigure(0, weight=1)

        self.info_label = create_label(self.results_frame, "", style="body",
                                       text_color=TEXT_SECONDARY)
        self.info_label.grid(row=0, column=0, sticky="ew", pady=20)

        self.pagination_frame = None

    def definir_requete(self, requete):
        self.search_bar.set_query(requete)
        self._last_query = requete

    def set_query(self, text):
        self._last_query = text
        self.search_bar.set_query(text)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(20, 0))
        header.columnconfigure(0, weight=1)

        self.search_bar = SearchBar(
            header,
            on_search=self._on_search,
            on_clear=self._clear_results,
            placeholder="Rechercher..."
        )
        self.search_bar.grid(row=0, column=0, sticky="ew")

    def _clear_results(self):
        for widget in self.results_frame.winfo_children():
            if widget != self.info_label:
                widget.destroy()
        if self.pagination_frame:
            self.pagination_frame.destroy()
            self.pagination_frame = None
        self.info_label.configure(text="")
        self._last_query = ""

    def _extract_query_terms(self, query):
        import re
        words = re.findall(r"\b\w{2,}\b", query.lower())
        return words

    def afficher_resultats(self, results: list, total: int, elapsed_ms: float,
                     page: int = 1, per_page: int = 10):
        self._show_results_internal(results, total, elapsed_ms, page, per_page)

    def show_results(self, results: list, total: int, elapsed_ms: float,
                     page: int = 1, per_page: int = 10):
        self._show_results_internal(results, total, elapsed_ms, page, per_page)

    def _show_results_internal(self, results, total, elapsed_ms, page=1, per_page=10):
        for widget in self.results_frame.winfo_children():
            if widget != self.info_label:
                widget.destroy()

        if self.pagination_frame:
            self.pagination_frame.destroy()
            self.pagination_frame = None

        if not results:
            self.info_label.configure(text="Aucun résultat trouvé.")
            return

        self.info_label.configure(
            text=f"{total:,} résultats trouvés ({elapsed_ms:.2f} ms)"
        )

        query_terms = self._extract_query_terms(self._last_query)

        for i, result in enumerate(results):
            card = ResultCard(
                self.results_frame, result, index=(page - 1) * per_page + i,
                on_click=self._on_result_click, query_terms=query_terms
            )
            card.grid(row=i + 1, column=0, sticky="ew", pady=5)

        total_pages = max(1, (total + per_page - 1) // per_page)
        if total_pages > 1:
            self.pagination_frame = Pagination(
                self,
                total_pages=total_pages,
                current_page=page,
                on_page_change=lambda p: self._on_search(
                    self.search_bar.get_query(), page=p
                )
            )
            self.pagination_frame.grid(row=2, column=0, pady=(20, 10), sticky="ew")
