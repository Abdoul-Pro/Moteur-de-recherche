"""
import_doc.py — Page d'import de documents de l'interface Windows.
"""

import tkinter.filedialog as fd
import os
import traceback
from datetime import datetime
import customtkinter as ctk

from database.database import insert_document
from utils.datetime import now_local_str
from windows.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, ACCENT_GREEN, ACCENT_RED,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_button,
)
from core.preprocessing import TextPreprocessor

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

USER_FIELDS = [
    ("title", "Titre", "TEXT", True, ""),
    ("author", "Auteur", "TEXT", False, ""),
    ("source", "Source", "TEXT", False, ""),
    ("period", "Période historique", "TEXT", False, ""),
    ("region", "Région", "TEXT", False, ""),
    ("language", "Langue", "TEXT", False, "Français"),
]

FIELD_LABELS = {name: label for name, label, *_ in USER_FIELDS}


class ImportPage(ctk.CTkFrame):
    def __init__(self, parent, app_atlas=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._app = app_atlas
        self._preprocessor = TextPreprocessor()
        self._selected_file_path = None
        self._selected_file_content = ""
        self._toast_job = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        self.scroll.columnconfigure(0, weight=1)

        self._build_ui()

        self.lbl_status = create_label(self.scroll, "", style="body", text_color=TEXT_SECONDARY)
        self.lbl_status.grid(row=4, column=0, sticky="ew", pady=(10, 0))

    def _build_ui(self):
        create_label(
            self.scroll,
            "Ajoutez un fichier ou un texte pour qu'il soit indexé automatiquement "
            "et disponible dans les recherches.",
            style="body", text_color=TEXT_SECONDARY, wraplength=800, justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        file_frame = create_card(self.scroll)
        file_frame.grid(row=1, column=0, sticky="ew", pady=5)
        file_frame.columnconfigure(0, weight=1)

        create_label(file_frame, "Importer un fichier", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 5))

        btn_choose = create_button(
            file_frame, "Choisir un fichier", command=self._choose_file, width=200, height=32)
        btn_choose.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        self.lbl_file = create_label(file_frame, "Aucun fichier sélectionné",
                                     style="body", text_color=TEXT_SECONDARY)
        self.lbl_file.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 5))

        self.btn_import_file = create_button(
            file_frame, "Importer et indexer", command=self._import_selected_file,
            width=200, height=32, state="disabled",
            fg_color=PRIMARY, hover_color=ACCENT_GREEN)
        self.btn_import_file.grid(row=3, column=0, sticky="w", padx=15, pady=5)

        manual_frame = create_card(self.scroll)
        manual_frame.grid(row=2, column=0, sticky="ew", pady=5)
        manual_frame.columnconfigure(0, weight=1)

        create_label(manual_frame, "Saisie manuelle", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 5))

        self.fields_frame = ctk.CTkFrame(manual_frame, fg_color="transparent")
        self.fields_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        self.fields_frame.columnconfigure(1, weight=1)

        self._build_manual_fields()

        create_button(
            manual_frame, "Importer et indexer", command=self._import_manual,
            width=200, height=32, fg_color=PRIMARY, hover_color=ACCENT_GREEN
        ).grid(row=2, column=0, sticky="w", padx=15, pady=5)

    def _build_manual_fields(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()

        self.entries = {}
        for row_idx, (name, label_text, typ, required, default) in enumerate(USER_FIELDS):
            display = label_text + (" *" if required else "")
            lbl = ctk.CTkLabel(self.fields_frame, text=display, anchor="w",
                               text_color=TEXT_PRIMARY, font=("Segoe UI", 12))
            lbl.grid(row=row_idx, column=0, sticky="w", pady=2, padx=(0, 5))

            entry = ctk.CTkEntry(
                self.fields_frame,
                placeholder_text=f"Saisir {label_text.lower()}...",
                fg_color=BG_INPUT, border_color=BORDER, text_color=TEXT_PRIMARY)
            entry.grid(row=row_idx, column=1, sticky="ew", pady=2)

            if default:
                entry.insert(0, default)

            self.entries[name] = (entry, typ, required)

        content_row = len(USER_FIELDS)
        create_label(self.fields_frame, "Contenu *", anchor="w",
                     text_color=TEXT_PRIMARY, font=("Segoe UI", 12)).grid(
            row=content_row, column=0, sticky="nw", pady=2, padx=(0, 5))

        textbox = ctk.CTkTextbox(
            self.fields_frame, height=120,
            fg_color=BG_INPUT, text_color=TEXT_PRIMARY,
            font=("Consolas", 12), border_width=1, border_color=BORDER)
        textbox.grid(row=content_row, column=1, sticky="ew", pady=2)
        self.entries["content"] = (textbox, "TEXT", True)

    def _show_toast(self, message, is_error=False):
        if self._toast_job:
            self.after_cancel(self._toast_job)

        for child in self.winfo_children():
            if getattr(child, "_is_toast", False):
                child.destroy()

        color = ACCENT_RED if is_error else ACCENT_GREEN
        toast = ctk.CTkToplevel(self)
        toast._is_toast = True
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(fg_color=color, corner_radius=12)

        ctk.CTkLabel(
            toast, text=message, font=("Segoe UI", 14, "bold"),
            text_color="#ffffff", wraplength=500, padx=20, pady=12
        ).pack()

        toast.update_idletasks()
        w = toast.winfo_reqwidth()
        h = toast.winfo_reqheight()
        x = (self.winfo_toplevel().winfo_width() // 2) - (w // 2)
        y = (self.winfo_toplevel().winfo_height() // 2) - (h // 2)
        toast.geometry(f"+{x}+{y}")

        self._toast_job = self.after(3000, toast.destroy)

    def _choose_file(self):
        filetypes = [("Fichiers texte", "*.txt")]
        if HAS_PDF:
            filetypes.append(("Fichiers PDF", "*.pdf"))
        if HAS_DOCX:
            filetypes.append(("Documents Word", "*.docx"))
        filetypes.append(("Tous les fichiers", "*.*"))

        filename = fd.askopenfilename(title="Choisir un fichier à importer", filetypes=filetypes)
        if filename:
            self._selected_file_path = filename
            self.lbl_file.configure(text=os.path.basename(filename), text_color=TEXT_PRIMARY)
            self.btn_import_file.configure(state="normal")
            self._read_file_content()
        else:
            self._selected_file_path = None
            self.lbl_file.configure(text="Aucun fichier sélectionné", text_color=TEXT_SECONDARY)
            self.btn_import_file.configure(state="disabled")

    def _read_file_content(self):
        if not self._selected_file_path:
            self._selected_file_content = ""
            return
        ext = os.path.splitext(self._selected_file_path)[1].lower()
        try:
            if ext == ".txt":
                with open(self._selected_file_path, "r", encoding="utf-8") as f:
                    self._selected_file_content = f.read()
            elif ext == ".pdf" and HAS_PDF:
                import PyPDF2
                text = []
                with open(self._selected_file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text.append(page.extract_text() or "")
                self._selected_file_content = "\n".join(text)
            elif ext == ".docx" and HAS_DOCX:
                import docx
                doc = docx.Document(self._selected_file_path)
                text = [p.text for p in doc.paragraphs]
                self._selected_file_content = "\n".join(text)
            else:
                self._selected_file_content = ""
                self._show_toast(f"Format non supporté : {ext}", is_error=True)
        except Exception as e:
            self._selected_file_content = ""
            self._show_toast(f"Erreur de lecture : {e}", is_error=True)

    def _import_selected_file(self):
        if not self._selected_file_path:
            self._show_toast("Veuillez sélectionner un fichier.", is_error=True)
            return
        if not self._selected_file_content.strip():
            self._show_toast("Le fichier est vide ou illisible.", is_error=True)
            return

        title = os.path.splitext(os.path.basename(self._selected_file_path))[0]
        ext = os.path.splitext(self._selected_file_path)[1].lower()
        doc_type = "Livre"
        if ext == ".pdf":
            doc_type = "PDF"
        elif ext == ".docx":
            doc_type = "Document Word"

        self._insert_document(
            title=title, author="", source="", period="", region="",
            language="Français", doc_type=doc_type, date_publication="",
            total_pages=1, file_path=self._selected_file_path,
            content=self._selected_file_content, created_at=now_local_str(),
        )

    def _import_manual(self):
        values = {}
        errors = []
        for name, (widget, typ, required) in self.entries.items():
            if isinstance(widget, ctk.CTkTextbox):
                val = widget.get("1.0", "end").strip()
            else:
                val = widget.get().strip()
            if required and not val:
                field_label = FIELD_LABELS.get(name, name)
                errors.append(f"Le champ « {field_label} » est obligatoire.")
                continue
            values[name] = val

        if errors:
            self._show_toast("\n".join(errors), is_error=True)
            return

        if not values.get("content"):
            self._show_toast("Le contenu du document ne peut pas être vide.", is_error=True)
            return

        self._insert_document(
            title=values.get("title", ""),
            author=values.get("author", ""),
            source=values.get("source", ""),
            period=values.get("period", ""),
            region=values.get("region", ""),
            language=values.get("language", "Français"),
            doc_type="Texte",
            date_publication="",
            total_pages=1,
            file_path=f"saisie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            content=values.get("content", ""),
            created_at=now_local_str(),
        )

    def _insert_document(self, **kwargs):
        if not kwargs.get("content", "").strip():
            self._show_toast("Le contenu du document ne peut pas être vide.", is_error=True)
            return
        try:
            conn = self._app.connexion
            doc_id = insert_document(
                conn,
                titre=kwargs.get("title", ""),
                contenu=kwargs.get("content", ""),
                fichier=kwargs.get("file_path", ""),
                auteur=kwargs.get("author", ""),
                source=kwargs.get("source", ""),
                periode=kwargs.get("period", ""),
                region=kwargs.get("region", ""),
                langue=kwargs.get("language", "Français"),
                type_doc=kwargs.get("doc_type", "Texte"),
                date_publication=kwargs.get("date_publication", ""),
                pages=int(kwargs.get("total_pages", 1)),
                title=kwargs.get("title", ""),
                content=kwargs.get("content", ""),
                file_path=kwargs.get("file_path", ""),
                author=kwargs.get("author", ""),
                period=kwargs.get("period", ""),
                doc_type=kwargs.get("doc_type", "Texte"),
                total_pages=int(kwargs.get("total_pages", 1)),
                created_at=kwargs.get("created_at", now_local_str()),
            )
            self._show_toast(f"Document enregistré avec ID {doc_id}")
            self.lbl_status.configure(
                text=f"Document {doc_id} enregistré. Indexation en cours...",
                text_color=ACCENT_GREEN)
            self._app.refresh_index_and_stats()
        except Exception as e:
            self._show_toast(f"Erreur : {e}", is_error=True)
            traceback.print_exc()
