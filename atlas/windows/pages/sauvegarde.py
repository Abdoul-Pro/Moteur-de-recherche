"""
sauvegarde.py — Page de gestion des sauvegardes de la base de données.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

import customtkinter as ctk

from config import DATABASE_PATH, BACKUPS_DIR
from windows.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, ACCENT_GREEN, ACCENT_RED,
    ACCENT_ORANGE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER,
    CORNER_RADIUS_LG, PAD_X, PAD_Y,
    create_card, create_label, create_button, create_entry,
)


class SauvegardePage(ctk.CTkFrame):
    """Page de gestion des sauvegardes de la base de données."""

    def __init__(self, parent, app_atlas=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self._app = app_atlas

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        self.scroll.columnconfigure(0, weight=1)

        self._build_ui()
        self._refresh_list()

    # ── Construction de l'interface ─────────────────────────────

    def _build_ui(self):
        create_label(self.scroll, "Gestion des sauvegardes", style="title").grid(
            row=0, column=0, sticky="w")
        create_label(self.scroll,
                     "Créez, restaurez et supprimez des copies de sécurité "
                     "de votre base de données.",
                     style="small").grid(row=1, column=0, sticky="w", pady=(0, 20))

        # ── Section : Nouvelle sauvegarde ──────────────────────
        create_card_frame = create_card(self.scroll)
        create_card_frame.grid(row=2, column=0, sticky="ew", pady=5)
        create_card_frame.columnconfigure(0, weight=1)

        create_label(create_card_frame, "Nouvelle sauvegarde",
                     style="subtitle").grid(row=0, column=0, sticky="w",
                                            padx=15, pady=(12, 5))

        name_frame = ctk.CTkFrame(create_card_frame, fg_color="transparent")
        name_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        name_frame.columnconfigure(0, weight=1)

        create_label(name_frame, "Nom", style="small").grid(
            row=0, column=0, sticky="w", pady=(0, 4))

        self.entry_name = create_entry(
            name_frame, placeholder="Ex: avant_modifs, avant_import...")
        self.entry_name.grid(row=1, column=0, sticky="ew")

        self.btn_save = create_button(
            create_card_frame, "Sauvegarder", command=self._create_backup,
            width=200)
        self.btn_save.grid(row=2, column=0, sticky="w", padx=15, pady=(5, 12))

        self.lbl_create_status = create_label(create_card_frame, "", style="small")
        self.lbl_create_status.grid(row=3, column=0, sticky="w", padx=15, pady=(0, 12))

        # ── Section : Sauvegardes existantes ───────────────────
        list_card = create_card(self.scroll)
        list_card.grid(row=3, column=0, sticky="ew", pady=5)
        list_card.columnconfigure(0, weight=1)

        create_label(list_card, "Sauvegardes existantes",
                     style="subtitle").grid(row=0, column=0, sticky="w",
                                            padx=15, pady=(12, 5))

        self.list_frame = ctk.CTkFrame(list_card, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 5))
        self.list_frame.columnconfigure(0, weight=1)

        self.lbl_empty = create_label(
            list_card, "Aucune sauvegarde disponible.",
            style="small", text_color=TEXT_MUTED)
        self.lbl_empty.grid(row=2, column=0, sticky="w", padx=15, pady=(8, 12))

        self.btn_refresh = create_button(
            list_card, "Rafraîchir", command=self._refresh_list,
            style="secondary", width=150)
        self.btn_refresh.grid(row=3, column=0, sticky="w", padx=15, pady=(0, 12))

        self.lbl_list_status = create_label(list_card, "", style="small")
        self.lbl_list_status.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 8))

    # ── Création de sauvegarde ──────────────────────────────────

    def _create_backup(self):
        raw_name = self.entry_name.get().strip()
        if not raw_name:
            self._set_status(self.lbl_create_status,
                             "Veuillez saisir un nom pour la sauvegarde.",
                             ACCENT_RED)
            return

        if not DATABASE_PATH.exists():
            self._set_status(self.lbl_create_status,
                             "Base de données introuvable.", ACCENT_RED)
            return

        safe_name = "".join(
            c if c.isalnum() or c in "-_ " else "_" for c in raw_name
        ).strip().replace(" ", "_")

        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = BACKUPS_DIR / f"{safe_name}_{timestamp}.db"

        try:
            shutil.copy2(str(DATABASE_PATH), str(filename))
            self.entry_name.delete(0, "end")
            self._set_status(self.lbl_create_status,
                             f"Sauvegarde créée : {filename.name}",
                             ACCENT_GREEN)
            self._refresh_list()
        except Exception as e:
            self._set_status(self.lbl_create_status,
                             f"Erreur : {e}", ACCENT_RED)

    # ── Liste des sauvegardes ───────────────────────────────────

    def _refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        backups = self._list_backups()

        if not backups:
            self.lbl_empty.grid(row=2, column=0, sticky="w", padx=15, pady=(8, 12))
            return

        self.lbl_empty.grid_forget()

        for idx, backup in enumerate(backups):
            self._create_backup_row(idx, backup)

    def _list_backups(self):
        if not BACKUPS_DIR.exists():
            return []

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
        return backups

    def _create_backup_row(self, idx, backup):
        row_frame = ctk.CTkFrame(self.list_frame, fg_color=BG_CARD,
                                 corner_radius=CORNER_RADIUS_LG,
                                 border_width=1, border_color=BORDER)
        row_frame.grid(row=idx, column=0, sticky="ew", pady=3)
        row_frame.columnconfigure(0, weight=1)
        row_frame.columnconfigure(1, weight=0)

        info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)

        create_label(info_frame, backup["name"],
                     style="subtitle", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, sticky="w")

        date_str = backup["mtime"].strftime("%d %b %Y  %H:%M")
        size_str = self._format_size(backup["size"])
        meta_text = f"{date_str}  ·  {size_str}"
        create_label(info_frame, meta_text, style="small").grid(
            row=1, column=0, sticky="w", pady=(2, 0))

        btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=15, pady=10)

        create_button(
            btn_frame, "Restaurer",
            command=lambda b=backup: self._restore_backup(b),
            style="primary", width=110, height=30
        ).grid(row=0, column=0, padx=(0, 5))

        create_button(
            btn_frame, "Supprimer",
            command=lambda b=backup: self._delete_backup(b),
            style="danger", width=110, height=30
        ).grid(row=0, column=1)

    # ── Restauration ────────────────────────────────────────────

    def _restore_backup(self, backup):
        popup = ctk.CTkToplevel(self)
        popup.title("Confirmer la restauration")
        popup.configure(fg_color=BG_DARK)
        popup.geometry("420x220")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(1, weight=1)

        create_label(popup, "Confirmer la restauration", style="title").grid(
            row=0, column=0, padx=20, pady=(20, 10))

        msg = (
            f"Voulez-vous restaurer la sauvegarde « {backup['name']} » ?\n\n"
            "La base de données actuelle sera remplacée.\n"
            "Cette action est irréversible."
        )
        create_label(popup, msg, style="body", wraplength=380,
                     justify="center").grid(
            row=1, column=0, padx=20, pady=10)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=(0, 20))

        create_button(btn_frame, "Annuler", command=popup.destroy,
                      style="secondary", width=120).grid(row=0, column=0, padx=5)
        create_button(btn_frame, "Restaurer",
                      command=lambda: self._do_restore(backup, popup),
                      style="primary", width=120).grid(row=0, column=1, padx=5)

    def _do_restore(self, backup, popup):
        try:
            if self._app and self._app.db._keeper is not None:
                self._app.db._keeper.close()
                self._app.db._keeper = None

            shutil.copy2(str(backup["path"]), str(DATABASE_PATH))

            if self._app:
                self._app.db = type(self._app.db)(DATABASE_PATH)
                self._app.connexion = self._app.db._get_connection()
                self._app.refresh_index_and_stats()

            popup.destroy()
            self._set_status(self.lbl_list_status,
                             f"Restauration réussie depuis « {backup['name']} »",
                             ACCENT_GREEN)
        except Exception as e:
            popup.destroy()
            self._set_status(self.lbl_list_status,
                             f"Erreur lors de la restauration : {e}",
                             ACCENT_RED)

    # ── Suppression ─────────────────────────────────────────────

    def _delete_backup(self, backup):
        popup = ctk.CTkToplevel(self)
        popup.title("Confirmer la suppression")
        popup.configure(fg_color=BG_DARK)
        popup.geometry("420x200")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(1, weight=1)

        create_label(popup, "Confirmer la suppression", style="title").grid(
            row=0, column=0, padx=20, pady=(20, 10))

        msg = (
            f"Voulez-vous supprimer la sauvegarde « {backup['name']} » ?\n\n"
            "Cette action est irréversible."
        )
        create_label(popup, msg, style="body", wraplength=380,
                     justify="center").grid(
            row=1, column=0, padx=20, pady=10)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=(0, 20))

        create_button(btn_frame, "Annuler", command=popup.destroy,
                      style="secondary", width=120).grid(row=0, column=0, padx=5)
        create_button(btn_frame, "Supprimer",
                      command=lambda: self._do_delete(backup, popup),
                      style="danger", width=120).grid(row=0, column=1, padx=5)

    def _do_delete(self, backup, popup):
        try:
            backup["path"].unlink()
            popup.destroy()
            self._set_status(self.lbl_list_status,
                             f"Sauvegarde « {backup['name']} » supprimée.",
                             ACCENT_GREEN)
            self._refresh_list()
        except Exception as e:
            popup.destroy()
            self._set_status(self.lbl_list_status,
                             f"Erreur lors de la suppression : {e}",
                             ACCENT_RED)

    # ── Utilitaires ─────────────────────────────────────────────

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} o"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.0f} Ko"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} Mo"

    def _set_status(self, label, text, color):
        label.configure(text=text, text_color=color)
        label.after(4000, lambda: label.configure(text="", text_color=TEXT_SECONDARY))
