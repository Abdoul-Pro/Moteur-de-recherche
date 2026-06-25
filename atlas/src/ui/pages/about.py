import customtkinter as ctk

from src.ui.theme import (
    BG_DARK, BG_CARD, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER, CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label,
)


class AboutPage(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        scroll.columnconfigure(0, weight=1)

        create_label(scroll, "À propos du projet", style="title").grid(
            row=0, column=0, sticky="w", pady=(0, 20))

        about_card = create_card(scroll)
        about_card.grid(row=1, column=0, sticky="ew", pady=5)
        about_card.columnconfigure(0, weight=1)

        ctk.CTkLabel(about_card, text="🧭", font=("Segoe UI", 48)).grid(
            row=0, column=0, pady=(20, 5))
        create_label(about_card, "Atlas", style="title",
                     font=("Segoe UI", 28, "bold"), text_color=PRIMARY).grid(
            row=1, column=0)
        create_label(about_card, "Moteur de recherche de documents historiques",
                     style="body", text_color=TEXT_SECONDARY).grid(
            row=2, column=0, pady=(2, 0))
        create_label(about_card, "Version 1.0.0", style="small").grid(
            row=3, column=0, pady=(5, 10))

        create_label(about_card,
                     "Atlas est une application académique conçue comme un projet pédagogique de\n"
                     "documents historiques. Elle intègre des avancées technologiques.\n"
                     "Elle utilise l'indexation TF-IDF et la similarité cosinus pour fournir des résultats\n"
                     "de recherche pertinents et précis.",
                     style="body", text_color=TEXT_SECONDARY, justify="center").grid(
            row=4, column=0, padx=30, pady=(0, 20))

        team_card = create_card(scroll)
        team_card.grid(row=2, column=0, sticky="ew", pady=5)
        team_card.columnconfigure(0, weight=1)

        create_label(team_card, "Équipe de développement", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 10))

        team = [
            ("SORE Abdoul Fadal", "Chef de projet & Intégration"),
            ("SAWADOGO Idrissa", "Base de données SQLite"),
            ("GOUEM Aboubacar Sidiki", "Prétraitement NLP"),
            ("SAWADOGO Djemila", "TF-IDF et moteur de recherche"),
            ("DICKO Idrissa Barkey Kalilou", "Interface graphique CustomTkinter"),
        ]

        for i, (name, role) in enumerate(team):
            member_frame = ctk.CTkFrame(team_card, fg_color="transparent")
            member_frame.grid(row=i + 1, column=0, sticky="ew", padx=15, pady=3)
            member_frame.columnconfigure(0, weight=0)
            member_frame.columnconfigure(1, weight=1)

            ctk.CTkLabel(member_frame, text="👤", font=("Segoe UI", 18)).grid(
                row=0, column=0, rowspan=2, padx=(0, 10))
            create_label(member_frame, name, style="body",
                         font=("Segoe UI", 13, "bold")).grid(row=0, column=1, sticky="w")
            create_label(member_frame, role, style="small").grid(
                row=1, column=1, sticky="w")

        tech_card = create_card(scroll)
        tech_card.grid(row=3, column=0, sticky="ew", pady=(5, 20))
        tech_card.columnconfigure(0, weight=1)

        create_label(tech_card, "Technologies utilisées", style="subtitle").grid(
            row=0, column=0, sticky="w", padx=15, pady=(12, 10))

        techs = [
            ("🐍", "Python", "Langage principal"),
            ("🧠", "Scikit-learn", "TF-IDF & Similarité"),
            ("🗄️", "SQLite", "Base de données"),
            ("🎨", "CustomTkinter", "Interface graphique"),
        ]

        tech_row = ctk.CTkFrame(tech_card, fg_color="transparent")
        tech_row.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        for i, (icon, name, desc) in enumerate(techs):
            tech_item = ctk.CTkFrame(tech_row, fg_color="transparent")
            tech_item.grid(row=0, column=i, sticky="nsew", padx=5)
            tech_row.columnconfigure(i, weight=1)

            ctk.CTkLabel(tech_item, text=icon, font=("Segoe UI", 24)).grid(
                row=0, column=0)
            create_label(tech_item, name, style="body",
                         font=("Segoe UI", 12, "bold")).grid(row=1, column=0)
            create_label(tech_item, desc, style="small").grid(row=2, column=0)
