"""
reset_db.py — Page de réinitialisation de la base de données.
"""

import threading
import customtkinter as ctk

from database.database import (
    reset_database, reset_documents_only, get_total_count,
)
from database.connection import Database
from windows.theme import (
    BG_DARK, BG_CARD, PRIMARY, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_button,
)


class ResetDBPage(ctk.CTkFrame):
    """Page de réinitialisation de la base de données."""

    def __init__(self, parent, app_atlas=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._app = app_atlas

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        # ── Titre ─────────────────────────────────────────────
        create_label(scroll, "Réinitialisation de la base de données",
                     style="title").grid(row=0, column=0, sticky="w", pady=(0, 5))
        create_label(scroll,
                     "Supprimez les données existantes pour repartir avec vos propres documents.",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", pady=(0, 20))

        # ── État actuel ───────────────────────────────────────
        state_card = create_card(scroll)
        state_card.grid(row=2, column=0, sticky="ew", pady=5)
        state_card.columnconfigure((0, 1), weight=1)

        create_label(state_card, "État actuel de la base", style="subtitle").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 8))

        self._stat_labels = {}
        stat_items = [
            ("Documents", "0", 0, 0),
            ("Passages", "0", 1, 0),
            ("Termes vocabulaire", "0", 0, 1),
            ("Recherches enregistrées", "0", 1, 1),
        ]

        for label_text, value, row, col in stat_items:
            lbl_val = create_label(state_card, value, style="stat",
                                   font=("Segoe UI", 22, "bold"))
            lbl_val.grid(row=row * 2 + 1, column=col, sticky="w", padx=15, pady=(4, 0))
            create_label(state_card, label_text, style="small").grid(
                row=row * 2 + 2, column=col, sticky="w", padx=15, pady=(0, 8))
            self._stat_labels[label_text] = lbl_val

        self._load_stats()

        # ── Option 1 : Tout supprimer ─────────────────────────
        reset_all_card = create_card(scroll)
        reset_all_card.grid(row=3, column=0, sticky="ew", pady=5)
        reset_all_card.columnconfigure(0, weight=1)

        create_label(reset_all_card, "Réinitialisation complète",
                     style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 4))
        create_label(reset_all_card,
                     "Supprime TOUT : documents, passages, index, vocabulaire et historique.\n"
                     "La base de données sera complètement vide.",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", padx=15, pady=(0, 8))

        self.btn_reset_all = create_button(
            reset_all_card, "Réinitialiser tout",
            command=self._reset_all, style="danger", width=250)
        self.btn_reset_all.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 12))

        # ── Option 2 : Documents seulement ────────────────────
        reset_docs_card = create_card(scroll)
        reset_docs_card.grid(row=4, column=0, sticky="ew", pady=5)
        reset_docs_card.columnconfigure(0, weight=1)

        create_label(reset_docs_card, "Supprimer les documents",
                     style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 4))
        create_label(reset_docs_card,
                     "Supprime les documents, passages et index TF-IDF.\n"
                     "Conserve l'historique des recherches.",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", padx=15, pady=(0, 8))

        self.btn_reset_docs = create_button(
            reset_docs_card, "Supprimer les documents",
            command=self._reset_docs_only, style="danger", width=250)
        self.btn_reset_docs.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 12))

        # ── Statut ────────────────────────────────────────────
        self.status_label = create_label(scroll, "", style="body",
                                         text_color=TEXT_SECONDARY)
        self.status_label.grid(row=5, column=0, sticky="ew", pady=(15, 0))

    def _load_stats(self):
        if not self._app:
            return
        db = self._app.db
        try:
            docs = db.fetchone("SELECT COUNT(*) as cnt FROM documents")["cnt"]
            chunks = db.fetchone("SELECT COUNT(*) as cnt FROM chunks")["cnt"]
            vocab = db.fetchone("SELECT COUNT(*) as cnt FROM vocabulary")["cnt"]
            searches = db.fetchone("SELECT COUNT(*) as cnt FROM search_history")["cnt"]
        except Exception:
            docs = chunks = vocab = searches = 0

        self._stat_labels["Documents"].configure(text=str(docs))
        self._stat_labels["Passages"].configure(text=str(chunks))
        self._stat_labels["Termes vocabulaire"].configure(text=str(vocab))
        self._stat_labels["Recherches enregistrées"].configure(text=str(searches))

    def _reset_all(self):
        """Réinitialisation complète de la base."""
        self.btn_reset_all.configure(state="disabled")
        self.btn_reset_docs.configure(state="disabled")
        self.status_label.configure(text="Réinitialisation en cours...",
                                    text_color=ACCENT_ORANGE)

        def _do_reset():
            try:
                conn = self._app.db._get_connection()
                stats = reset_database(conn)
                conn.close()
                self.after(0, lambda: self._on_reset_done(stats, "total"))
            except Exception as e:
                self.after(0, lambda: self._on_reset_error(str(e)))

        thread = threading.Thread(target=_do_reset, daemon=True)
        thread.start()

    def _reset_docs_only(self):
        """Suppression des documents uniquement."""
        self.btn_reset_all.configure(state="disabled")
        self.btn_reset_docs.configure(state="disabled")
        self.status_label.configure(text="Suppression des documents...",
                                    text_color=ACCENT_ORANGE)

        def _do_reset():
            try:
                conn = self._app.db._get_connection()
                stats = reset_documents_only(conn)
                conn.close()
                self.after(0, lambda: self._on_reset_done(stats, "docs"))
            except Exception as e:
                self.after(0, lambda: self._on_reset_error(str(e)))

        thread = threading.Thread(target=_do_reset, daemon=True)
        thread.start()

    def _on_reset_done(self, stats: dict, mode: str):
        """Appelé quand la réinitialisation est terminée."""
        self.btn_reset_all.configure(state="normal")
        self.btn_reset_docs.configure(state="normal")

        total_deleted = sum(stats.values())
        details = ", ".join(f"{k}: {v}" for k, v in stats.items() if v > 0)

        if mode == "total":
            msg = f"Réinitialisation terminée — {total_deleted} lignes supprimées"
        else:
            msg = f"Documents supprimés — {total_deleted} lignes supprimées"

        if details:
            msg += f"\n({details})"

        self.status_label.configure(text=msg, text_color=ACCENT_GREEN)
        self._load_stats()

        # Rafraîchir l'application principale
        if self._app:
            try:
                self._app.refresh_index_and_stats()
            except Exception:
                pass

    def _on_reset_error(self, error: str):
        """Appelé en cas d'erreur."""
        self.btn_reset_all.configure(state="normal")
        self.btn_reset_docs.configure(state="normal")
        self.status_label.configure(
            text=f"Erreur lors de la réinitialisation : {error}",
            text_color=ACCENT_RED)
