"""
theme.py — Thème et couleurs pour l'interface Windows (CustomTkinter).
"""

import customtkinter as ctk

from config import WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_TITLE

BG_DARK = "#0a1628"
BG_SIDEBAR = "#0c1d36"
BG_CARD = "#0f2042"
BG_INPUT = "#0a1628"
BG_HOVER = "#162d54"

PRIMARY = "#d4a843"
PRIMARY_HOVER = "#e6b955"
PRIMARY_DARK = "#b8922e"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#8899b3"
TEXT_MUTED = "#556680"

ACCENT_BLUE = "#3a7bd5"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_ORANGE = "#f39c12"

BORDER = "#1a3055"
BORDER_LIGHT = "#234070"

SUCCESS = "#2ecc71"
WARNING = "#f39c12"
ERROR = "#e74c3c"
INFO = "#3498db"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 16, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_STAT = (FONT_FAMILY, 28, "bold")
FONT_ICON = (FONT_FAMILY, 18)
FONT_SIDEBAR = (FONT_FAMILY, 13)
FONT_SIDEBAR_ACTIVE = (FONT_FAMILY, 13, "bold")

CORNER_RADIUS = 8
CORNER_RADIUS_LG = 12
CORNER_RADIUS_SM = 6

PAD_X = 20
PAD_Y = 15
PAD_SM = 8

NAV_ITEMS = [
    ("Accueil", "🏠"),
    ("Recherche", "🔍"),
    ("Recherche avancée", "🔬"),
    ("Analyse", "📊"),
    ("Historique", "📋"),
    ("Indexation", "⚙️"),
    ("Ajouter un document", "📄"),
    ("Export", "📤"),
    ("Sauvegarde", "💾"),
    ("Réinitialiser", "🗑️"),
    ("À propos", "ℹ️"),
]


def configure_appearance():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def create_card(parent, **kwargs) -> ctk.CTkFrame:
    defaults = {
        "fg_color": BG_CARD,
        "corner_radius": CORNER_RADIUS_LG,
        "border_width": 1,
        "border_color": BORDER,
    }
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def create_button(parent, text: str, command=None, style: str = "primary", **kwargs) -> ctk.CTkButton:
    styles = {
        "primary": {"fg_color": PRIMARY, "hover_color": PRIMARY_HOVER, "text_color": BG_DARK},
        "secondary": {"fg_color": BG_CARD, "hover_color": BG_HOVER, "text_color": TEXT_PRIMARY, "border_width": 1, "border_color": BORDER},
        "danger": {"fg_color": ACCENT_RED, "hover_color": "#c0392b", "text_color": TEXT_PRIMARY},
        "ghost": {"fg_color": "transparent", "hover_color": BG_HOVER, "text_color": TEXT_SECONDARY},
    }
    defaults = {
        "text": text,
        "command": command,
        "corner_radius": CORNER_RADIUS,
        "font": FONT_BODY,
        "height": 38,
    }
    defaults.update(styles.get(style, styles["primary"]))
    defaults.update(kwargs)
    return ctk.CTkButton(parent, **defaults)


def create_entry(parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
    defaults = {
        "placeholder_text": placeholder,
        "fg_color": BG_INPUT,
        "border_color": BORDER,
        "text_color": TEXT_PRIMARY,
        "font": FONT_BODY,
        "corner_radius": CORNER_RADIUS,
        "height": 38,
    }
    defaults.update(kwargs)
    return ctk.CTkEntry(parent, **defaults)


def create_label(parent, text: str, style: str = "body", **kwargs) -> ctk.CTkLabel:
    styles = {
        "title": {"font": FONT_TITLE, "text_color": TEXT_PRIMARY},
        "subtitle": {"font": FONT_SUBTITLE, "text_color": TEXT_PRIMARY},
        "body": {"font": FONT_BODY, "text_color": TEXT_PRIMARY},
        "small": {"font": FONT_SMALL, "text_color": TEXT_SECONDARY},
        "muted": {"font": FONT_SMALL, "text_color": TEXT_MUTED},
        "stat": {"font": FONT_STAT, "text_color": PRIMARY},
    }
    defaults = {"text": text}
    defaults.update(styles.get(style, styles["body"]))
    defaults.update(kwargs)
    return ctk.CTkLabel(parent, **defaults)
