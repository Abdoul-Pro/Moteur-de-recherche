"""
main.py — Application Atlas : Moteur de recherche de documents historiques
Projet universitaire — Groupe 5
"""

import sys
import csv
import json
import shutil
import tkinter.filedialog as fd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import customtkinter as ctk
from src.ui.theme import (
    BG_DARK, BG_SIDEBAR, BG_CARD, BG_INPUT, BG_HOVER,
    PRIMARY, PRIMARY_HOVER, PRIMARY_DARK,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER, BORDER_LIGHT,
    ACCENT_GREEN, ACCENT_RED,
    FONT_FAMILY, FONT_BODY, FONT_SIDEBAR, FONT_SIDEBAR_ACTIVE,
    CORNER_RADIUS, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    NAV_ITEMS, configure_appearance,
    create_card, create_label, create_button, create_entry,
)
from src.ui.components.sidebar import Sidebar
from src.core.preprocessing import TextPreprocessor
from src.core.indexer import TFIDFIndexer
from src.core.search_engine import SearchEngine, SearchFilters
from src.core.statistics import StatsCollector, create_dashboard_panel
from src.database.database import get_documents
from src.database.connection import Database

configure_appearance()


class PageExport(ctk.CTkFrame):
    def __init__(self, parent, app_atlas=None, **kw):
        super().__init__(parent, fg_color=BG_DARK, **kw)
        self._app = app_atlas
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="\U0001f4e6", font=(FONT_FAMILY, 48)).grid(
            row=0, column=0, pady=(10, 10))
        create_label(scroll, "Export des documents", style="title").grid(row=1, column=0)
        create_label(scroll, "Exporter la liste des documents au format CSV ou JSON",
                     style="small").grid(row=2, column=0, pady=(0, 20))

        options_frame = create_card(scroll)
        options_frame.grid(row=3, column=0, sticky="ew", pady=10)
        options_frame.columnconfigure(0, weight=1)

        create_label(options_frame, "Format d'export", style="body").grid(
            row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.var_format = ctk.StringVar(value="CSV")
        ctk.CTkOptionMenu(
            options_frame, variable=self.var_format,
            values=["CSV", "JSON"],
            fg_color=BG_INPUT, button_color=PRIMARY,
            dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY,
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        create_button(scroll, "Exporter", command=self._exporter, width=200).grid(
            row=4, column=0, pady=20)

        self.label_statut = create_label(scroll, "", style="small")
        self.label_statut.grid(row=5, column=0, pady=10)

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


class PageSauvegarde(ctk.CTkFrame):
    def __init__(self, parent, app_atlas=None, **kw):
        super().__init__(parent, fg_color=BG_DARK, **kw)
        self._app = app_atlas
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text="\U0001f4be", font=(FONT_FAMILY, 48)).grid(
            row=0, column=0, pady=(10, 10))
        create_label(scroll, "Sauvegarde de la base de données", style="title").grid(
            row=1, column=0)
        create_label(scroll, "Créer une copie de sauvegarde de la base de données SQLite",
                     style="small").grid(row=2, column=0, pady=(0, 20))

        create_button(scroll, "Sauvegarder", command=self._sauvegarder, width=200).grid(
            row=3, column=0, pady=20)

        self.label_statut = create_label(scroll, "", style="small")
        self.label_statut.grid(row=4, column=0, pady=10)

    def _sauvegarder(self):
        if not self._app:
            self.label_statut.configure(text="Erreur : application non disponible",
                                        text_color=ACCENT_RED)
            return
        try:
            db_path = Path(__file__).resolve().parent / "data" / "atlas.db"
            if not db_path.exists():
                self.label_statut.configure(text="Base de données introuvable",
                                            text_color=ACCENT_RED)
                return
            backup_dir = Path(__file__).resolve().parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = backup_dir / f"atlas_backup_{timestamp}.db"
            shutil.copy2(db_path, backup_filename)
            self.label_statut.configure(text=f"Sauvegarde réussie : {backup_filename.name}",
                                        text_color=ACCENT_GREEN)
        except Exception as e:
            self.label_statut.configure(text=f"Erreur : {e}", text_color=ACCENT_RED)


class AtlasApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Atlas")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=BG_DARK)
        self.state("zoomed")

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.db = Database()
        self.connexion = self.db._get_connection()
        self.preprocesseur = TextPreprocessor()
        self.indexeur = TFIDFIndexer(min_df=1, max_features=10000)
        self.moteur_recherche = SearchEngine(
            indexer=self.indexeur, preprocessor=self.preprocesseur)
        self.statistiques = StatsCollector()
        self._cadre_dashboard = None

        self._documents = [dict(row) for row in get_documents(self.connexion, limit=10000)]
        if self._documents:
            self.indexeur.build_index(self._documents, text_key="content")
            self._indexe = True
        else:
            self._documents = []
            self._indexe = False

        self._init_statistiques()

        self._create_widgets()
        self._naviguer("Accueil")

    def _init_statistiques(self):
        self.statistiques.set_documents(self._documents)
        try:
            chunk_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM chunks")
            chunk_count = chunk_count["cnt"] if chunk_count else 0
        except Exception:
            chunk_count = 0
        self.statistiques.set_chunks_count(chunk_count)
        try:
            vocab_count = self.db.fetchone("SELECT COUNT(*) as cnt FROM vocabulary")
            vocab_count = vocab_count["cnt"] if vocab_count else 0
        except Exception:
            vocab_count = 0
        self.statistiques.set_vocabulary_size(vocab_count)

    def _create_widgets(self):
        self.sidebar = Sidebar(self, on_navigate=self._naviguer)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.contenu_principal = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.contenu_principal.grid(row=0, column=1, sticky="nsew")
        self.contenu_principal.rowconfigure(0, weight=1)
        self.contenu_principal.columnconfigure(0, weight=1)

        self._pages = {}
        self._page_courante = None

        from src.ui.pages.home import HomePage
        from src.ui.pages.search import SearchPage
        from src.ui.pages.advanced import AdvancedSearchPage
        from src.ui.pages.analytics import AnalyticsPage
        from src.ui.pages.indexing import IndexingPage
        from src.ui.pages.history import HistoryPage
        from src.ui.pages.import_doc import ImportPage
        from src.ui.pages.about import AboutPage
        from src.ui.pages.document import DocumentPage

        self._pages["Accueil"] = HomePage(self.contenu_principal, on_search=self._rechercher)
        self._pages["Recherche"] = SearchPage(
            self.contenu_principal, on_search=self._rechercher,
            on_result_click=self._on_result_click)
        self._pages["Recherche avancée"] = AdvancedSearchPage(
            self.contenu_principal, on_search=self._rechercher)
        self._pages["Analyse"] = AnalyticsPage(
            self.contenu_principal, engine=self.moteur_recherche)
        self._pages["Historique"] = HistoryPage(
            self.contenu_principal, engine=self.moteur_recherche)
        self._pages["Indexation"] = IndexingPage(
            self.contenu_principal, db=self.db)
        self._pages["Export"] = PageExport(self.contenu_principal, app_atlas=self)
        self._pages["Sauvegarde"] = PageSauvegarde(self.contenu_principal, app_atlas=self)
        self._pages["Ajouter un document"] = ImportPage(
            self.contenu_principal, app_atlas=self)
        self._pages["À propos"] = AboutPage(self.contenu_principal)
        self._pages["Document"] = DocumentPage(
            self.contenu_principal,
            on_back=lambda: self._naviguer("Recherche"))

        self.barre_statut = ctk.CTkLabel(
            self, text="Prêt", height=20, anchor="w",
            font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY)
        self.barre_statut.grid(row=1, column=0, columnspan=2, sticky="ew",
                               padx=PAD_X, pady=(2, 0))

    def _naviguer(self, nom: str):
        if self._page_courante:
            self._page_courante.grid_forget()

        page = self._pages.get(nom)
        if page:
            page.grid(row=0, column=0, sticky="nsew")
            self._page_courante = page
            self.sidebar.set_active(nom)

            if nom == "Accueil":
                page.update_stats(self.statistiques.get_resume())
            elif nom == "Analyse":
                page.refresh()
            elif nom == "Historique":
                page.refresh()

    def _rechercher(self, requete: str, page: int = 1, per_page: int = 10, **filtres):
        if not self._indexe:
            self._construire_index()

        top_k = page * per_page
        reponse = self.moteur_recherche.search(
            query=requete, top_k=top_k,
            filters=SearchFilters(**filtres) if filtres else None)

        start = (page - 1) * per_page
        end = start + per_page
        page_results = reponse.results[start:end]

        resultats = []
        for r in page_results:
            doc = {**r.__dict__, **(r.metadata or {})}
            doc["score"] = round(r.score * 100, 1)
            resultats.append(doc)
        self.statistiques.enregistrer_recherche(
            requete, reponse.total_results, reponse.search_time_ms)

        self._pages["Recherche"].definir_requete(requete)
        self._pages["Recherche"].afficher_resultats(
            resultats, reponse.total_results, reponse.search_time_ms,
            page=page, per_page=per_page)
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
            self.indexeur.build_index(self._documents, text_key="content")
            self._indexe = True

    def refresh_index_and_stats(self):
        self._documents = [dict(row) for row in get_documents(self.connexion, limit=10000)]
        if self._documents:
            self.indexeur.build_index(self._documents, text_key="content")
            self._indexe = True
        else:
            self._documents = []
            self._indexe = False
        self._init_statistiques()


def main():
    app = AtlasApp()
    app.mainloop()


if __name__ == "__main__":
    main()
