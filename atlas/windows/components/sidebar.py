"""
sidebar.py — Barre latérale de navigation pour l'interface Windows.
"""

import customtkinter as ctk
from pathlib import Path

from windows.theme import (
    BG_SIDEBAR, BG_HOVER, PRIMARY, PRIMARY_HOVER, TEXT_PRIMARY,
    TEXT_SECONDARY, BORDER, FONT_SIDEBAR, FONT_SIDEBAR_ACTIVE,
    NAV_ITEMS, CORNER_RADIUS, CORNER_RADIUS_SM, PAD_X, PAD_SM,
    create_label,
)

_LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "icon.png"


class Sidebar(ctk.CTkFrame):
    """Barre latérale de navigation."""

    def __init__(self, parent, on_navigate=None, **kwargs):
        super().__init__(parent, **{
            "fg_color": BG_SIDEBAR,
            "corner_radius": 0,
            "width": 220,
            **kwargs
        })
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._buttons = {}
        self._current = None

        self.columnconfigure(0, weight=1)

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=PAD_X, pady=(20, 5))
        logo_frame.columnconfigure(0, weight=0)
        logo_frame.columnconfigure(1, weight=1)

        try:
            from PIL import Image as PilImage
            _img = PilImage.open(str(_LOGO_PATH))
            logo_img = ctk.CTkImage(light_image=_img, dark_image=_img, size=(36, 36))
            ctk.CTkLabel(logo_frame, image=logo_img, text="").grid(
                row=0, column=0, rowspan=2, padx=(0, 8))
        except Exception:
            ctk.CTkLabel(logo_frame, text="🧭", font=("Segoe UI", 28)).grid(
                row=0, column=0, rowspan=2, padx=(0, 8))
        ctk.CTkLabel(logo_frame, text="Atlas", font=("Segoe UI", 22, "bold"),
                      text_color=PRIMARY).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(logo_frame, text="Documents historiques", font=("Segoe UI", 10),
                      text_color=TEXT_SECONDARY).grid(row=1, column=1, sticky="nw")

        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1)
        sep.grid(row=1, column=0, sticky="ew", padx=PAD_X, pady=(15, 10))

        for i, (label, icon) in enumerate(NAV_ITEMS):
            btn = self._create_nav_button(label, icon, i + 2)
            self._buttons[label] = btn

        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.grid(row=len(NAV_ITEMS) + 3, column=0, sticky="nsew")

        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=len(NAV_ITEMS) + 4, column=0, sticky="ew",
                          padx=PAD_X, pady=(0, 15))

        dot = ctk.CTkLabel(status_frame, text="●", text_color="#2ecc71",
                            font=("Segoe UI", 10))
        dot.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkLabel(status_frame, text="Statut du système", font=("Segoe UI", 10),
                      text_color=TEXT_SECONDARY).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(status_frame, text="Opérationnel", font=("Segoe UI", 9),
                      text_color="#2ecc71").grid(row=1, column=1, sticky="w")

    def _create_nav_button(self, label: str, icon: str, row: int) -> ctk.CTkButton:
        text = f"  {icon}  {label}"
        btn = ctk.CTkButton(
            self,
            text=text,
            anchor="w",
            font=FONT_SIDEBAR,
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            corner_radius=CORNER_RADIUS_SM,
            height=38,
            command=lambda l=label: self._navigate(l),
        )
        btn.grid(row=row, column=0, sticky="ew", padx=8, pady=1)
        return btn

    def _navigate(self, label: str):
        if self._current and self._current in self._buttons:
            self._buttons[self._current].configure(
                fg_color="transparent", text_color=TEXT_SECONDARY,
                font=FONT_SIDEBAR
            )

        self._current = label
        if label in self._buttons:
            self._buttons[label].configure(
                fg_color=BG_HOVER, text_color=PRIMARY,
                font=FONT_SIDEBAR_ACTIVE
            )

        if self._on_navigate:
            self._on_navigate(label)

    def set_active(self, label: str):
        if self._current and self._current in self._buttons:
            self._buttons[self._current].configure(
                fg_color="transparent", text_color=TEXT_SECONDARY,
                font=FONT_SIDEBAR
            )

        self._current = label
        if label in self._buttons:
            self._buttons[label].configure(
                fg_color=BG_HOVER, text_color=PRIMARY,
                font=FONT_SIDEBAR_ACTIVE
            )
