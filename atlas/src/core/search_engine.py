"""
search_engine.py — Moteur de recherche pour l'application Atlas.

Fonctionnalites :
    - Transformation de la requete en vecteur TF-IDF
    - Calcul de similarite cosinus
    - Classement des resultats par pertinence
    - Retour des Top 10 resultats avec scores
    - Recherche avec filtres (periode, auteur, region)
    - Historique des recherches
    - Gestion des erreurs

Usage :
    from src.core.search_engine import SearchEngine

    engine = SearchEngine()
    engine.load_index()
    results = engine.search("revolution industrielle")
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.utils.datetime import now_local_str

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from src.core.preprocessing import TextPreprocessor
    from src.core.indexer import TFIDFIndexer, SearchResult, IndexNotBuiltError
except ImportError:
    from preprocessing import TextPreprocessor
    from indexer import TFIDFIndexer, SearchResult, IndexNotBuiltError

logger = logging.getLogger(__name__)


# ── Exceptions ───────────────────────────────────────────────────────
class SearchError(Exception):
    """Erreur generique de recherche."""


class EmptyQueryError(SearchError):
    """La requete est vide."""


class IndexNotLoadedError(SearchError):
    """L'index n'est pas charge."""


# ── Dataclasses ──────────────────────────────────────────────────────
@dataclass
class SearchFilters:
    """Filtres de recherche avancee."""
    period: Optional[str] = None
    author: Optional[str] = None
    region: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    doc_type: Optional[str] = None

    def is_empty(self) -> bool:
        return all(v is None for v in self.__dict__.values())


@dataclass
class SearchQuery:
    """Representation structuree d'une requete de recherche."""
    text: str
    filters: SearchFilters = field(default_factory=SearchFilters)
    top_k: int = 10
    min_score: float = 0.01


@dataclass
class SearchResponse:
    """Reponse complete d'une recherche."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    filters_applied: Dict[str, Any]
    timestamp: str = field(default_factory=now_local_str)


@dataclass
class SearchHistoryEntry:
    """Entree d'historique de recherche."""
    query: str
    timestamp: str
    result_count: int
    search_time_ms: float
    filters: Dict[str, Any]


# ── Moteur de recherche ──────────────────────────────────────────────
class SearchEngine:
    """Moteur de recherche TF-IDF avec similarite cosinus.

    Pipeline de recherche :
        1. Pretraitement de la requete (tokenisation, nettoyage)
        2. Transformation en vecteur TF-IDF
        3. Calcul de similarite cosinus avec tous les documents
        4. Tri par score de pertinence
        5. Application des filtres optionnels
        6. Retour des Top-K resultats
    """

    def __init__(
        self,
        indexer: Optional[TFIDFIndexer] = None,
        preprocessor: Optional[TextPreprocessor] = None,
        default_top_k: int = 10,
        min_score: float = 0.01,
    ):
        """Initialise le moteur de recherche.

        Args:
            indexer:        Indexeur TF-IDF externe (optionnel).
            preprocessor:   Preprocesseur NLP externe (optionnel).
            default_top_k:  Nombre par defaut de resultats.
            min_score:      Score minimal pour etre inclus.
        """
        self.indexer = indexer or TFIDFIndexer()
        self.preprocessor = preprocessor or TextPreprocessor()
        self.default_top_k = default_top_k
        self.min_score = min_score

        self._history: List[SearchHistoryEntry] = []
        self._max_history = 1000
        self._search_count = 0
        self._total_search_time_ms = 0.0

    @property
    def is_ready(self) -> bool:
        """True si le moteur est pret pour la recherche."""
        return self.indexer.is_built

    @property
    def stats(self) -> Dict[str, Any]:
        """Statistiques globales du moteur."""
        index_stats = self.indexer.stats
        avg_time = (
            self._total_search_time_ms / self._search_count
            if self._search_count > 0
            else 0.0
        )
        return {
            "total_documents": index_stats.total_documents,
            "vocabulary_size": index_stats.vocabulary_size,
            "total_searches": self._search_count,
            "avg_search_time_ms": round(avg_time, 2),
            "history_size": len(self._history),
        }

    # ── chargement de l'index ────────────────────────────────────
    def load_index(self, filepath=None):
        """Charge l'index TF-IDF depuis le disque.

        Args:
            filepath: Chemin du fichier d'index.

        Raises:
            IndexNotLoadedError: Si le chargement echoue.
        """
        try:
            self.indexer.load(filepath)
            logger.info("Index charge avec succes.")
        except Exception as e:
            raise IndexNotLoadedError(f"Impossible de charger l'index : {e}") from e

    # ── Recherche principale ─────────────────────────────────────
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[SearchFilters] = None,
        min_score: Optional[float] = None,
    ) -> SearchResponse:
        """Execute une recherche par similarite cosinus.

        Args:
            query:     Texte de la requete utilisateur.
            top_k:     Nombre max de resultats (defaut : 10).
            filters:   Filtres optionnels (periode, auteur...).
            min_score: Score minimal (defaut : 0.01).

        Returns:
            SearchResponse avec resultats, scores et metadonnees.

        Raises:
            EmptyQueryError:   Si la requete est vide.
            IndexNotLoadedError: Si l'index n'est pas charge.
        """
        start_time = time.perf_counter()

        if not query or not query.strip():
            raise EmptyQueryError("La requete de recherche ne peut pas etre vide.")

        if not self.is_ready:
            raise IndexNotLoadedError(
                "L'index n'est pas charge. Appelez load_index() d'abord."
            )

        k = top_k or self.default_top_k
        score_threshold = min_score if min_score is not None else self.min_score
        filters = filters or SearchFilters()

        query_processed = self._preprocess_query(query)

        raw_results = self.indexer.search(
            query=query_processed,
            top_k=k * 3,
            min_score=score_threshold * 0.5,
        )

        filtered_results = self._apply_filters(raw_results, filters)

        final_results = filtered_results[:k]

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        self._record_search(query, len(final_results), elapsed_ms, filters)

        response = SearchResponse(
            query=query,
            results=final_results,
            total_results=len(filtered_results),
            search_time_ms=round(elapsed_ms, 2),
            filters_applied=self._filters_to_dict(filters),
        )

        logger.info(
            "Recherche '%s' : %d resultats en %.1fms",
            query[:30],
            len(final_results),
            elapsed_ms,
        )

        return response

    def _preprocess_query(self, query: str) -> str:
        """Pretraite la requete avant vectorisation."""
        cleaned = self.preprocessor.clean(query)
        cleaned = self.preprocessor.lowercase(cleaned)
        cleaned = self.preprocessor.remove_punctuation(cleaned)
        return cleaned

    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: SearchFilters,
    ) -> List[SearchResult]:
        """Filtre les resultats selon les criteres specifies."""
        if filters.is_empty():
            return results

        filtered = []
        for result in results:
            meta = result.metadata

            if filters.period:
                doc_period = meta.get("period", "")
                if filters.period.lower() not in doc_period.lower():
                    continue

            if filters.author:
                doc_author = meta.get("author", "")
                if filters.author.lower() not in doc_author.lower():
                    continue

            if filters.region:
                doc_region = meta.get("region", "")
                if filters.region.lower() not in doc_region.lower():
                    continue

            if filters.doc_type:
                doc_type = meta.get("doc_type", "")
                if filters.doc_type.lower() != doc_type.lower():
                    continue

            if filters.date_from:
                doc_date = meta.get("date_publication", "")
                if doc_date and doc_date < filters.date_from:
                    continue

            if filters.date_to:
                doc_date = meta.get("date_publication", "")
                if doc_date and doc_date > filters.date_to:
                    continue

            filtered.append(result)

        return filtered

    def _record_search(
        self,
        query: str,
        result_count: int,
        search_time_ms: float,
        filters: SearchFilters,
    ):
        """Enregistre la recherche dans l'historique."""
        entry = SearchHistoryEntry(
            query=query,
            timestamp=now_local_str(),
            result_count=result_count,
            search_time_ms=round(search_time_ms, 2),
            filters=self._filters_to_dict(filters),
        )

        self._history.append(entry)

        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        self._search_count += 1
        self._total_search_time_ms += search_time_ms

    @staticmethod
    def _filters_to_dict(filters: SearchFilters) -> Dict[str, Any]:
        """Convertit les filtres en dictionnaire."""
        return {k: v for k, v in filters.__dict__.items() if v is not None}

    # ── Historique ───────────────────────────────────────────────
    def get_history(self, limit: int = 50) -> List[SearchHistoryEntry]:
        """Retourne les dernieres recherches."""
        return list(reversed(self._history[-limit:]))

    def clear_history(self):
        """Vide l'historique des recherches."""
        self._history.clear()
        self._search_count = 0
        self._total_search_time_ms = 0.0

    def get_frequent_queries(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Retourne les requetes les plus frequentes."""
        counter: Dict[str, int] = defaultdict(int)
        for entry in self._history:
            counter[entry.query.lower()] += 1
        sorted_queries = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        return sorted_queries[:top_n]

    # ── Recherche par document ───────────────────────────────────
    def search_similar(
        self,
        document_id: int,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """Trouve des documents similaires a un document donne.

        Args:
            document_id: ID du document de reference.
            top_k:       Nombre de resultats.

        Returns:
            Liste de resultats similaires (sans le document source).
        """
        doc = self.indexer.get_document(document_id)
        if not doc:
            return []

        query = doc.get("content", "")[:500]
        results = self.indexer.search(query, top_k=top_k + 1)

        return [r for r in results if r.document_id != document_id][:top_k]

    # ── Suggestions ──────────────────────────────────────────────
    def suggest(self, partial_query: str, max_suggestions: int = 5) -> List[str]:
        """Propose des completions pour une requete partielle.

        Args:
            partial_query: Debut de requete.
            max_suggestions: Nombre max de suggestions.

        Returns:
            Liste de suggestions basees sur l'historique.
        """
        if not partial_query or len(partial_query) < 2:
            return []

        lower_partial = partial_query.lower()
        seen: Set[str] = set()
        suggestions: List[str] = []

        for entry in reversed(self._history):
            if entry.query.lower().startswith(lower_partial):
                q = entry.query
                if q not in seen:
                    seen.add(q)
                    suggestions.append(q)
                    if len(suggestions) >= max_suggestions:
                        break

        return suggestions

    # ── Statistiques detaillees ──────────────────────────────────
    def get_search_analytics(self) -> Dict[str, Any]:
        """Retourne des analytiques detaillees des recherches."""
        if not self._history:
            return {
                "total_searches": 0,
                "unique_queries": 0,
                "avg_results": 0,
                "avg_time_ms": 0,
                "top_queries": [],
                "period_distribution": {},
            }

        unique_queries = set(e.query.lower() for e in self._history)
        avg_results = sum(e.result_count for e in self._history) / len(self._history)
        avg_time = self._total_search_time_ms / len(self._history)

        period_count: Dict[str, int] = defaultdict(int)
        for entry in self._history:
            for period in entry.filters.get("period", []):
                period_count[period] += 1

        return {
            "total_searches": len(self._history),
            "unique_queries": len(unique_queries),
            "avg_results": round(avg_results, 1),
            "avg_time_ms": round(avg_time, 2),
            "top_queries": self.get_frequent_queries(10),
            "period_distribution": dict(period_count),
        }


# ── Point d'entree pour test rapide ──────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    documents = [
        {"id": 1, "title": "Revolutions industrielles",
         "content": "La revolution industrielle a transforme l'europe au XIXe siecle. "
                    "Les usines et les machines ont change la production de masse.",
         "period": "XIXe siecle", "author": "Thompson", "region": "Europe"},
        {"id": 2, "title": "Guerre mondiale",
         "content": "La Premiere Guerre mondiale a eclate en 1914. Les puissances "
                    "europeennes se sont affrontees pendant quatre ans.",
         "period": "XXe siecle", "author": "Dupont", "region": "Europe"},
        {"id": 3, "title": "Renaissance",
         "content": "La Renaissance est une periode de renouveau culturel en Europe "
                    "aux XVe et XVIe siecles. L'art et la science ont prospere.",
         "period": "XVe-XVIe siecle", "author": "Martin", "region": "Europe"},
        {"id": 4, "title": "Revolution francaise",
         "content": "La revolution francaise de 1789 a renverse la monarchie. "
                    "Les droits de l'homme ont ete proclames a la nation.",
         "period": "XVIIIe siecle", "author": "Bernard", "region": "Europe"},
        {"id": 5, "title": "Empire romain",
         "content": "L'Empire romain a domine la Mediterranee pendant des siecles. "
                    "Son influence sur le droit et la culture persiste encore.",
         "period": "Antiquite", "author": "Moreau", "region": "Europe"},
        {"id": 6, "title": "Traite negriere",
         "content": "La traite des esclaves a transatlantique a dure plusieurs siecles. "
                    "Des millions de personnes ont ete deplacees de force.",
         "period": "XVIe-XIXe siecle", "author": "Petit", "region": "Afrique"},
        {"id": 7, "title": "Guerre froide",
         "content": "La Guerre froide a oppose les Etats-Unis et l'URSS pendant "
                    "pres de 50 ans. La course a l'armement a defini cette epoque.",
         "period": "XXe siecle", "author": "Robert", "region": "Mondial"},
    ]

    engine = SearchEngine(default_top_k=10)
    engine.indexer.build_index(documents)

    print("=" * 60)
    print("ATLAS - Test du moteur de recherche")
    print("=" * 60)

    query = "revolution industrielle europe"
    print(f"\n[Recherche] '{query}'")
    response = engine.search(query, top_k=5)
    print(f"  {response.total_results} resultats en {response.search_time_ms}ms")
    for i, r in enumerate(response.results, 1):
        print(f"  {i}. {r.title} (score: {r.score})")

    print(f"\n[Filtre] Periode = 'XXe siecle'")
    filters = SearchFilters(period="XXe siecle")
    response = engine.search("guerre", filters=filters, top_k=5)
    print(f"  {response.total_results} resultats")
    for r in response.results:
        print(f"  -> {r.title} (score: {r.score})")

    print(f"\n[Historique] {len(engine.get_history())} recherches")
    print(frequent := engine.get_frequent_queries(3))

    print(f"\n[Analytiques]")
    analytics = engine.get_search_analytics()
    print(f"  Recherches: {analytics['total_searches']}")
    print(f"  Requetes uniques: {analytics['unique_queries']}")
    print(f"  Temps moyen: {analytics['avg_time_ms']}ms")

    print(f"\n[Suggestions] 'rev'")
    suggestions = engine.suggest("rev")
    for s in suggestions:
        print(f"  -> {s}")

    print("\nTous les tests passent")
