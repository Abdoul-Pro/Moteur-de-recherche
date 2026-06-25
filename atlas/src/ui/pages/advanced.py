import customtkinter as ctk

from src.ui.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER, FONT_BODY, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_entry, create_button,
)


class AdvancedSearchPage(ctk.CTkFrame):
    """Page de recherche avancée avec filtres."""

    def __init__(self, parent, on_search=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._on_search = on_search

        self.columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        create_label(scroll, "Recherche avancée", style="title").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        create_label(scroll, "Affinez votre recherche en utilisant plusieurs critères",
                     style="small", text_color=TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", pady=(0, 20)
        )

        form = create_card(scroll)
        form.grid(row=2, column=0, sticky="ew", pady=10)
        form.columnconfigure((0, 1), weight=1)

        row_idx = 0

        create_label(form, "Requête", style="body").grid(
            row=row_idx, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5)
        )
        self.query_entry = create_entry(form, placeholder="Entrez votre recherche...")
        self.query_entry.grid(row=row_idx + 1, column=0, columnspan=2,
                              sticky="ew", padx=20, pady=(0, 10))
        row_idx += 2

        create_label(form, "Période historique", style="body").grid(
            row=row_idx, column=0, sticky="w", padx=20, pady=(10, 5)
        )
        self.period_var = ctk.StringVar(value="Toutes")
        self.period_menu = ctk.CTkOptionMenu(
            form, variable=self.period_var,
            values=["Toutes", "XIIIe siecle", "XIIIe-XVIe siecle", "XIXe siecle",
                    "XXe siecle", "XXIe siecle", "1983-1987", "2023-2024",
                    "Traditionnel", "Antiquite-XXIe siecle"],
            fg_color=BG_INPUT, button_color=PRIMARY,
            dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY
        )
        self.period_menu.grid(row=row_idx + 1, column=0, sticky="ew",
                              padx=20, pady=(0, 10))

        create_label(form, "Région", style="body").grid(
            row=row_idx, column=1, sticky="w", padx=20, pady=(10, 5)
        )
        self.region_var = ctk.StringVar(value="Toutes")
        self.region_menu = ctk.CTkOptionMenu(
            form, variable=self.region_var,
            values=["Toutes", "Afrique de l'Ouest", "Burkina Faso", "Sahel",
                    "Mali", "Niger", "Guinee"],
            fg_color=BG_INPUT, button_color=PRIMARY,
            dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY
        )
        self.region_menu.grid(row=row_idx + 1, column=1, sticky="ew",
                              padx=20, pady=(0, 10))
        row_idx += 2

        create_label(form, "Auteur", style="body").grid(
            row=row_idx, column=0, sticky="w", padx=20, pady=(10, 5)
        )
        self.author_entry = create_entry(form, placeholder="Nom de l'auteur...")
        self.author_entry.grid(row=row_idx + 1, column=0, sticky="ew",
                               padx=20, pady=(0, 10))

        create_label(form, "Type de document", style="body").grid(
            row=row_idx, column=1, sticky="w", padx=20, pady=(10, 5)
        )
        self.type_var = ctk.StringVar(value="Tous")
        self.type_menu = ctk.CTkOptionMenu(
            form, variable=self.type_var,
            values=["Tous", "Livre", "Article", "Archive", "Lettre", "Rapport"],
            fg_color=BG_INPUT, button_color=PRIMARY,
            dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY
        )
        self.type_menu.grid(row=row_idx + 1, column=1, sticky="ew",
                            padx=20, pady=(0, 10))
        row_idx += 2

        create_label(form, "Plage d'années", style="body").grid(
            row=row_idx, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 5)
        )

        year_frame = ctk.CTkFrame(form, fg_color="transparent")
        year_frame.grid(row=row_idx + 1, column=0, columnspan=2,
                        sticky="ew", padx=20, pady=(0, 15))
        year_frame.columnconfigure(0, weight=1)
        year_frame.columnconfigure(1, weight=0)
        year_frame.columnconfigure(2, weight=1)

        self.year_from = create_entry(year_frame, placeholder="De (année)")
        self.year_from.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        create_label(year_frame, "à", style="body").grid(row=0, column=1, padx=5)

        self.year_to = create_entry(year_frame, placeholder="À (année)")
        self.year_to.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=0)

        create_button(btn_frame, "Appliquer les filtres",
                      command=self._apply_filters, width=200).grid(
            row=0, column=0, sticky="e", padx=(0, 10)
        )
        create_button(btn_frame, "Réinitialiser",
                      command=self._reset_filters, style="secondary", width=140).grid(
            row=0, column=1
        )

    def _apply_filters(self):
        if not self._on_search:
            return

        query = self.query_entry.get().strip()
        if not query:
            return

        filters = self.get_filters()
        self._on_search(query, **filters)

    def _reset_filters(self):
        self.query_entry.delete(0, "end")
        self.period_var.set("Toutes")
        self.region_var.set("Toutes")
        self.author_entry.delete(0, "end")
        self.type_var.set("Tous")
        self.year_from.delete(0, "end")
        self.year_to.delete(0, "end")

    def get_filters(self) -> dict:
        filters = {}
        period = self.period_var.get()
        if period != "Toutes":
            filters["period"] = period
        region = self.region_var.get()
        if region != "Toutes":
            filters["region"] = region
        author = self.author_entry.get().strip()
        if author:
            filters["author"] = author
        doc_type = self.type_var.get()
        if doc_type != "Tous":
            filters["doc_type"] = doc_type
        year_from = self.year_from.get().strip()
        if year_from.isdigit():
            filters["date_from"] = year_from
        year_to = self.year_to.get().strip()
        if year_to.isdigit():
            filters["date_to"] = year_to
        return filters
