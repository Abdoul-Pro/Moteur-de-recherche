"""
analytics.py — Page d'analyse de l'interface Windows.
"""

import customtkinter as ctk

from windows.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label,
)


class AnalyticsPage(ctk.CTkFrame):
    def __init__(self, parent, engine=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._engine = engine

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        create_label(scroll, "Tableau d'analyse", style="title").grid(
            row=0, column=0, sticky="w", pady=(0, PAD_Y // 2))

        metrics_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        metrics_frame.grid(row=1, column=0, sticky="ew", pady=(0, PAD_Y))
        metrics_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.metric_cards = []
        metrics = [
            ("Précision moyenne", "-", "🎯"),
            ("Rappel moyen", "-", "📊"),
            ("Score F1 moyen", "-", "📈"),
            ("Total des recherches", "-", "🔍"),
        ]

        for i, (title, value, icon) in enumerate(metrics):
            card = create_card(metrics_frame)
            card.grid(row=0, column=i, sticky="nsew", padx=2, pady=2)
            card.columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 20)).grid(
                row=0, column=0, sticky="w", padx=12, pady=(10, 0))
            val_label = create_label(card, value, style="stat")
            val_label.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 0))
            create_label(card, title, style="small").grid(
                row=2, column=0, sticky="w", padx=12, pady=(0, 10))
            self.metric_cards.append(val_label)

        content_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="ew", pady=(0, PAD_Y))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)

        chart_frame = create_card(content_frame)
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_X // 2), pady=0)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(1, weight=1)

        create_label(chart_frame, "Répartition des documents par période", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.period_list = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.period_list.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 12))

        freq_frame = create_card(content_frame)
        freq_frame.grid(row=0, column=1, sticky="nsew", padx=(PAD_X // 2, 0), pady=0)
        freq_frame.columnconfigure(0, weight=1)

        create_label(freq_frame, "Requêtes les plus fréquentes", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.freq_list = ctk.CTkFrame(freq_frame, fg_color="transparent")
        self.freq_list.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 12))

        history_frame = create_card(content_frame)
        history_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PAD_X // 2, 0))
        history_frame.columnconfigure(0, weight=1)

        create_label(history_frame, "Recherches au fil du temps", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.history_text = ctk.CTkTextbox(
            history_frame, fg_color="transparent",
            text_color=TEXT_SECONDARY, font=("Consolas", 11),
            height=150)
        self.history_text.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        self.history_text.configure(state="disabled")

    def refresh(self):
        if not self._engine:
            return

        if hasattr(self._engine, "get_stats") and callable(self._engine.get_stats):
            stats = self._engine.get_stats()
        elif hasattr(self._engine, "stats"):
            stats = self._engine.stats
        else:
            stats = {}

        if hasattr(self._engine, "get_analytics"):
            analytics = self._engine.get_analytics()
        elif hasattr(self._engine, "get_search_analytics"):
            raw = self._engine.get_search_analytics()
            analytics = {
                "searches_over_time": [
                    {"searched_at": e.timestamp, "query": e.query, "result_count": e.result_count}
                    for e in (self._engine.get_search_history(100) if hasattr(self._engine, "get_search_history") else [])
                ],
                "documents_by_period": [
                    {"period": k, "cnt": v}
                    for k, v in raw.get("period_distribution", {}).items()
                ] if raw.get("period_distribution") else [],
                "frequent_queries": [
                    {"query": q, "cnt": c}
                    for q, c in raw.get("top_queries", [])
                ],
            }
        else:
            analytics = {
                "searches_over_time": [],
                "documents_by_period": [],
                "frequent_queries": [],
            }

        precision = "-"
        if stats.get("total_searches", 0) > 0:
            avg = stats.get("avg_search_time_ms", 0)
            precision = f"{avg:.1f} ms"
        metric_values = [
            precision,
            str(stats.get("total_documents", 0)),
            str(stats.get("total_chunks", 0)),
            str(stats.get("total_searches", 0)),
        ]
        for i, val in enumerate(metric_values):
            if i < len(self.metric_cards):
                self.metric_cards[i].configure(text=val)

        for w in self.period_list.winfo_children():
            w.destroy()
        periods = analytics.get("documents_by_period", [])
        if periods:
            max_cnt = max(p["cnt"] for p in periods) if periods else 1
            for i, p in enumerate(periods[:10]):
                row = ctk.CTkFrame(self.period_list, fg_color="transparent")
                row.grid(row=i, column=0, sticky="ew", pady=1)
                create_label(row, p["period"] or "N/A", style="small",
                             font=("Segoe UI", 11), width=180, anchor="w").pack(side="left")
                bar = ctk.CTkProgressBar(row, fg_color="#1a3055", progress_color=PRIMARY, height=8)
                bar.pack(side="left", fill="x", expand=True, padx=(8, 8))
                bar.set(p["cnt"] / max_cnt if max_cnt > 0 else 0)
                create_label(row, str(p["cnt"]), style="small", width=30).pack(side="right")
        else:
            create_label(self.period_list, "Aucune donnée", style="small").grid(row=0, column=0)

        for w in self.freq_list.winfo_children():
            w.destroy()
        freq = analytics.get("frequent_queries", [])
        if freq:
            for i, q in enumerate(freq[:10]):
                row = ctk.CTkFrame(self.freq_list, fg_color="transparent")
                row.grid(row=i, column=0, sticky="ew", pady=1)
                create_label(row, f"{i+1}.", style="body",
                             text_color=PRIMARY, font=("Segoe UI", 11, "bold"), width=24).pack(side="left")
                create_label(row, q["query"], style="small",
                             font=("Segoe UI", 11)).pack(side="left", padx=(4, 0))
                create_label(row, f"{q['cnt']}x", style="small").pack(side="right")
        else:
            create_label(self.freq_list, "Aucune recherche", style="small").grid(row=0, column=0)

        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        searches = analytics.get("searches_over_time", [])
        if searches:
            for s in searches[:15]:
                line = f"  {s['searched_at']}  |  {s['query']:<30}  |  {s['result_count']} résultats\n"
                self.history_text.insert("end", line)
        else:
            self.history_text.insert("end", "  Aucune recherche enregistrée\n")
        self.history_text.configure(state="disabled")
