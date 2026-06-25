import re
import unicodedata
from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

from src.utils.constants import MIN_WORD_LENGTH, FRENCH_STOP_WORDS, FRENCH_STEMMER


nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)


class TextPreprocessor:
    """Nettoyage, tokenisation, lemmatisation et normalisation du texte."""

    def __init__(self, language: str = "french"):
        self.language = language
        self.stemmer = SnowballStemmer(language)
        try:
            self.stop_words = set(stopwords.words(language))
        except OSError:
            self.stop_words = set(FRENCH_STOP_WORDS)

    def clean_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("utf-8")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[^\w\s'-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    def tokenize(self, text: str) -> List[str]:
        cleaned = self.clean_text(text)
        tokens = word_tokenize(cleaned, language=self.language)
        tokens = [
            t for t in tokens
            if len(t) >= MIN_WORD_LENGTH
            and t not in self.stop_words
            and not t.isdigit()
        ]
        return tokens

    def stem(self, tokens: List[str]) -> List[str]:
        return [self.stemmer.stem(t) for t in tokens]

    def process(self, text: str) -> List[str]:
        tokens = self.tokenize(text)
        return self.stem(tokens)

    def process_queries(self, query: str) -> List[str]:
        return self.process(query)
