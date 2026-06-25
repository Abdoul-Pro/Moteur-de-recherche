import customtkinter as ctk

from src.ui.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER, FONT_BODY, FONT_SMALL, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label,
)


class DocumentPage(ctk.CTkFrame):
    def __init__(self, parent, on_back=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._on_back = on_back

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self._build_header()

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=(PAD_X, 10), pady=(0, PAD_Y))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=0)
        content_frame.rowconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            content_frame, text="", font=("Segoe UI", 22, "bold"),
            text_color=PRIMARY, anchor="w", justify="left", wraplength=600)
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.content_text = ctk.CTkTextbox(
            content_frame,
            fg_color=BG_CARD,
            text_color=TEXT_PRIMARY,
            font=("Consolas", 12),
            corner_radius=CORNER_RADIUS_LG,
            border_width=1,
            border_color=BORDER,
            wrap="word",
        )
        self.content_text.grid(row=1, column=0, sticky="nsew")
        self.content_text.configure(state="disabled")

        meta_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        meta_scroll.grid(row=1, column=1, sticky="nsew", padx=(0, PAD_X), pady=(0, PAD_Y))
        meta_scroll.columnconfigure(0, weight=1)

        meta_card = create_card(meta_scroll)
        meta_card.grid(row=0, column=0, sticky="ew")
        meta_card.columnconfigure(0, weight=1)

        create_label(meta_card, "Métadonnées du document", style="subtitle").grid(
            row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.meta_labels = {}
        fields = [
            ("Auteur", "author"),
            ("Date de publication", "date_publication"),
            ("Période historique", "period"),
            ("Région", "region"),
            ("Type de document", "doc_type"),
            ("Langue", "language"),
            ("Source", "source"),
            ("Identifiant", "id"),
        ]

        for i, (label_text, key) in enumerate(fields):
            create_label(meta_card, label_text, style="muted").grid(
                row=i * 2 + 1, column=0, sticky="ew", padx=15, pady=(8, 0))
            val_label = ctk.CTkLabel(
                meta_card, text="-", font=("Segoe UI", 13),
                text_color=TEXT_PRIMARY, anchor="w", justify="left",
                wraplength=220)
            val_label.grid(row=i * 2 + 2, column=0, sticky="ew", padx=15, pady=(0, 2))
            self.meta_labels[key] = val_label

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=PAD_X, pady=(20, 0))

        if self._on_back:
            back_btn = ctk.CTkButton(
                header, text="← Retour", font=FONT_BODY,
                fg_color="transparent", hover_color="#162d54",
                text_color=PRIMARY, command=self._on_back
            )
            back_btn.pack(side="left")

    def display_document(self, doc: dict):
        title = doc.get("title", "")
        self.title_label.configure(text=title, wraplength=max(400, self.winfo_width() - 50))

        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", doc.get("content", ""))
        self.content_text.configure(state="disabled")

        for key, label in self.meta_labels.items():
            value = doc.get(key, "-")
            if not value:
                value = "-"
            label.configure(text=str(value))

    def load_from_db(self, db, document_id: int):
        if hasattr(db, "fetchone") and callable(db.fetchone):
            try:
                row = db.fetchone("SELECT * FROM documents WHERE id = ?", (document_id,))
            except TypeError:
                row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        else:
            row = db.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        if row:
            self.display_document(dict(row))
