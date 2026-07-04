"""
history.py — Page d'historique de l'interface Windows.
"""

import customtkinter as ctk

from windows.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label,
)


class HistoryPage(ctk.CTkFrame):
    def __init__(self, parent, engine=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._engine = engine

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        create_label(scroll, "Historique des recherches", style="title").grid(
            row=0, column=0, sticky="w", pady=(0, 5))
        create_label(scroll, "Consultez les archives liées à votre activité",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", pady=(0, 15))

        table_card = create_card(scroll)
        table_card.grid(row=2, column=0, sticky="ew", pady=(0, PAD_Y))
        table_card.columnconfigure(0, weight=0)
        table_card.columnconfigure(1, weight=3)
        table_card.columnconfigure(2, weight=2)
        table_card.columnconfigure(3, weight=1)
        table_card.columnconfigure(4, weight=2)

        headers = ["#", "Requête", "Filtres", "Résultats", "Date et heure"]
        for i, h in enumerate(headers):
            create_label(table_card, h, style="body",
                         text_color=PRIMARY, font=("Segoe UI", 12, "bold")).grid(
                row=0, column=i, sticky="w", padx=10, pady=(10, 5))

        self.table_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, columnspan=5, sticky="ew",
                              padx=5, pady=(0, 10))
        self.table_frame.columnconfigure(0, weight=0)
        self.table_frame.columnconfigure(1, weight=3)
        self.table_frame.columnconfigure(2, weight=2)
        self.table_frame.columnconfigure(3, weight=1)
        self.table_frame.columnconfigure(4, weight=2)

        activity_card = create_card(scroll)
        activity_card.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        activity_card.columnconfigure(0, weight=1)

        create_label(activity_card, "Activité récente", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.activity_frame = ctk.CTkFrame(activity_card, fg_color="transparent")
        self.activity_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))

    def _get_entry_attr(self, entry, attr, default=""):
        if hasattr(entry, attr):
            return getattr(entry, attr, default)
        if isinstance(entry, dict):
            return entry.get(attr, default)
        return default

    def refresh(self):
        if not self._engine:
            return

        for widget in self.table_frame.winfo_children():
            widget.destroy()
        for widget in self.activity_frame.winfo_children():
            widget.destroy()

        history = self._engine.get_search_history(limit=50)

        if not history:
            create_label(self.table_frame, "Aucun historique",
                         style="small", text_color=TEXT_SECONDARY).grid(
                row=0, column=0, columnspan=5, pady=20)
            return

        for i, entry in enumerate(history):
            row_fg = BG_CARD if i % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(self.table_frame, fg_color=row_fg, corner_radius=0)
            row_frame.grid(row=i, column=0, columnspan=5, sticky="ew", pady=1)
            row_frame.columnconfigure(0, weight=0)
            row_frame.columnconfigure(1, weight=3)
            row_frame.columnconfigure(2, weight=2)
            row_frame.columnconfigure(3, weight=1)
            row_frame.columnconfigure(4, weight=2)

            query = self._get_entry_attr(entry, "query", "")
            result_count = self._get_entry_attr(entry, "result_count", 0)
            timestamp = self._get_entry_attr(entry, "timestamp",
                          self._get_entry_attr(entry, "searched_at", ""))
            filters_raw = self._get_entry_attr(entry, "filters", None)

            create_label(row_frame, str(i + 1), style="body").grid(
                row=0, column=0, sticky="w", padx=10, pady=4)
            create_label(row_frame, query, style="body").grid(
                row=0, column=1, sticky="w", padx=10, pady=4)

            if filters_raw:
                import json
                try:
                    f = json.loads(filters_raw) if isinstance(filters_raw, str) else filters_raw
                    if isinstance(f, dict):
                        filter_text = ", ".join(f"{k}: {v}" for k, v in f.items())
                    else:
                        filter_text = str(f)
                except (json.JSONDecodeError, TypeError):
                    filter_text = str(filters_raw)
            else:
                filter_text = "-"
            create_label(row_frame, filter_text, style="small").grid(
                row=0, column=2, sticky="w", padx=10, pady=4)
            create_label(row_frame, str(result_count), style="body").grid(
                row=0, column=3, sticky="w", padx=10, pady=4)
            create_label(row_frame, timestamp, style="small").grid(
                row=0, column=4, sticky="w", padx=10, pady=4)

            if i < 5:
                activity_text = f"{timestamp} — Recherche \"{query}\" ({result_count} résultats)"
                create_label(self.activity_frame, activity_text, style="small").grid(
                    row=i, column=0, sticky="w", pady=2)
