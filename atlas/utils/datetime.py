"""
datetime.py — Utilitaires de formatage date/heure pour Atlas.
"""

from datetime import datetime


def now_local_str() -> str:
    """Retourne la date et l'heure locale actuelle formatée."""
    return datetime.now().strftime("%d/%m/%Y à %H:%M:%S")


def now_local_date() -> str:
    """Retourne la date locale actuelle."""
    return datetime.now().strftime("%d/%m/%Y")


def now_local_time() -> str:
    """Retourne l'heure locale actuelle."""
    return datetime.now().strftime("%H:%M:%S")
