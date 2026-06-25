"""Constantes partagées pour le prétraitement NLP."""

from config import MIN_WORD_LENGTH

from src.core.preprocessing import FRENCH_STOP_WORDS

FRENCH_STEMMER = "french"

__all__ = ["MIN_WORD_LENGTH", "FRENCH_STOP_WORDS", "FRENCH_STEMMER"]
