"""
preprocessing.py — Module de prétraitement NLP pour Atlas.

Fonctionnalités :
    1. Nettoyage du texte (HTML, Unicode, caractères spéciaux)
    2. Passage en minuscules
    3. Suppression de la ponctuation
    4. Suppression des stop words français
    5. Tokenisation
    6. Stemming (racinisation)
    7. Découpage en passages (chunking)
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

# ── Dépendances NLTK (téléchargement automatique au besoin) ──────────
try:
    import nltk
    from nltk.corpus import stopwords as _nltk_stopwords
    from nltk.stem import SnowballStemmer as _SnowballStemmer
    from nltk.tokenize import word_tokenize as _nltk_word_tokenize

    for _res in ("punkt", "punkt_tab", "stopwords"):
        nltk.download(_res, quiet=True)

    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False


# ── Stop words français embarqués (fallback si NLTK indisponible) ────
FRENCH_STOP_WORDS: set = {
    "ai", "aie", "aient", "aies", "alors", "as", "au", "aucun", "aucune",
    "aura", "aurai", "auraient", "aurais", "aurait", "auras", "aurez",
    "auriez", "aurions", "aurons", "auront", "aussi", "autre", "autres",
    "aux", "avaient", "avais", "avait", "avant", "avec", "avions", "avoir",
    "ayant", "ayez", "ayons", "bon", "c", "ça", "car", "ce", "ceci",
    "cela", "celle", "celles", "celui", "cependant", "certain", "certaine",
    "certaines", "certains", "ces", "cet", "cette", "ceux", "chacun",
    "chacune", "chaque", "che", "ci", "comme", "comment", "compris",
    "concernant", "contre", "d", "dans", "de", "debout", "dedans",
    "dehors", "delà", "depuis", "des", "desquelles", "desquels", "dessous",
    "dessus", "dessein", "devant", "devoir", "devra", "différent",
    "différente", "différentes", "différents", "dire", "divers", "diverse",
    "diverses", "doit", "donc", "dont", "du", "dû", "d'où", "duplicate",
    "elle", "elles", "en", "encore", "enfin", "entre", "er", "ès",
    "est", "et", "étaient", "étais", "était", "étant", "etc", "été",
    "être", "eu", "eue", "eues", "eurent", "eus", "eusse", "eussent",
    "eusses", "eussiez", "eussions", "eut", "eût", "f", "faire", "fais",
    "faisaient", "faisant", "fait", "faites", "façon", "fera", "ferai",
    "feraient", "ferais", "ferait", "feras", "ferez", "feriez", "ferions",
    "ferons", "feront", "fille", "fils", "fois", "font", "force", "fors",
    "furent", "fus", "fusse", "fussent", "fusses", "fussiez", "fussions",
    "fut", "fût", "g", "gens", "h", "ha", "hardi", "hein", "hem", "hi",
    "holà", "hop", "hormis", "hors", "hui", "i", "ici", "il", "ils",
    "j", "je", "jusqu", "jusque", "juste", "k", "l", "la", "laquelle",
    "le", "lequel", "les", "lesquelles", "lesquels", "leur", "leurs",
    "lorsque", "lui", "m", "ma", "maintenant", "mais", "malgré", "malgré",
    "me", "mes", "mien", "mienne", "miennes", "miens", "mieux", "mon",
    "n", "na", "naturellement", "ne", "néanmoins", "ni", "no", "nommés",
    "notre", "nôtre", "nôtres", "nous", "nul", "nulle", "o", "oh",
    "on", "ont", "onze", "ou", "où", "oui", "par", "parce", "parfois",
    "parle", "parlent", "parler", "parlé", "parlée", "parlées", "parlés",
    "partout", "pas", "passé", "pendant", "permet", "personne", "peu",
    "plupart", "plus", "plusieurs", "plutôt", "possessif", "pour",
    "pourquoi", "premier", "première", "premièrement", "près", "puis",
    "puisque", "qu", "quand", "que", "quel", "quelconque", "quelle",
    "quelles", "quelqu", "quelque", "quelques", "quels", "qui", "quoi",
    "quotidien", "quotidienne", "quotidiennement", "quotidiennes",
    "quotidiens", "r", "rien", "s", "sa", "sans", "sauf", "se",
    "semestre", "sera", "serai", "seraient", "serais", "serait", "seras",
    "serez", "seriez", "serions", "serons", "seront", "ses", "si",
    "sien", "sienne", "siennes", "siens", "sinon", "soi", "soient",
    "sommes", "son", "sont", "sous", "souvent", "soyez", "soyons",
    "subit", "suffo", "suffoque", "suffoque", "suffoquent", "suis",
    "sur", "surtout", "t", "ta", "tandis", "tant", "te", "tel",
    "telle", "tellement", "telles", "tels", "tenant", "tes", "tien",
    "tienne", "tiennes", "tiens", "toi", "ton", "toujours", "tous",
    "tout", "toute", "toutefois", "toutes", "très", "trop", "t",
    "tu", "un", "une", "v", "va", "vais", "vas", "vers", "via",
    "voient", "volontiers", "vont", "vos", "votre", "vôtre", "vôtres",
    "vous", "vu", "y",
}

MIN_TOKEN_LENGTH = 2


@dataclass
class PreprocessedText:
    """Résultat du prétraitement d'un texte brut."""
    raw: str
    cleaned: str
    tokens: List[str] = field(default_factory=list)
    stemmed: List[str] = field(default_factory=list)


@dataclass
class TextChunk:
    """Un passage découpé à partir d'un document."""
    index: int
    content: str
    token_count: int = 0
    start_char: int = 0
    end_char: int = 0


class TextPreprocessor:
    """Moteur de prétraitement NLP pour le texte français."""

    def __init__(self, language: str = "french", use_stemming: bool = True):
        self.language = language
        self.use_stemming = use_stemming

        if _NLTK_AVAILABLE:
            try:
                self.stop_words = set(_nltk_stopwords.words(language))
            except OSError:
                self.stop_words = FRENCH_STOP_WORDS.copy()
        else:
            self.stop_words = FRENCH_STOP_WORDS.copy()

        self.stemmer = None
        if use_stemming and _NLTK_AVAILABLE:
            self.stemmer = _SnowballStemmer(language)

    @staticmethod
    def clean(text: str) -> str:
        """Supprime le bruit : balises HTML, espaces multiples, unicode cassé."""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def lowercase(text: str) -> str:
        """Passe tout le texte en minuscules."""
        return text.lower()

    @staticmethod
    def remove_punctuation(text: str) -> str:
        """Supprime la ponctuation et les caractères spéciaux."""
        text = re.sub(r"[^\w\sàâäéèêëïîôùûüÿçœæ'-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        """Découpe le texte en tokens, filtre stop words et mots courts."""
        text = self.remove_punctuation(self.lowercase(self.clean(text)))

        if _NLTK_AVAILABLE:
            try:
                tokens = _nltk_word_tokenize(text, language=self.language)
            except Exception:
                tokens = text.split()
        else:
            tokens = text.split()

        tokens = [
            t for t in tokens
            if len(t) >= MIN_TOKEN_LENGTH
            and t not in self.stop_words
            and not t.isdigit()
            and not re.fullmatch(r"[\W_]+", t)
        ]
        return tokens

    def stem(self, tokens: List[str]) -> List[str]:
        """Racine chaque token via Snowball (français)."""
        if self.stemmer is None:
            return tokens
        return [self.stemmer.stem(t) for t in tokens]

    def process(self, text: str) -> PreprocessedText:
        """Exécute le pipeline complet de prétraitement."""
        cleaned = self.clean(text)
        tokens = self.tokenize(text)
        stemmed = self.stem(tokens) if self.use_stemming else tokens

        return PreprocessedText(
            raw=text,
            cleaned=cleaned,
            tokens=tokens,
            stemmed=stemmed,
        )

    def process_text(self, text: str) -> List[str]:
        """Version simplifiée : retourne directement la liste de tokens stemmés."""
        result = self.process(text)
        return result.stemmed if self.use_stemming else result.tokens

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[TextChunk]:
        """Découpe un texte long en passages de taille fixe."""
        words = text.split()
        if not words:
            return []

        if overlap >= chunk_size:
            overlap = 0

        step = chunk_size - overlap
        if step <= 0:
            step = chunk_size

        chunks = []
        start = 0
        idx = 0

        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_content = " ".join(chunk_words)

            char_start = len(" ".join(words[:start])) + (1 if start > 0 else 0)
            char_end = char_start + len(chunk_content)

            chunks.append(TextChunk(
                index=idx,
                content=chunk_content,
                token_count=len(chunk_words),
                start_char=char_start,
                end_char=char_end,
            ))

            idx += 1
            start += step

        return chunks

    def chunk_document(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[dict]:
        """Découpe et prétraite un document complet."""
        raw_chunks = self.chunk_text(text, chunk_size, overlap)
        results = []

        for chunk in raw_chunks:
            tokens = self.tokenize(chunk.content)
            stemmed = self.stem(tokens) if self.use_stemming else tokens
            results.append({
                "content": chunk.content,
                "token_count": chunk.token_count,
                "tokens": tokens,
                "stemmed": stemmed,
                "index": chunk.index,
            })

        return results

    def get_stop_words(self) -> set:
        """Retourne l'ensemble des stop words chargés."""
        return self.stop_words.copy()

    def add_stop_words(self, words: List[str]) -> None:
        """Ajoute des stop words personnalisés."""
        self.stop_words.update(w.lower() for w in words)

    def remove_stop_words(self, words: List[str]) -> None:
        """Retire des stop words de la liste."""
        self.stop_words.difference_update(w.lower() for w in words)
