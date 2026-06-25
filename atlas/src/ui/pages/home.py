import customtkinter as ctk

from src.ui.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_TITLE, FONT_SUBTITLE, FONT_BODY, FONT_STAT,
    CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label,
)
from src.ui.components.widgets import StatCard, SearchBar


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, on_search=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._on_search = on_search

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        self._build_header(scroll)
        self._build_search(scroll)
        self._build_stats(scroll)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(20, 0))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="🧭", font=("Segoe UI", 48)).grid(
            row=0, column=0, pady=(0, 5))
        create_label(header, "Atlas", style="title",
                     font=("Segoe UI", 36, "bold"), text_color=PRIMARY).grid(
            row=1, column=0)
        create_label(header, "Explorer l'histoire. Découvrir le savoir.",
                     style="body", text_color=TEXT_SECONDARY).grid(
            row=2, column=0, pady=(5, 0))

    def _build_search(self, parent):
        search_frame = ctk.CTkFrame(parent, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(30, 0))
        search_frame.columnconfigure(0, weight=1)

        self.search_bar = SearchBar(
            search_frame,
            on_search=self._on_search,
            placeholder="Rechercher dans les documents historiques, passages, auteurs..."
        )
        self.search_bar.grid(row=0, column=0, sticky="ew")

    def _build_stats(self, parent):
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.grid(row=2, column=0, sticky="ew", pady=(40, 20))
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        cards_data = [
            ("Documents indexés", "0", "📚"),
            ("Passages indexés", "0", "📄"),
            ("Temps moyen", "0 ms", "⏱️"),
            ("Recherches effectuées", "0", "🔍"),
        ]

        self.stat_cards = []
        for i, (title, value, icon) in enumerate(cards_data):
            card = StatCard(stats_frame, title=title, value=value, icon=icon)
            card.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            self.stat_cards.append(card)

    def update_stats(self, stats: dict):
        if len(self.stat_cards) >= 4:
            self.stat_cards[0].grid_forget()
            self.stat_cards[1].grid_forget()
            self.stat_cards[2].grid_forget()
            self.stat_cards[3].grid_forget()

            cards_data = [
                ("Documents indexés", f"{stats.get('total_documents', 0):,}", "📚"),
                ("Passages indexés", f"{stats.get('total_chunks', 0):,}", "📄"),
                ("Temps moyen", f"{stats.get('avg_search_time_ms', 0):.0f} ms", "⏱️"),
                ("Recherches effectuées", f"{stats.get('total_searches', 0):,}", "🔍"),
            ]

            parent = self.stat_cards[0].master
            for i, (title, value, icon) in enumerate(cards_data):
                card = StatCard(parent, title=title, value=value, icon=icon)
                card.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
                self.stat_cards[i] = card
