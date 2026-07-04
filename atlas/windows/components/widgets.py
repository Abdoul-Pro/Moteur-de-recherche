"""
widgets.py — Composants réutilisables pour l'interface Windows.
"""

import re
import customtkinter as ctk
from windows.theme import (
    BG_CARD, BG_HOVER, BG_INPUT, BORDER, BORDER_LIGHT,
    PRIMARY, PRIMARY_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    FONT_BODY, FONT_SMALL, FONT_STAT, CORNER_RADIUS, CORNER_RADIUS_LG,
    create_card, create_entry, create_button, create_label,
)


class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, on_search=None, on_clear=None, placeholder="Rechercher...", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search
        self._on_clear = on_clear

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.entry = create_entry(self, placeholder=placeholder)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", self._handle_search)
        self.entry.bind("<KeyRelease>", self._handle_key)

        self.btn = create_button(self, "Rechercher", command=self._handle_search, width=120)
        self.btn.grid(row=0, column=1)

    def get_query(self) -> str:
        return self.entry.get().strip()

    def set_query(self, text: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

    def _handle_key(self, event=None):
        if not self.entry.get().strip() and self._on_clear:
            self._on_clear()

    def _handle_search(self, event=None):
        query = self.get_query()
        if query and self._on_search:
            self._on_search(query)


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, icon: str = "", **kwargs):
        super().__init__(parent, **{
            "fg_color": BG_CARD,
            "corner_radius": CORNER_RADIUS_LG,
            "border_width": 1,
            "border_color": BORDER,
            **kwargs
        })

        self.columnconfigure(0, weight=1)

        if icon:
            create_label(self, icon, style="body", font=("Segoe UI", 22)).grid(
                row=0, column=0, sticky="w", padx=15, pady=(12, 0))

        create_label(self, value, style="stat").grid(
            row=1, column=0, sticky="w", padx=15, pady=(4, 0))

        create_label(self, title, style="small").grid(
            row=2, column=0, sticky="w", padx=15, pady=(0, 12))


class ResultCard(ctk.CTkFrame):
    def __init__(self, parent, result: dict, index: int = 0,
                 on_click=None, query_terms=None, **kwargs):
        super().__init__(parent, **{
            "fg_color": BG_CARD,
            "corner_radius": CORNER_RADIUS_LG,
            "border_width": 1,
            "border_color": BORDER,
            **kwargs
        })
        self._result = result
        self._query_terms = query_terms or []

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        idx_label = create_label(self, f"{index + 1}", style="body",
                                 text_color=PRIMARY, font=("Segoe UI", 16, "bold"))
        idx_label.grid(row=0, column=0, sticky="nw", padx=(15, 5), pady=(12, 0))

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="ew", padx=(35, 0), pady=(12, 12))
        content_frame.columnconfigure(0, weight=1)

        title_text = result.get("title", "")
        if self._query_terms:
            title_label = ctk.CTkLabel(content_frame, text="",
                                       font=("Segoe UI", 14, "bold"),
                                       text_color=TEXT_PRIMARY, anchor="w",
                                       justify="left")
            title_label.grid(row=0, column=0, sticky="ew")
            self._insert_highlighted(title_label, title_text, self._query_terms)
        else:
            create_label(content_frame, title_text, style="subtitle").grid(
                row=0, column=0, sticky="ew")

        snippet = result.get("snippet", "")
        if len(snippet) > 350:
            snippet = snippet[:350] + "..."
        if self._query_terms and snippet:
            snippet_label = ctk.CTkLabel(content_frame, text="",
                                         font=("Segoe UI", 11),
                                         text_color=TEXT_SECONDARY, anchor="w",
                                         justify="left", wraplength=550)
            snippet_label.grid(row=1, column=0, sticky="ew", pady=(4, 0))
            self._insert_highlighted(snippet_label, snippet, self._query_terms)
        elif snippet:
            create_label(content_frame, snippet, style="small", wraplength=550).grid(
                row=1, column=0, sticky="ew", pady=(4, 0))

        meta_parts = []
        if result.get("author"):
            meta_parts.append(f"Auteur: {result['author']}")
        if result.get("period"):
            meta_parts.append(result["period"])
        if result.get("region"):
            meta_parts.append(result["region"])
        meta_text = " · ".join(meta_parts)
        if meta_text:
            create_label(content_frame, meta_text, style="muted").grid(
                row=2, column=0, sticky="ew", pady=(4, 0))

        score = result.get("score", 0)
        score_frame = ctk.CTkFrame(self, fg_color="transparent")
        score_frame.grid(row=0, column=1, padx=15, pady=(12, 0), sticky="ne")

        create_label(score_frame, f"{score}%", style="body",
                     text_color=PRIMARY, font=("Segoe UI", 14, "bold")).grid(row=0, column=0)
        create_label(score_frame, "Pertinence", style="muted").grid(row=1, column=0)

        if on_click:
            def _click(e):
                on_click(result)
            self.bind("<Button-1>", _click)
            self._bind_recursive(self, _click)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _bind_recursive(self, widget, callback):
        for child in widget.winfo_children():
            try:
                child.bind("<Button-1>", callback)
            except Exception:
                pass
            self._bind_recursive(child, callback)

    def _insert_highlighted(self, label, text, terms):
        import re as _re
        if not terms:
            label.configure(text=text)
            return
        pattern = "|".join(_re.escape(t) for t in terms if t)
        if not pattern:
            label.configure(text=text)
            return
        parts = _re.split(f"({pattern})", text, flags=_re.IGNORECASE)
        full_text = ""
        for part in parts:
            is_match = any(part.lower() == t.lower() for t in terms if t)
            if is_match:
                full_text += f"»{part}«"
            else:
                full_text += part
        label.configure(text=full_text)

    def _on_enter(self, e):
        self.configure(border_color=BORDER_LIGHT)

    def _on_leave(self, e):
        self.configure(border_color=BORDER)


class Pagination(ctk.CTkFrame):
    def __init__(self, parent, total_pages: int, current_page: int = 1,
                 on_page_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._total_pages = total_pages
        self._current = current_page
        self._on_page_change = on_page_change

        if total_pages <= 1:
            return

        if current_page > 1:
            btn = create_button(self, "←", command=lambda: self._go(current_page - 1),
                                style="secondary", width=36, height=36)
            btn.grid(row=0, column=0, padx=2)

        start = max(1, current_page - 2)
        end = min(total_pages, current_page + 2)

        for i in range(start, end + 1):
            style = "primary" if i == current_page else "secondary"
            btn = create_button(self, str(i), command=lambda p=i: self._go(p),
                                style=style, width=36, height=36)
            btn.grid(row=0, column=i - start + 1, padx=2)

        if current_page < total_pages:
            btn = create_button(self, "→", command=lambda: self._go(current_page + 1),
                                style="secondary", width=36, height=36)
            btn.grid(row=0, column=end - start + 2, padx=2)

    def _go(self, page: int):
        if self._on_page_change:
            self._on_page_change(page)
