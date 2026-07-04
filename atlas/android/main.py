"""
main.py — Application Atlas pour Android (Kivy).

Toutes les pages et fonctionnalités de la version Windows
sont implémentées ici pour Android.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.clock import Clock
import threading
import os
from datetime import datetime

from android.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, PRIMARY_HOVER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE, ACCENT_BLUE,
    CORNER_RADIUS, CORNER_RADIUS_LG,
    PAD_X, PAD_Y,
)
from database.connection import Database
from core.engine import SearchEngine
from database.database import get_documents, insert_document
from config import DATABASE_PATH, BACKUPS_DIR


def _get_logo_path():
    """Retourne le chemin vers logo.png de façon robuste (desktop + Android)."""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "assets", "icons", "logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "logo.png"),
        "assets/icons/logo.png",
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def hex_to_color(hex_color):
    """Convertit une couleur hex en tuple RGBA."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def create_card_bg(widget, color=BG_CARD, radius=CORNER_RADIUS_LG):
    """Dessine un fond arrondi sur un widget."""
    with widget.canvas.before:
        Color(*hex_to_color(color))
        RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    widget.bind(pos=lambda w, _: update_card_bg(w, color, radius),
                size=lambda w, _: update_card_bg(w, color, radius))


def update_card_bg(widget, color, radius):
    widget.canvas.before.clear()
    with widget.canvas.before:
        Color(*hex_to_color(color))
        RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN D'ACCUEIL
# ══════════════════════════════════════════════════════════════════════
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(800))
        layout.bind(minimum_height=layout.setter('height'))

        # ── Header ──
        _lp = _get_logo_path()
        if _lp:
            from kivy.uix.image import Image as KivyImage
            layout.add_widget(KivyImage(source=_lp, size_hint_y=None,
                                        height=dp(120), allow_stretch=True))
        else:
            layout.add_widget(Label(text='🧭', font_size=dp(48),
                                    size_hint_y=None, height=dp(55)))
        layout.add_widget(Label(
            text='Atlas', font_size=dp(32), bold=True,
            color=hex_to_color(PRIMARY), size_hint_y=None, height=dp(40)))
        layout.add_widget(Label(
            text="Explorer l'histoire. Découvrir le savoir.",
            font_size=dp(13), color=hex_to_color(TEXT_SECONDARY),
            size_hint_y=None, height=dp(22)))

        # ── Barre de recherche ──
        search_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                               height=dp(48), spacing=dp(8))
        self.search_input = TextInput(
            hint_text="Rechercher dans les documents...",
            multiline=False, size_hint_x=0.7,
            background_color=hex_to_color(BG_CARD),
            foreground_color=hex_to_color(TEXT_PRIMARY),
            hint_color=hex_to_color(TEXT_SECONDARY),
            padding=[dp(10), dp(10)])
        search_box.add_widget(self.search_input)

        search_btn = Button(text="🔍", size_hint_x=0.15,
                            background_color=hex_to_color(PRIMARY),
                            color=hex_to_color(BG_DARK), bold=True, font_size=dp(16))
        search_btn.bind(on_press=self.do_search)
        search_box.add_widget(search_btn)
        layout.add_widget(search_box)

        # ── Statistiques ──
        stats_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(140))
        self.stat_labels = {}
        for title, icon in [("Documents", "📚"), ("Passages", "📄"),
                            ("Recherches", "🔍"), ("Temps moyen", "⏱️")]:
            card = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(2))
            create_card_bg(card)
            card.add_widget(Label(text=icon, font_size=dp(20), size_hint_y=None, height=dp(28)))
            val_label = Label(text="0", font_size=dp(20), bold=True,
                              color=hex_to_color(PRIMARY), size_hint_y=None, height=dp(26))
            card.add_widget(val_label)
            card.add_widget(Label(text=title, font_size=dp(11),
                                  color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(18)))
            stats_grid.add_widget(card)
            self.stat_labels[title] = val_label
        layout.add_widget(stats_grid)

        # ── Navigation ──
        nav_items = [
            ("🔍 Recherche", "search"), ("🔬 Recherche avancée", "advanced"),
            ("📊 Analyse", "analytics"), ("📋 Historique", "history"),
            ("⚙️ Indexation", "indexing"), ("📄 Ajouter document", "import"),
            ("📤 Export", "export"), ("💾 Sauvegarde", "backup"),
            ("🗑️ Réinitialiser", "reset"),
            ("ℹ️ À propos", "about"),
        ]

        nav_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(396))
        for label, screen_name in nav_items:
            btn = Button(text=label, size_hint_y=None, height=dp(36),
                         background_color=hex_to_color(BG_CARD),
                         color=hex_to_color(TEXT_PRIMARY), font_size=dp(13))
            btn.bind(on_press=lambda x, s=screen_name: self.navigate(s))
            nav_grid.add_widget(btn)
        layout.add_widget(nav_grid)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def do_search(self, instance):
        query = self.search_input.text.strip()
        if query:
            App.get_running_app().search(query)

    def navigate(self, screen_name):
        App.get_running_app().root.current = screen_name

    def on_enter(self):
        app = App.get_running_app()
        stats = app.get_stats()
        if self.stat_labels:
            self.stat_labels["Documents"].text = str(stats.get("total_documents", 0))
            self.stat_labels["Passages"].text = str(stats.get("total_chunks", 0))
            self.stat_labels["Recherches"].text = str(stats.get("total_searches", 0))
            self.stat_labels["Temps moyen"].text = f"{stats.get('avg_search_time_ms', 0):.0f} ms"


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN DE RECHERCHE
# ══════════════════════════════════════════════════════════════════════
class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y)

        # ── Header ──
        header = BoxLayout(orientation='horizontal', size_hint_y=None,
                           height=dp(48), spacing=dp(8))
        back_btn = Button(text="← Retour", size_hint_x=0.25,
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY), font_size=dp(12))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        header.add_widget(back_btn)

        self.search_input = TextInput(
            hint_text="Rechercher...", multiline=False, size_hint_x=0.55,
            background_color=hex_to_color(BG_CARD),
            foreground_color=hex_to_color(TEXT_PRIMARY),
            hint_color=hex_to_color(TEXT_SECONDARY),
            padding=[dp(10), dp(10)])
        header.add_widget(self.search_input)

        search_btn = Button(text="🔍", size_hint_x=0.2,
                            background_color=hex_to_color(PRIMARY),
                            color=hex_to_color(BG_DARK), font_size=dp(14))
        search_btn.bind(on_press=self.do_search)
        header.add_widget(search_btn)
        layout.add_widget(header)

        # ── Résultats ──
        self.results_scroll = ScrollView()
        self.results_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                     spacing=dp(8), padding=[0, dp(8)])
        self.results_box.bind(minimum_height=self.results_box.setter('height'))
        self.results_scroll.add_widget(self.results_box)
        layout.add_widget(self.results_scroll)

        self.add_widget(layout)

    def do_search(self, instance):
        query = self.search_input.text.strip()
        if query:
            App.get_running_app().search(query)

    def show_results(self, results, total, elapsed_ms):
        self.results_box.clear_widgets()

        self.results_box.add_widget(Label(
            text=f"{total} résultats trouvés ({elapsed_ms:.1f} ms)",
            font_size=dp(13), color=hex_to_color(TEXT_SECONDARY),
            size_hint_y=None, height=dp(28)))

        for i, result in enumerate(results):
            card = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(3),
                           size_hint_y=None, height=dp(110))
            create_card_bg(card)

            card.add_widget(Label(
                text=f"{i+1}. {result.get('title', '')[:50]}",
                font_size=dp(14), bold=True,
                color=hex_to_color(TEXT_PRIMARY),
                size_hint_y=None, height=dp(24),
                halign='left', text_size=(dp(280), None)))

            snippet = result.get('snippet', '')[:80]
            if len(result.get('snippet', '')) > 80:
                snippet += "..."
            card.add_widget(Label(
                text=snippet, font_size=dp(11),
                color=hex_to_color(TEXT_SECONDARY),
                size_hint_y=None, height=dp(36),
                halign='left', text_size=(dp(280), None)))

            score = result.get('score', 0)
            period = result.get('period', '')
            card.add_widget(Label(
                text=f"Score: {score}%  |  {period}",
                font_size=dp(10), color=hex_to_color(PRIMARY),
                size_hint_y=None, height=dp(18),
                halign='left'))

            self.results_box.add_widget(card)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN RECHERCHE AVANCÉE
# ══════════════════════════════════════════════════════════════════════
class AdvancedScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(700))
        layout.bind(minimum_height=layout.setter('height'))

        # Back
        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Recherche avancée", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Requête
        layout.add_widget(Label(text="Requête", font_size=dp(13), color=hex_to_color(TEXT_PRIMARY),
                                size_hint_y=None, height=dp(22), halign='left'))
        self.query_input = TextInput(hint_text="Entrez votre recherche...", multiline=False,
                                     size_hint_y=None, height=dp(40),
                                     background_color=hex_to_color(BG_CARD),
                                     foreground_color=hex_to_color(TEXT_PRIMARY),
                                     hint_color=hex_to_color(TEXT_SECONDARY),
                                     padding=[dp(10), dp(10)])
        layout.add_widget(self.query_input)

        # Période
        layout.add_widget(Label(text="Période historique", font_size=dp(13),
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22)))
        self.period_spinner = Spinner(
            text='Toutes',
            values=['Toutes', 'XIIIe siècle', 'XIXe siècle', 'XXe siècle',
                    'XIIIe-XVIe siècle', 'XVe-XVIe siècle', 'XVIe-XIXe siècle',
                    '1983-1987', '2023-2024'],
            size_hint_y=None, height=dp(40),
            background_color=hex_to_color(BG_CARD),
            color=hex_to_color(TEXT_PRIMARY))
        layout.add_widget(self.period_spinner)

        # Région
        layout.add_widget(Label(text="Région", font_size=dp(13),
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22)))
        self.region_spinner = Spinner(
            text='Toutes',
            values=['Toutes', 'Afrique de l\'Ouest', 'Burkina Faso', 'Sahel',
                    'Mali', 'Niger', 'Mondial'],
            size_hint_y=None, height=dp(40),
            background_color=hex_to_color(BG_CARD),
            color=hex_to_color(TEXT_PRIMARY))
        layout.add_widget(self.region_spinner)

        # Type
        layout.add_widget(Label(text="Type de document", font_size=dp(13),
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22)))
        self.type_spinner = Spinner(
            text='Tous',
            values=['Tous', 'Livre', 'Article', 'Archive', 'Lettre'],
            size_hint_y=None, height=dp(40),
            background_color=hex_to_color(BG_CARD),
            color=hex_to_color(TEXT_PRIMARY))
        layout.add_widget(self.type_spinner)

        # Auteur
        layout.add_widget(Label(text="Auteur", font_size=dp(13),
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22)))
        self.author_input = TextInput(hint_text="Nom de l'auteur...", multiline=False,
                                      size_hint_y=None, height=dp(40),
                                      background_color=hex_to_color(BG_CARD),
                                      foreground_color=hex_to_color(TEXT_PRIMARY),
                                      hint_color=hex_to_color(TEXT_SECONDARY),
                                      padding=[dp(10), dp(10)])
        layout.add_widget(self.author_input)

        # Boutons
        btn_box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        search_btn = Button(text="Rechercher", background_color=hex_to_color(PRIMARY),
                            color=hex_to_color(BG_DARK), bold=True)
        search_btn.bind(on_press=self.do_search)
        btn_box.add_widget(search_btn)

        reset_btn = Button(text="Réinitialiser", background_color=hex_to_color(BG_CARD),
                           color=hex_to_color(TEXT_PRIMARY))
        reset_btn.bind(on_press=self.reset_filters)
        btn_box.add_widget(reset_btn)
        layout.add_widget(btn_box)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def do_search(self, instance):
        query = self.query_input.text.strip()
        if not query:
            return
        filters = {}
        period = self.period_spinner.text
        if period != 'Toutes':
            filters['period'] = period
        region = self.region_spinner.text
        if region != 'Toutes':
            filters['region'] = region
        author = self.author_input.text.strip()
        if author:
            filters['author'] = author
        doc_type = self.type_spinner.text
        if doc_type != 'Tous':
            filters['doc_type'] = doc_type
        App.get_running_app().search(query, **filters)

    def reset_filters(self, instance):
        self.query_input.text = ''
        self.period_spinner.text = 'Toutes'
        self.region_spinner.text = 'Toutes'
        self.type_spinner.text = 'Tous'
        self.author_input.text = ''


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN ANALYSE
# ══════════════════════════════════════════════════════════════════════
class AnalyticsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(600))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Tableau d'analyse", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Métriques
        self.metric_labels = {}
        metrics = [("Temps moyen", "⏱️"), ("Documents", "📚"),
                   ("Passages", "📄"), ("Recherches", "🔍")]
        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(120))
        for title, icon in metrics:
            card = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(2))
            create_card_bg(card)
            card.add_widget(Label(text=icon, font_size=dp(18), size_hint_y=None, height=dp(24)))
            val = Label(text="0", font_size=dp(18), bold=True,
                        color=hex_to_color(PRIMARY), size_hint_y=None, height=dp(24))
            card.add_widget(val)
            card.add_widget(Label(text=title, font_size=dp(10),
                                  color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(16)))
            grid.add_widget(card)
            self.metric_labels[title] = val
        layout.add_widget(grid)

        # Documents par période
        layout.add_widget(Label(text="Documents par période", font_size=dp(16), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(28)))
        self.period_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150))
        layout.add_widget(self.period_box)

        # Requêtes fréquentes
        layout.add_widget(Label(text="Requêtes fréquentes", font_size=dp(16), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(28)))
        self.freq_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150))
        layout.add_widget(self.freq_box)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self):
        app = App.get_running_app()
        stats = app.get_stats()
        analytics = app.engine.get_analytics()

        if self.metric_labels:
            self.metric_labels["Temps moyen"].text = f"{stats.get('avg_search_time_ms', 0):.1f} ms"
            self.metric_labels["Documents"].text = str(stats.get("total_documents", 0))
            self.metric_labels["Passages"].text = str(stats.get("total_chunks", 0))
            self.metric_labels["Recherches"].text = str(stats.get("total_searches", 0))

        self.period_box.clear_widgets()
        periods = analytics.get("documents_by_period", [])
        if periods:
            for p in periods[:8]:
                self.period_box.add_widget(Label(
                    text=f"{p['period'] or 'N/A'}: {p['cnt']} documents",
                    font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                    size_hint_y=None, height=dp(20), halign='left'))
        else:
            self.period_box.add_widget(Label(text="Aucune donnée", font_size=dp(12),
                                             color=hex_to_color(TEXT_MUTED), size_hint_y=None, height=dp(20)))

        self.freq_box.clear_widgets()
        freq = analytics.get("frequent_queries", [])
        if freq:
            for q in freq[:8]:
                self.freq_box.add_widget(Label(
                    text=f"{q['query']}: {q['cnt']} fois",
                    font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                    size_hint_y=None, height=dp(20), halign='left'))
        else:
            self.freq_box.add_widget(Label(text="Aucune recherche", font_size=dp(12),
                                           color=hex_to_color(TEXT_MUTED), size_hint_y=None, height=dp(20)))


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN HISTORIQUE
# ══════════════════════════════════════════════════════════════════════
class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(500))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Historique des recherches", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        self.history_box = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        self.history_box.bind(minimum_height=self.history_box.setter('height'))
        layout.add_widget(self.history_box)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self):
        self.history_box.clear_widgets()
        app = App.get_running_app()
        history = app.engine.get_search_history(limit=30)

        if not history:
            self.history_box.add_widget(Label(text="Aucun historique",
                                              font_size=dp(13), color=hex_to_color(TEXT_MUTED),
                                              size_hint_y=None, height=dp(30)))
            return

        for i, entry in enumerate(history):
            card = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(2),
                           size_hint_y=None, height=dp(60))
            create_card_bg(card)

            query = entry.get('query', '') if isinstance(entry, dict) else getattr(entry, 'query', '')
            count = entry.get('result_count', 0) if isinstance(entry, dict) else getattr(entry, 'result_count', 0)
            ts = entry.get('searched_at', '') if isinstance(entry, dict) else getattr(entry, 'searched_at', '')

            card.add_widget(Label(text=f"🔍 {query}", font_size=dp(13), bold=True,
                                  color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22),
                                  halign='left', text_size=(dp(300), None)))
            card.add_widget(Label(text=f"{count} résultats  |  {ts}",
                                  font_size=dp(10), color=hex_to_color(TEXT_SECONDARY),
                                  size_hint_y=None, height=dp(18)))
            self.history_box.add_widget(card)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN INDEXATION
# ══════════════════════════════════════════════════════════════════════
class IndexingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(500))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Indexation des documents", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Stats
        self.stat_labels = {}
        stats_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(100))
        for title in ["Documents", "Passages", "Vocabulaire"]:
            card = BoxLayout(orientation='vertical', padding=dp(8))
            create_card_bg(card)
            val = Label(text="0", font_size=dp(18), bold=True,
                        color=hex_to_color(PRIMARY), size_hint_y=None, height=dp(24))
            card.add_widget(val)
            card.add_widget(Label(text=title, font_size=dp(10),
                                  color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(16)))
            stats_grid.add_widget(card)
            self.stat_labels[title] = val
        layout.add_widget(stats_grid)

        # Statut
        self.status_label = Label(text="En attente", font_size=dp(13),
                                  color=hex_to_color(ACCENT_ORANGE), size_hint_y=None, height=dp(24))
        layout.add_widget(self.status_label)

        # Bouton
        self.index_btn = Button(text="Démarrer l'indexation", size_hint_y=None, height=dp(44),
                                background_color=hex_to_color(PRIMARY),
                                color=hex_to_color(BG_DARK), bold=True)
        self.index_btn.bind(on_press=self.start_indexing)
        layout.add_widget(self.index_btn)

        # Log
        self.log_label = Label(text="", font_size=dp(11), color=hex_to_color(TEXT_SECONDARY),
                               size_hint_y=None, height=dp(100), halign='left', valign='top',
                               text_size=(dp(300), None))
        layout.add_widget(self.log_label)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self):
        app = App.get_running_app()
        stats = app.get_stats()
        if self.stat_labels:
            self.stat_labels["Documents"].text = str(stats.get("total_documents", 0))
            self.stat_labels["Passages"].text = str(stats.get("total_chunks", 0))
            vocab = app.db.fetchone("SELECT COUNT(*) as cnt FROM vocabulary")
            self.stat_labels["Vocabulaire"].text = str(vocab["cnt"] if vocab else 0)

    def start_indexing(self, instance):
        self.index_btn.disabled = True
        self.status_label.text = "Indexation en cours..."
        self.status_label.color = hex_to_color(ACCENT_ORANGE)

        def _run():
            try:
                from core.indexer import DocumentIndexer
                app = App.get_running_app()
                indexer = DocumentIndexer(app.db)
                indexer.index_all()
                Clock.schedule_once(lambda dt: self._done(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self._error(err), 0)

        threading.Thread(target=_run, daemon=True).start()

    def _done(self):
        self.index_btn.disabled = False
        self.status_label.text = "Indexation terminée!"
        self.status_label.color = hex_to_color(ACCENT_GREEN)
        app = App.get_running_app()
        app.engine._load_vocab_cache()
        self.on_enter()

    def _error(self, msg):
        self.index_btn.disabled = False
        self.status_label.text = f"Erreur: {msg}"
        self.status_label.color = hex_to_color(ACCENT_RED)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN AJOUTER DOCUMENT
# ══════════════════════════════════════════════════════════════════════
class ImportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(650))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Ajouter un document", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Champs
        self.fields = {}
        field_defs = [
            ("title", "Titre *", True), ("author", "Auteur", False),
            ("source", "Source", False), ("period", "Période", False),
            ("region", "Région", False),
        ]

        for name, label, required in field_defs:
            layout.add_widget(Label(text=label, font_size=dp(12),
                                    color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(20)))
            inp = TextInput(hint_text=f"Saisir {label.lower().replace(' *', '')}...",
                            multiline=False, size_hint_y=None, height=dp(36),
                            background_color=hex_to_color(BG_CARD),
                            foreground_color=hex_to_color(TEXT_PRIMARY),
                            hint_color=hex_to_color(TEXT_SECONDARY),
                            padding=[dp(8), dp(8)])
            layout.add_widget(inp)
            self.fields[name] = (inp, required)

        # Contenu
        layout.add_widget(Label(text="Contenu *", font_size=dp(12),
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(20)))
        self.content_input = TextInput(hint_text="Saisir le contenu du document...",
                                       multiline=True, size_hint_y=None, height=dp(120),
                                       background_color=hex_to_color(BG_CARD),
                                       foreground_color=hex_to_color(TEXT_PRIMARY),
                                       hint_color=hex_to_color(TEXT_SECONDARY),
                                       padding=[dp(8), dp(8)])
        layout.add_widget(self.content_input)

        # Bouton
        import_btn = Button(text="Importer et indexer", size_hint_y=None, height=dp(44),
                            background_color=hex_to_color(PRIMARY),
                            color=hex_to_color(BG_DARK), bold=True)
        import_btn.bind(on_press=self.import_document)
        layout.add_widget(import_btn)

        self.status_label = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(24))
        layout.add_widget(self.status_label)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def import_document(self, instance):
        title = self.fields["title"][0].text.strip()
        content = self.content_input.text.strip()

        if not title:
            self.status_label.text = "Le titre est obligatoire"
            self.status_label.color = hex_to_color(ACCENT_RED)
            return
        if not content:
            self.status_label.text = "Le contenu est obligatoire"
            self.status_label.color = hex_to_color(ACCENT_RED)
            return

        try:
            app = App.get_running_app()
            from utils.datetime import now_local_str
            doc_id = insert_document(
                app.db._get_connection(),
                titre=title,
                contenu=content,
                fichier=f"saisie_{now_local_str().replace('/', '_').replace(' ', '_').replace(':', '')}.txt",
                auteur=self.fields["author"][0].text.strip(),
                source=self.fields["source"][0].text.strip(),
                periode=self.fields["period"][0].text.strip(),
                region=self.fields["region"][0].text.strip(),
            )
            self.status_label.text = f"Document {doc_id} enregistré!"
            self.status_label.color = hex_to_color(ACCENT_GREEN)
            # Vider les champs
            for inp, _ in self.fields.values():
                inp.text = ''
            self.content_input.text = ''
        except Exception as e:
            self.status_label.text = f"Erreur: {e}"
            self.status_label.color = hex_to_color(ACCENT_RED)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN EXPORT
# ══════════════════════════════════════════════════════════════════════
class ExportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y)

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Export des documents", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        layout.add_widget(Label(text="Choisir le format d'export:",
                                font_size=dp(13), color=hex_to_color(TEXT_SECONDARY),
                                size_hint_y=None, height=dp(24)))

        self.format_spinner = Spinner(
            text='CSV', values=['CSV', 'JSON'],
            size_hint_y=None, height=dp(40),
            background_color=hex_to_color(BG_CARD),
            color=hex_to_color(TEXT_PRIMARY))
        layout.add_widget(self.format_spinner)

        export_btn = Button(text="Exporter", size_hint_y=None, height=dp(44),
                            background_color=hex_to_color(PRIMARY),
                            color=hex_to_color(BG_DARK), bold=True)
        export_btn.bind(on_press=self.do_export)
        layout.add_widget(export_btn)

        self.status_label = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(24))
        layout.add_widget(self.status_label)

        layout.add_widget(Label())  # spacer
        self.add_widget(layout)

    def do_export(self, instance):
        import csv
        import json
        from datetime import datetime
        try:
            app = App.get_running_app()
            docs = [dict(row) for row in app.db.fetchall("SELECT * FROM documents")]
            if not docs:
                self.status_label.text = "Aucun document à exporter"
                self.status_label.color = hex_to_color(ACCENT_ORANGE)
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fmt = self.format_spinner.text
            filename = f"atlas_export_{timestamp}.{fmt.lower()}"

            # Sauvegarder dans le répertoire de l'app
            from pathlib import Path
            import sys
            if sys.platform == 'android':
                from android.storage import app_storage_path
                export_dir = Path(app_storage_path()) / "exports"
            else:
                export_dir = Path(__file__).resolve().parent.parent / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            filepath = export_dir / filename

            if fmt == "CSV":
                fields = ["id", "title", "author", "source", "period", "region",
                          "language", "doc_type", "date_publication", "total_pages"]
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    for doc in docs:
                        writer.writerow({field: doc.get(field, "") for field in fields})
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2, default=str)

            self.status_label.text = f"Exporté: {filename}"
            self.status_label.color = hex_to_color(ACCENT_GREEN)
        except Exception as e:
            self.status_label.text = f"Erreur: {e}"
            self.status_label.color = hex_to_color(ACCENT_RED)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN RÉINITIALISER
# ══════════════════════════════════════════════════════════════════════
class ResetScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(500))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Réinitialisation de la base", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Stats actuelles
        self.stats_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        create_card_bg(self.stats_box)
        self.stats_label = Label(text="Chargement...", font_size=dp(13),
                                 color=hex_to_color(TEXT_SECONDARY))
        self.stats_box.add_widget(self.stats_label)
        layout.add_widget(self.stats_box)

        # Tout supprimer
        layout.add_widget(Label(text="Réinitialisation complète", font_size=dp(16), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(28)))
        layout.add_widget(Label(text="Supprime TOUS les données : documents, index, vocabulaire, historique.",
                                font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                                size_hint_y=None, height=dp(30)))

        reset_all_btn = Button(text="Réinitialiser tout", size_hint_y=None, height=dp(44),
                               background_color=hex_to_color(ACCENT_RED),
                               color=hex_to_color(TEXT_PRIMARY), bold=True)
        reset_all_btn.bind(on_press=lambda x: self.do_reset(full=True))
        layout.add_widget(reset_all_btn)

        # Documents seulement
        layout.add_widget(Label(text="Supprimer les documents", font_size=dp(16), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(28)))
        layout.add_widget(Label(text="Supprime documents et index. Conserve l'historique.",
                                font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                                size_hint_y=None, height=dp(30)))

        reset_docs_btn = Button(text="Supprimer les documents", size_hint_y=None, height=dp(44),
                                background_color=hex_to_color(ACCENT_RED),
                                color=hex_to_color(TEXT_PRIMARY), bold=True)
        reset_docs_btn.bind(on_press=lambda x: self.do_reset(full=False))
        layout.add_widget(reset_docs_btn)

        self.status_label = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(30))
        layout.add_widget(self.status_label)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self):
        app = App.get_running_app()
        try:
            docs = app.db.fetchone("SELECT COUNT(*) as cnt FROM documents")["cnt"]
            chunks = app.db.fetchone("SELECT COUNT(*) as cnt FROM chunks")["cnt"]
            vocab = app.db.fetchone("SELECT COUNT(*) as cnt FROM vocabulary")["cnt"]
            searches = app.db.fetchone("SELECT COUNT(*) as cnt FROM search_history")["cnt"]
            self.stats_label.text = f"Documents: {docs}  |  Passages: {chunks}  |  Termes: {vocab}  |  Recherches: {searches}"
        except Exception:
            self.stats_label.text = "Erreur de lecture"

    def do_reset(self, full=False):
        try:
            app = App.get_running_app()
            conn = app.db._get_connection()
            from database.database import reset_database, reset_documents_only
            if full:
                stats = reset_database(conn)
                self.status_label.text = f"Réinitialisation terminée!"
            else:
                stats = reset_documents_only(conn)
                self.status_label.text = f"Documents supprimés!"
            self.status_label.color = hex_to_color(ACCENT_GREEN)
            conn.close()
            app.engine._load_vocab_cache()
            self.on_enter()
        except Exception as e:
            self.status_label.text = f"Erreur: {e}"
            self.status_label.color = hex_to_color(ACCENT_RED)


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN SAUVEGARDE
# ══════════════════════════════════════════════════════════════════════
class BackupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(800))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="Gestion des sauvegardes", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))
        layout.add_widget(Label(text="Créez, restaurez et supprimez des copies de sécurité.",
                                font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                                size_hint_y=None, height=dp(20)))

        # ── Nouvelle sauvegarde ──
        create_card = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6),
                                size_hint_y=None, height=dp(140))
        create_card_bg(create_card)
        create_card.add_widget(Label(text="Nouvelle sauvegarde", font_size=dp(16), bold=True,
                                     color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(26)))
        create_card.add_widget(Label(text="Nom", font_size=dp(11),
                                     color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(18)))
        self.name_input = TextInput(hint_text="Ex: avant_modifs, avant_import...",
                                    multiline=False, size_hint_y=None, height=dp(36),
                                    background_color=hex_to_color(BG_INPUT),
                                    foreground_color=hex_to_color(TEXT_PRIMARY),
                                    hint_color=hex_to_color(TEXT_SECONDARY),
                                    padding=[dp(8), dp(8)])
        create_card.add_widget(self.name_input)
        save_btn = Button(text="Sauvegarder", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(PRIMARY),
                          color=hex_to_color(BG_DARK), bold=True)
        save_btn.bind(on_press=self.create_backup)
        create_card.add_widget(save_btn)
        layout.add_widget(create_card)

        self.create_status = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(22))
        layout.add_widget(self.create_status)

        # ── Sauvegardes existantes ──
        layout.add_widget(Label(text="Sauvegardes existantes", font_size=dp(16), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(28)))

        self.backups_box = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        self.backups_box.bind(minimum_height=self.backups_box.setter('height'))
        layout.add_widget(self.backups_box)

        refresh_btn = Button(text="Rafraîchir", size_hint_y=None, height=dp(40),
                             background_color=hex_to_color(BG_CARD),
                             color=hex_to_color(TEXT_PRIMARY))
        refresh_btn.bind(on_press=lambda x: self.refresh_list())
        layout.add_widget(refresh_btn)

        self.list_status = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(22))
        layout.add_widget(self.list_status)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def on_enter(self):
        self.refresh_list()

    def refresh_list(self):
        self.backups_box.clear_widgets()
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        backups = []
        for f in sorted(BACKUPS_DIR.glob("*.db"), key=os.path.getmtime, reverse=True):
            stat = f.stat()
            backups.append({
                "path": f,
                "name": f.stem,
                "filename": f.name,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime),
            })

        if not backups:
            self.backups_box.add_widget(Label(text="Aucune sauvegarde disponible.",
                                              font_size=dp(13), color=hex_to_color(TEXT_MUTED),
                                              size_hint_y=None, height=dp(30)))
            return

        for backup in backups:
            card = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(4),
                             size_hint_y=None, height=dp(100))
            create_card_bg(card)

            date_str = backup["mtime"].strftime("%d %b %Y  %H:%M")
            size_str = self._format_size(backup["size"])

            card.add_widget(Label(text=backup["name"], font_size=dp(14), bold=True,
                                  color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(22),
                                  halign='left', text_size=(dp(280), None)))
            card.add_widget(Label(text=f"{date_str}  ·  {size_str}",
                                  font_size=dp(11), color=hex_to_color(TEXT_SECONDARY),
                                  size_hint_y=None, height=dp(18)))

            btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36),
                                spacing=dp(8))
            restore_btn = Button(text="Restaurer", background_color=hex_to_color(PRIMARY),
                                 color=hex_to_color(BG_DARK), font_size=dp(12), bold=True)
            restore_btn.bind(on_press=lambda x, b=backup: self.restore_backup(b))
            btn_row.add_widget(restore_btn)

            delete_btn = Button(text="Supprimer", background_color=hex_to_color(ACCENT_RED),
                                color=hex_to_color(TEXT_PRIMARY), font_size=dp(12), bold=True)
            delete_btn.bind(on_press=lambda x, b=backup: self.delete_backup(b))
            btn_row.add_widget(delete_btn)

            card.add_widget(btn_row)
            self.backups_box.add_widget(card)

    def create_backup(self, instance):
        raw_name = self.name_input.text.strip()
        if not raw_name:
            self.create_status.text = "Veuillez saisir un nom."
            self.create_status.color = hex_to_color(ACCENT_RED)
            return

        if not DATABASE_PATH.exists():
            self.create_status.text = "Base de données introuvable."
            self.create_status.color = hex_to_color(ACCENT_RED)
            return

        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in raw_name).strip().replace(" ", "_")
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = BACKUPS_DIR / f"{safe_name}_{timestamp}.db"

        try:
            import shutil
            shutil.copy2(str(DATABASE_PATH), str(filename))
            self.name_input.text = ""
            self.create_status.text = f"Sauvegarde créée : {filename.name}"
            self.create_status.color = hex_to_color(ACCENT_GREEN)
            Clock.schedule_once(lambda dt: self._clear_status(self.create_status), 4)
            self.refresh_list()
        except Exception as e:
            self.create_status.text = f"Erreur : {e}"
            self.create_status.color = hex_to_color(ACCENT_RED)
            Clock.schedule_once(lambda dt: self._clear_status(self.create_status), 4)

    def restore_backup(self, backup):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text=f"Voulez-vous restaurer « {backup['name']} » ?\n\n"
                 "La base actuelle sera remplacée.",
            font_size=dp(13), color=hex_to_color(TEXT_PRIMARY),
            halign='center', text_size=(dp(280), None)))

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44),
                            spacing=dp(10))
        cancel_btn = Button(text="Annuler", background_color=hex_to_color(BG_CARD),
                            color=hex_to_color(TEXT_PRIMARY))
        confirm_btn = Button(text="Restaurer", background_color=hex_to_color(PRIMARY),
                             color=hex_to_color(BG_DARK), bold=True)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title="Confirmer la restauration", content=content,
                      size_hint=(0.85, 0.35), auto_dismiss=False,
                      background_color=hex_to_color(BG_DARK))
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=lambda x: self._do_restore(backup, popup))
        popup.open()

    def _do_restore(self, backup, popup):
        popup.dismiss()
        try:
            import shutil
            app = App.get_running_app()
            if app.db._keeper is not None:
                app.db._keeper.close()
                app.db._keeper = None

            shutil.copy2(str(backup["path"]), str(DATABASE_PATH))

            app.db = Database(DATABASE_PATH)
            app.engine = SearchEngine(app.db)

            self.list_status.text = f"Restauration réussie : {backup['name']}"
            self.list_status.color = hex_to_color(ACCENT_GREEN)
            Clock.schedule_once(lambda dt: self._clear_status(self.list_status), 4)
            self.refresh_list()
        except Exception as e:
            self.list_status.text = f"Erreur : {e}"
            self.list_status.color = hex_to_color(ACCENT_RED)
            Clock.schedule_once(lambda dt: self._clear_status(self.list_status), 4)

    def delete_backup(self, backup):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text=f"Supprimer « {backup['name']} » ?\nCette action est irréversible.",
            font_size=dp(13), color=hex_to_color(TEXT_PRIMARY),
            halign='center', text_size=(dp(280), None)))

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(44),
                            spacing=dp(10))
        cancel_btn = Button(text="Annuler", background_color=hex_to_color(BG_CARD),
                            color=hex_to_color(TEXT_PRIMARY))
        confirm_btn = Button(text="Supprimer", background_color=hex_to_color(ACCENT_RED),
                             color=hex_to_color(TEXT_PRIMARY), bold=True)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title="Confirmer la suppression", content=content,
                      size_hint=(0.85, 0.3), auto_dismiss=False,
                      background_color=hex_to_color(BG_DARK))
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_btn.bind(on_press=lambda x: self._do_delete(backup, popup))
        popup.open()

    def _do_delete(self, backup, popup):
        popup.dismiss()
        try:
            backup["path"].unlink()
            self.list_status.text = f"Supprimé : {backup['name']}"
            self.list_status.color = hex_to_color(ACCENT_GREEN)
            Clock.schedule_once(lambda dt: self._clear_status(self.list_status), 4)
            self.refresh_list()
        except Exception as e:
            self.list_status.text = f"Erreur : {e}"
            self.list_status.color = hex_to_color(ACCENT_RED)
            Clock.schedule_once(lambda dt: self._clear_status(self.list_status), 4)

    @staticmethod
    def _clear_status(label):
        label.text = ""

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} o"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.0f} Ko"
        return f"{size_bytes / (1024 * 1024):.1f} Mo"


# ══════════════════════════════════════════════════════════════════════
# ÉCRAN À PROPOS
# ══════════════════════════════════════════════════════════════════════
class AboutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView()
        layout = BoxLayout(orientation='vertical', padding=PAD_X, spacing=PAD_Y,
                           size_hint_y=None, min_height=dp(600))
        layout.bind(minimum_height=layout.setter('height'))

        back_btn = Button(text="← Retour", size_hint_y=None, height=dp(40),
                          background_color=hex_to_color(BG_CARD),
                          color=hex_to_color(TEXT_PRIMARY))
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'home'))
        layout.add_widget(back_btn)

        layout.add_widget(Label(text="À propos du projet", font_size=dp(22), bold=True,
                                color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(36)))

        # Carte principale
        main_card = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(6),
                              size_hint_y=None, height=dp(180))
        create_card_bg(main_card)
        _lp = _get_logo_path()
        if _lp:
            from kivy.uix.image import Image as KivyImage
            main_card.add_widget(KivyImage(source=_lp, size_hint_y=None,
                                           height=dp(80), allow_stretch=True))
        else:
            main_card.add_widget(Label(text="🧭", font_size=dp(40),
                                       size_hint_y=None, height=dp(45)))
        main_card.add_widget(Label(text="Atlas", font_size=dp(26), bold=True,
                                   color=hex_to_color(PRIMARY), size_hint_y=None, height=dp(32)))
        main_card.add_widget(Label(text="Moteur de recherche de documents historiques",
                                   font_size=dp(12), color=hex_to_color(TEXT_SECONDARY),
                                   size_hint_y=None, height=dp(18)))
        main_card.add_widget(Label(text="Version 1.0.0", font_size=dp(11),
                                   color=hex_to_color(TEXT_MUTED), size_hint_y=None, height=dp(16)))
        main_card.add_widget(Label(
            text="Projet académique — Groupe 5\nIFOAD — Université Joseph Ki-Zerbo\nAnnée 2025-2026",
            font_size=dp(11), color=hex_to_color(TEXT_SECONDARY),
            size_hint_y=None, height=dp(48), halign='center'))
        layout.add_widget(main_card)

        # Équipe
        team_card = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(4),
                              size_hint_y=None, height=dp(220))
        create_card_bg(team_card)
        team_card.add_widget(Label(text="Équipe de développement", font_size=dp(16), bold=True,
                                   color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(26)))

        team = [
            ("SORE Abdoul Fadal", "Chef de projet & Intégration"),
            ("SAWADOGO Idrissa", "Base de données SQLite"),
            ("GOUEM Aboubacar Sidiki", "Prétraitement NLP"),
            ("SAWADOGO Djemila", "TF-IDF et moteur de recherche"),
            ("DICKO Idrissa Barkey Kalilou", "Interface graphique"),
        ]
        for name, role in team:
            team_card.add_widget(Label(text=f"👤 {name}", font_size=dp(12), bold=True,
                                       color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(18)))
            team_card.add_widget(Label(text=f"   {role}", font_size=dp(11),
                                       color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(16)))
        layout.add_widget(team_card)

        # Technologies
        tech_card = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(4),
                              size_hint_y=None, height=dp(180))
        create_card_bg(tech_card)
        tech_card.add_widget(Label(text="Technologies", font_size=dp(16), bold=True,
                                   color=hex_to_color(TEXT_PRIMARY), size_hint_y=None, height=dp(26)))
        techs = "Python • scikit-learn • NLTK • SQLite • Kivy • CustomTkinter"
        tech_card.add_widget(Label(text=techs, font_size=dp(11),
                                   color=hex_to_color(TEXT_SECONDARY), size_hint_y=None, height=dp(20),
                                   halign='center', text_size=(dp(300), None)))
        layout.add_widget(tech_card)

        scroll.add_widget(layout)
        self.add_widget(scroll)


# ══════════════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════
class AtlasAndroidApp(App):
    """Application Atlas pour Android."""

    def build(self):
        self.title = "Atlas"
        self.icon = "assets/icons/icon.png"
        self.db = Database()
        self.engine = SearchEngine(self.db)

        sm = ScreenManager(transition=SlideTransition(direction='left'))

        screens = [
            ('home', HomeScreen),
            ('search', SearchScreen),
            ('advanced', AdvancedScreen),
            ('analytics', AnalyticsScreen),
            ('history', HistoryScreen),
            ('indexing', IndexingScreen),
            ('import', ImportScreen),
            ('export', ExportScreen),
            ('backup', BackupScreen),
            ('reset', ResetScreen),
            ('about', AboutScreen),
        ]

        for name, cls in screens:
            sm.add_widget(cls(name=name))

        return sm

    def search(self, query, **filters):
        try:
            results, total, elapsed = self.engine.search(query, limit=20, **filters)
            search_screen = self.root.get_screen('search')
            search_screen.search_input.text = query
            search_screen.show_results(results, total, elapsed)
            self.root.current = 'search'
        except Exception as e:
            print(f"Erreur de recherche: {e}")

    def get_stats(self):
        return self.engine.get_stats()
