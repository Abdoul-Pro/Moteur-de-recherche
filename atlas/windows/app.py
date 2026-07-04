"""
app.py — Application principale Atlas pour Windows (CustomTkinter).
"""

import sys
import csv
import json
import tkinter.filedialog as fd
from pathlib import Path
from datetime import datetime

import customtkinter as ctk

from config import WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from database.connection import Database
from core.engine import SearchEngine
from windows.theme import (
    configure_appearance, BG_DARK, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    ACCENT_GREEN, ACCENT_RED, FONT_FAMILY, PAD_X, PAD_Y,
    create_label, create_button, create_card,
)
from windows.components.sidebar import Sidebar
from windows.pages.home import HomePage
from windows.pages.search import SearchPage
from windows.pages.advanced import AdvancedSearchPage
from windows.pages.document import DocumentPage
from windows.pages.analytics import AnalyticsPage
from windows.pages.history import HistoryPage
from windows.pages.indexing import IndexingPage
from windows.pages.about import AboutPage
from windows.pages.import_doc import ImportPage
from windows.pages.reset_db import ResetDBPage
from windows.pages.sauvegarde import SauvegardePage


class PageExport(ctk.CTkFrame):
    def __init__(self, parent, app_atlas=None, **kw):
        super().__init__(parent, fg_color=BG_DARK, **kw)
        self._app = app_atlas
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        create_label(scroll, "Export des documents", style="title").grid(row=0, column=0)
        create_label(scroll, "Exporter la liste des documents au format CSV ou JSON",
                     style="small").grid(row=1, column=0, pady=(0, 20))

        options_frame = create_card(scroll)
        options_frame.grid(row=2, column=0, sticky="ew", pady=10)
        options_frame.columnconfigure(0, weight=1)

        create_label(options_frame, "Format d'export", style="body").grid(
            row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.var_format = ctk.StringVar(value="CSV")
        ctk.CTkOptionMenu(
            options_frame, variable=self.var_format,
            values=["CSV", "JSON"],
            fg_color="#0a1628", button_color=PRIMARY,
            dropdown_fg_color="#0f2042", text_color=TEXT_PRIMARY,
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        create_button(scroll, "Exporter", command=self._exporter, width=200).grid(
            row=3, column=0, pady=20)

        self.label_statut = create_label(scroll, "", style="small")
        self.label_statut.grid(row=4, column=0, pady=10)

    def _exporter(self):
        if not self._app:
            self.label_statut.configure(text="Erreur : application non disponible",
                                        text_color=ACCENT_RED)
            return

        docs = self._app._documents
        if not docs:
            self.label_statut.configure(text="Aucun document à exporter",
                                        text_color=TEXT_SECONDARY)
            return

        try:
            format_choice = self.var_format.get()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format_choice == "CSV":
                default_name = f"export_documents_{timestamp}.csv"
                filetypes = [("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
            else:
                default_name = f"export_documents_{timestamp}.json"
                filetypes = [("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]

            filename = fd.asksaveasfilename(
                title="Enregistrer l'export",
                defaultextension=f".{format_choice.lower()}",
                initialfile=default_name,
                filetypes=filetypes,
            )

            if not filename:
                self.label_statut.configure(text="Export annulé",
                                            text_color=TEXT_SECONDARY)
                return

            if format_choice == "CSV":
                self._exporter_csv(docs, Path(filename))
            else:
                self._exporter_json(docs, Path(filename))

            self.label_statut.configure(text=f"Export réussi : {Path(filename).name}",
                                        text_color=ACCENT_GREEN)
        except Exception as e:
            self.label_statut.configure(text=f"Erreur : {e}", text_color=ACCENT_RED)

    def _exporter_csv(self, docs, filename):
        fields = ["id", "title", "author", "source", "period", "region",
                  "language", "doc_type", "date_publication", "total_pages", "file_path"]
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            for doc in docs:
                writer.writerow({f: doc.get(f, "") for f in fields})

    def _exporter_json(self, docs, filename):
        export_data = [{
            "id": doc.get("id", ""), "title": doc.get("title", ""),
            "author": doc.get("author", ""), "source": doc.get("source", ""),
            "period": doc.get("period", ""), "region": doc.get("region", ""),
            "language": doc.get("language", ""), "doc_type": doc.get("doc_type", ""),
            "date_publication": doc.get("date_publication", ""),
            "total_pages": doc.get("total_pages", ""),
            "file_path": doc.get("file_path", ""),
            "content": doc.get("content", ""),
        } for doc in docs]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


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
        self.connexion = self.db._get_connection()
        self.engine = SearchEngine(self.db)

        self._documents = [dict(row) for row in self.db.fetchall(
            "SELECT * FROM documents LIMIT 10000")]
        self._indexe = False
        if self._documents:
            self._indexe = True

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self._naviguer)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self._pages = {}
        self._page_courante = None

        self._init_pages()

        self.barre_statut = ctk.CTkLabel(
            self, text="Prêt", height=20, anchor="w",
            font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY)
        self.barre_statut.grid(row=1, column=0, columnspan=2, sticky="ew",
                               padx=PAD_X, pady=(2, 0))

        self._naviguer("Accueil")

    def _init_pages(self):
        self._pages["Accueil"] = HomePage(
            self.content, on_search=self._rechercher)
        self._pages["Recherche"] = SearchPage(
            self.content, on_search=self._rechercher,
            on_result_click=self._on_result_click)
        self._pages["Recherche avancée"] = AdvancedSearchPage(
            self.content, on_search=self._rechercher_avancee)
        self._pages["Analyse"] = AnalyticsPage(
            self.content, engine=self.engine)
        self._pages["Historique"] = HistoryPage(
            self.content, engine=self.engine)
        self._pages["Indexation"] = IndexingPage(
            self.content, db=self.db)
        self._pages["Ajouter un document"] = ImportPage(
            self.content, app_atlas=self)
        self._pages["Export"] = PageExport(self.content, app_atlas=self)
        self._pages["Sauvegarde"] = SauvegardePage(self.content, app_atlas=self)
        self._pages["Réinitialiser"] = ResetDBPage(self.content, app_atlas=self)
        self._pages["À propos"] = AboutPage(self.content)
        self._pages["Document"] = DocumentPage(
            self.content, on_back=lambda: self._naviguer("Recherche"))

    def _naviguer(self, nom: str):
        if self._page_courante:
            self._page_courante.grid_forget()

        page = self._pages.get(nom)
        if page:
            page.grid(row=0, column=0, sticky="nsew")
            self._page_courante = page
            self.sidebar.set_active(nom)

            if nom == "Accueil":
                stats = self.engine.get_stats()
                page.update_stats(stats)
            elif nom == "Analyse":
                page.refresh()
            elif nom == "Historique":
                page.refresh()

    def _rechercher(self, requete: str, page: int = 1, per_page: int = 10, **filtres):
        if not self._indexe:
            self._construire_index()

        offset = (page - 1) * per_page
        results, total, elapsed = self.engine.search(
            requete, limit=per_page, offset=offset)

        self.engine.log_search(requete, filtres, total, elapsed)

        resultats = []
        for r in results:
            resultats.append(r)

        self._pages["Recherche"].set_query(requete)
        self._pages["Recherche"].show_results(
            resultats, total, elapsed, page=page, per_page=per_page)
        self._naviguer("Recherche")

    def _rechercher_avancee(self, requete: str, **filtres):
        results, total, elapsed = self.engine.search(requete, **filtres)

        self.engine.log_search(requete, filtres, total, elapsed)

        self._pages["Recherche"].set_query(requete)
        self._pages["Recherche"].show_results(results, total, elapsed)
        self._naviguer("Recherche")

    def _on_result_click(self, result: dict):
        doc_id = result.get("document_id")
        if doc_id:
            row = self.db.fetchone(
                "SELECT * FROM documents WHERE id = ?", (doc_id,))
            if row:
                self._pages["Document"].display_document(dict(row))
                self._naviguer("Document")

    def _construire_index(self):
        if not self._indexe and self._documents:
            self._indexe = True

    def refresh_index_and_stats(self):
        self._documents = [dict(row) for row in self.db.fetchall(
            "SELECT * FROM documents LIMIT 10000")]
        if self._documents:
            self._indexe = True
        else:
            self._documents = []
            self._indexe = False


def main():
    app = AtlasApp()
    app.mainloop()


if __name__ == "__main__":
    main()
