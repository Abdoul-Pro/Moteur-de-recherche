"""
Utility functions for date and time handling in Atlas.
Provides localized date/time formatting.
"""

from datetime import datetime


def now_local_str() -> str:
    """
    Retourne la date et l'heure locale actuelle formatée selon les normes Atlas.

    Format : JJ/MM/AAAA à HH:MM:SS

    Returns:
        str: Date et heure locale formatée.
    """
    return datetime.now().strftime("%d/%m/%Y à %H:%M:%S")


def now_local_date() -> str:
    """
    Retourne la date locale actuelle au format JJ/MM/AAAA.

    Returns:
        str: Date locale formatée.
    """
    return datetime.now().strftime("%d/%m/%Y")


def now_local_time() -> str:
    """
    Retourne l'heure locale actuelle au format HH:MM:SS.

    Returns:
        str: Heure locale formatée.
    """
    return datetime.now().strftime("%H:%M:%S")