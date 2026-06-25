import threading

import customtkinter as ctk

from src.core.indexer import DocumentIndexer
from src.ui.theme import (
    BG_DARK, BG_CARD, PRIMARY, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_button,
)


class IndexingPage(ctk.CTkFrame):
    def __init__(self, parent, db=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._db = db
        self._indexer = DocumentIndexer(db)
        self._indexing = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)
        self._scroll = scroll

        create_label(scroll, "Indexation des documents", style="title").grid(
            row=0, column=0, sticky="w", pady=(0, 5))
        create_label(scroll, "Traitement des documents et mise à jour de l'indice de recherche",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", pady=(0, 15))

        progress_card = create_card(scroll)
        progress_card.grid(row=2, column=0, sticky="ew", pady=5)
        progress_card.columnconfigure(0, weight=1)

        create_label(progress_card, "Progression globale", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 5))

        self.progress_bar = ctk.CTkProgressBar(
            progress_card, fg_color="#1a3055", progress_color=PRIMARY,
            height=8, corner_radius=4)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        self.progress_label = create_label(progress_card, "0%", style="body",
                                           text_color=PRIMARY)
        self.progress_label.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.grid(row=3, column=0, sticky="ew", pady=5)
        stats_row.columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_labels = {}
        stat_items = [
            ("Documents traités", "0", ACCENT_GREEN),
            ("Passages indexés", "0", PRIMARY),
            ("Vocabulaire", "0", ACCENT_ORANGE),
            ("Erreurs", "0", ACCENT_RED),
        ]

        for i, (title, value, color) in enumerate(stat_items):
            card = create_card(stats_row)
            card.grid(row=0, column=i, sticky="nsew", padx=4, pady=4)
            card.columnconfigure(0, weight=1)

            create_label(card, title, style="small").grid(
                row=0, column=0, sticky="w", padx=10, pady=(8, 0))
            val_label = create_label(card, value, style="body",
                                     text_color=color, font=("Segoe UI", 18, "bold"))
            val_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
            self.stat_labels[title] = val_label

        summary_card = create_card(scroll)
        summary_card.grid(row=4, column=0, sticky="ew", pady=5)
        summary_card.columnconfigure((0, 1), weight=1)

        create_label(summary_card, "Dernière indexation", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        self.last_indexed_label = create_label(summary_card, "Aucune", style="body",
                                               text_color=TEXT_SECONDARY)
        self.last_indexed_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 4))

        create_label(summary_card, "Vocabulaire total", style="subtitle").grid(
            row=0, column=1, sticky="w", padx=15, pady=(12, 4))

        self.vocab_label = create_label(summary_card, "0 termes", style="body",
                                        text_color=TEXT_SECONDARY)
        self.vocab_label.grid(row=1, column=1, sticky="w", padx=15, pady=(0, 4))

        status_card = create_card(scroll)
        status_card.grid(row=5, column=0, sticky="ew", pady=5)
        status_card.columnconfigure(0, weight=1)

        create_label(status_card, "Statut du traitement", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.status_items = {}
        stages = [
            "Analyse des documents",
            "Extraction de texte",
            "Prétraitement linguistique",
            "Calcul TF-IDF",
            "Mise à jour de l'index",
        ]

        for i, stage in enumerate(stages):
            create_label(status_card, stage, style="body").grid(
                row=i + 1, column=0, sticky="w", padx=15, pady=2)

            status_label = create_label(status_card, "En attente", style="small",
                                        text_color=ACCENT_ORANGE)
            status_label.grid(row=i + 1, column=1, sticky="e", padx=15, pady=2)
            self.status_items[stage] = status_label

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.grid(row=6, column=0, sticky="ew", pady=(15, 0))

        self.start_btn = create_button(btn_frame, "Démarrer l'indexation",
                                       command=self._start_indexing, width=200)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = create_button(btn_frame, "Arrêter", command=self._stop_indexing,
                                      style="danger", width=120)
        self.stop_btn.pack(side="left")
        self.stop_btn.configure(state="disabled")

        log_card = create_card(scroll)
        log_card.grid(row=7, column=0, sticky="ew", pady=(10, 20))
        log_card.columnconfigure(0, weight=1)

        create_label(log_card, "Journal en temps réel", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 8))

        self.log_text = ctk.CTkTextbox(
            log_card, fg_color="transparent",
            text_color=TEXT_SECONDARY, font=("Consolas", 11),
            height=150)
        self.log_text.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        self.log_text.configure(state="disabled")

        self._load_real_stats()

    def _load_real_stats(self):
        try:
            doc_count = self._db.fetchone("SELECT COUNT(*) as cnt FROM documents")
            doc_count = doc_count["cnt"] if doc_count else 0
        except Exception:
            doc_count = 0

        try:
            chunk_count = self._db.fetchone("SELECT COUNT(*) as cnt FROM chunks")
            chunk_count = chunk_count["cnt"] if chunk_count else 0
        except Exception:
            chunk_count = 0

        try:
            vocab_count = self._db.fetchone("SELECT COUNT(*) as cnt FROM vocabulary")
            vocab_count = vocab_count["cnt"] if vocab_count else 0
        except Exception:
            vocab_count = 0

        try:
            pending_docs = self._db.fetchone(
                "SELECT COUNT(*) as cnt FROM documents d "
                "WHERE NOT EXISTS (SELECT 1 FROM chunks c WHERE c.document_id = d.id)")
            pending = pending_docs["cnt"] if pending_docs else 0
        except Exception:
            pending = 0

        try:
            stats_row = self._db.fetchone("SELECT * FROM index_stats WHERE id = 1")
            if stats_row and stats_row["last_indexed_at"]:
                last_str = stats_row["last_indexed_at"]
            else:
                last_str = None
        except Exception:
            last_str = None

        self.stat_labels["Documents traités"].configure(text=str(doc_count))
        self.stat_labels["Passages indexés"].configure(text=str(chunk_count))
        self.stat_labels["Vocabulaire"].configure(text=str(vocab_count))
        self.stat_labels["Erreurs"].configure(text="0")

        self.last_indexed_label.configure(
            text=last_str if last_str else "Aucune indexation effectuée")
        self.vocab_label.configure(text=f"{vocab_count} termes")

    def _start_indexing(self):
        if self._indexing:
            return

        self._indexing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log("Démarrage de l'indexation...")

        thread = threading.Thread(target=self._run_indexing, daemon=True)
        thread.start()

    def _stop_indexing(self):
        self._indexer.stop()
        self._log("Arrêt demandé...")
        self._update_status("Arrêt en cours...", ACCENT_ORANGE)

    def _run_indexing(self):
        self._indexer.set_callbacks(
            progress=self._on_progress,
            status=self._on_status)
        try:
            self._indexer.index_all()
        except Exception as e:
            self.after(0, lambda ev=e: self._log(f"Erreur: {str(ev)}"))
        finally:
            self.after(0, self._indexing_done)

    def _on_progress(self, pct, current, total, stage):
        self.after(0, lambda: self._update_progress(pct, current, total, stage))

    def _on_status(self, message):
        self.after(0, lambda: self._log(message))

    def _update_progress(self, pct, current, total, stage):
        self.progress_bar.set(pct / 100)
        self.progress_label.configure(text=f"{pct:.0f}%")

        if stage:
            for s, label in self.status_items.items():
                if s == stage:
                    label.configure(text="En cours", text_color=ACCENT_GREEN)
                elif list(self.status_items.keys()).index(s) < list(self.status_items.keys()).index(stage):
                    label.configure(text="Terminé", text_color=ACCENT_GREEN)

    def _update_status(self, text, color=ACCENT_ORANGE):
        for label in self.status_items.values():
            if label.cget("text") == "En cours":
                label.configure(text=text, text_color=color)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"  {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _indexing_done(self):
        self._indexing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._log("Indexation terminée!")

        for label in self.status_items.values():
            if label.cget("text") in ("En cours", "En attente"):
                label.configure(text="Terminé", text_color=ACCENT_GREEN)

        self._load_real_stats()
