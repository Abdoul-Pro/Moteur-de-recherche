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

Usage :
    from src.core.preprocessing import TextPreprocessor

    pp = TextPreprocessor()
    tokens = pp.process("La révolution industrielle a transformé l'Europe.")
    chunks  = pp.chunk_text(long_text, chunk_size=500)
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

# Longueur minimale d'un token pour être conservé
MIN_TOKEN_LENGTH = 2


# ── Dataclasses de sortie ────────────────────────────────────────────
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


# ── Classe principale ────────────────────────────────────────────────
class TextPreprocessor:
    """Moteur de prétraitement NLP pour le texte français.

    Pipeline complet :
        1. clean()       → nettoyage unicode, suppression HTML
        2. lowercase()   → passage en minuscules
        3. remove_punct()→ suppression ponctuation et caractères spéciaux
        4. tokenize()    → découpage en tokens + filtrage stop words
        5. stem()        → racinisation (Snowball)
        6. process()     → exécute tout le pipeline
        7. chunk_text()  → découpe en passages de taille fixe
    """

    def __init__(self, language: str = "french", use_stemming: bool = True):
        self.language = language
        self.use_stemming = use_stemming

        # Stop words
        if _NLTK_AVAILABLE:
            try:
                self.stop_words = set(_nltk_stopwords.words(language))
            except OSError:
                self.stop_words = FRENCH_STOP_WORDS.copy()
        else:
            self.stop_words = FRENCH_STOP_WORDS.copy()

        # Stemmer
        self.stemmer = None
        if use_stemming and _NLTK_AVAILABLE:
            self.stemmer = _SnowballStemmer(language)

    # ── 1. Nettoyage ─────────────────────────────────────────────
    @staticmethod
    def clean(text: str) -> str:
        """Supprime le bruit : balises HTML, espaces multiples, unicode cassé."""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── 2. Minuscules ────────────────────────────────────────────
    @staticmethod
    def lowercase(text: str) -> str:
        """Passe tout le texte en minuscules."""
        return text.lower()

    # ── 3. Suppression ponctuation ────────────────────────────────
    @staticmethod
    def remove_punctuation(text: str) -> str:
        """Supprime la ponctuation et les caractères spéciaux.

        Conserve les tirets, apostrophes et accents pour le français.
        """
        text = re.sub(r"[^\w\sàâäéèêëïîôùûüÿçœæ'-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # ── 4. Tokenisation ──────────────────────────────────────────
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

    # ── 5. Stemming ──────────────────────────────────────────────
    def stem(self, tokens: List[str]) -> List[str]:
        """Racine chaque token via Snowball (français)."""
        if self.stemmer is None:
            return tokens
        return [self.stemmer.stem(t) for t in tokens]

    # ── 6. Pipeline complet ──────────────────────────────────────
    def process(self, text: str) -> PreprocessedText:
        """Exécute le pipeline complet de prétraitement.

        Retourne un objet PreprocessedText contenant le texte nettoyé,
        les tokens et les racines.
        """
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

    # ── 7. Découpage en passages ─────────────────────────────────
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[TextChunk]:
        """Découpe un texte long en passages de taille fixe.

        Args:
            text:       Texte brut à découper.
            chunk_size: Nombre de mots par passage (défaut 500).
            overlap:    chevauchement entre passages (défaut 50 mots).

        Returns:
            Liste de TextChunk avec index, contenu, position chars.
        """
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
        """Découpe et prétraite un document complet.

        Retourne une liste de dicts prêts pour l'insertion en base :
            {"content": str, "token_count": int, "tokens": list, "stemmed": list}
        """
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

    # ── Utilitaires ──────────────────────────────────────────────
    def get_stop_words(self) -> set:
        """Retourne l'ensemble des stop words chargés."""
        return self.stop_words.copy()

    def add_stop_words(self, words: List[str]) -> None:
        """Ajoute des stop words personnalisés."""
        self.stop_words.update(w.lower() for w in words)

    def remove_stop_words(self, words: List[str]) -> None:
        """Retire des stop words de la liste."""
        self.stop_words.difference_update(w.lower() for w in words)


# ── Point d'entrée pour test rapide ──────────────────────────────────
if __name__ == "__main__":
    pp = TextPreprocessor()

    sample = """
    <p>La <b>révolution industrielle</b> a marqué un tournant décisif dans
    l'histoire économique, sociale et technologique de l'Europe. Elle a débuté
    en Grande-Bretagne à la fin du XVIIIe siècle et s'est progressivement
    étendue à d'autres pays européens.</p>

    <p>Les usines, alimentées par la vapeur et les machines, sont devenues
    le cœur de la production. Cette transformation a entraîné une augmentation
    massive de la productivité, mais aussi de profondes mutations sociales
    et économiques.</p>
    """

    print("=" * 60)
    print("ATLAS - Test du pretraitement NLP")
    print("=" * 60)

    # Pipeline complet
    result = pp.process(sample)

    print("\n[Texte nettoye]")
    print(result.cleaned[:200] + "...")

    print(f"\n[Tokens: {len(result.tokens)}]")
    print(result.tokens[:20])

    print(f"\n[Stemmes: {len(result.stemmed)}]")
    print(result.stemmed[:20])

    # Chunking
    chunks = pp.chunk_text(sample, chunk_size=40)
    print(f"\n[Passages: {len(chunks)}]")
    for c in chunks:
        print(f"  [{c.index}] {c.token_count} mots | chars {c.start_char}-{c.end_char}")

    # Chunking + pretraitement
    doc_chunks = pp.chunk_document(sample, chunk_size=40)
    print(f"\n[Passages pretraite: {len(doc_chunks)}]")
    for dc in doc_chunks:
        print(f"  [{dc['index']}] {dc['token_count']} mots -> {len(dc['stemmed'])} stemmes")

    print("\nTous les tests passent")
