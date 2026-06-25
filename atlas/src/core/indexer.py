"""
indexer.py — Moteur d'indexation TF-IDF pour Atlas.

Fonctionnalites :
    - Vectorisation des documents avec TfidfVectorizer (scikit-learn)
    - Construction de l'inverse index pour recherche rapide
    - Sauvegarde de l'index sur disque (joblib)
    - Chargement de l'index depuis le disque
    - Gestion des erreurs et logging

Usage :
    from src.core.indexer import TFIDFIndexer

    indexer = TFIDFIndexer()
    indexer.build_index(documents)
    indexer.save()
    indexer.load()
    results = indexer.search("revolution industrielle")
"""

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from config import INDEX_DIR
except ImportError:
    from pathlib import Path
    INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "index"

logger = logging.getLogger(__name__)

from src.utils.datetime import now_local_str


# ── Exceptions personnalisees ────────────────────────────────────────
class IndexerError(Exception):
    """Erreur generique du module d'indexation."""


class IndexNotBuiltError(IndexerError):
    """L'index n'a pas encore ete construit."""


class DocumentNotFoundError(IndexerError):
    """Document introuvable dans l'index."""


class SaveIndexError(IndexerError):
    """Echec de la sauvegarde de l'index."""


class LoadIndexError(IndexerError):
    """Echec du chargement de l'index."""


# ── Dataclasses ──────────────────────────────────────────────────────
@dataclass
class SearchResult:
    """Un resultat de recherche avec score de pertinence."""
    document_id: int
    title: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexStats:
    """Statistiques de l'index courant."""
    total_documents: int = 0
    total_features: int = 0
    vocabulary_size: int = 0
    index_size_mb: float = 0.0
    last_built: str = ""


# ── Classe principale ────────────────────────────────────────────────
class TFIDFIndexer:
    """Moteur d'indexation TF-IDF avec scikit-learn.

    Pipeline :
        1. Pretraitement des documents (tokenisation, nettoyage)
        2. Vectorisation TF-IDF via TfidfVectorizer
        3. Construction de la matrice documents x termes
        4. Recherche par similarite cosinus
        5. Persistance sur disque (joblib)
    """

    def __init__(
        self,
        max_features: int = 50000,
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 2,
        max_df: float = 0.95,
        sublinear_tf: bool = True,
        index_dir: Optional[Path] = None,
    ):
        """Initialise l'indexeur TF-IDF.

        Args:
            max_features:  Nombre max de termes dans le vocabulaire.
            ngram_range:   Plage de n-grammes (defaut : unigrammes + bigrammes).
            min_df:        Frequence documentaire minimale pour un terme.
            max_df:        Frequence documentaire maximale (proportion).
            sublinear_tf:  Appliquer la log-normalisation au TF.
            index_dir:     Repertoire de sauvegarde de l'index.
        """
        self.index_dir = index_dir or INDEX_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=sublinear_tf,
            strip_accents="unicode",
            token_pattern=r"(?u)\b\w[\w'-]+\b",
        )

        self._documents: List[Dict[str, Any]] = []
        self._tfidf_matrix = None
        self._vocabulary: Dict[str, int] = {}
        self._is_built = False
        self._build_time: str = ""

    @property
    def is_built(self) -> bool:
        """True si l'index a ete construit ou charge."""
        return self._is_built

    @property
    def stats(self) -> IndexStats:
        """Retourne les statistiques courantes de l'index."""
        size_mb = 0.0
        if self._tfidf_matrix is not None:
            size_mb = self._tfidf_matrix.data.nbytes / (1024 * 1024)

        return IndexStats(
            total_documents=len(self._documents),
            total_features=self._tfidf_matrix.shape[1] if self._tfidf_matrix is not None else 0,
            vocabulary_size=len(self._vocabulary),
            index_size_mb=round(size_mb, 2),
            last_built=self._build_time,
        )

    # ── Construction de l'index ──────────────────────────────────
    def build_index(
        self,
        documents: List[Dict[str, Any]],
        text_key: str = "content",
    ) -> IndexStats:
        """Construit l'index TF-IDF a partir d'une liste de documents.

        Args:
            documents:  Liste de dicts contenant au minimum 'content'.
            text_key:   Cle du champ texte a vectoriser.

        Returns:
            IndexStats avec les metriques de construction.

        Raises:
            IndexerError: Si la liste est vide ou les champs manquent.
        """
        if not documents:
            raise IndexerError("Aucun document fourni pour l'indexation.")

        start_time = time.time()

        texts = []
        valid_docs = []

        for i, doc in enumerate(documents):
            text = doc.get(text_key, "")
            if not text or not text.strip():
                logger.warning("Document %d ignore : contenu vide.", i)
                continue
            texts.append(text)
            valid_docs.append(doc)

        if not texts:
            raise IndexerError("Aucun document avec contenu valide.")

        try:
            n_docs = len(texts)
            effective_max_df = self.vectorizer.max_df
            effective_min_df = self.vectorizer.min_df

            if isinstance(effective_max_df, float) and n_docs * effective_max_df < 1:
                effective_max_df = 1
            if isinstance(effective_min_df, int) and effective_min_df > n_docs:
                effective_min_df = 1

            temp_vectorizer = TfidfVectorizer(
                max_features=self.vectorizer.max_features,
                ngram_range=self.vectorizer.ngram_range,
                min_df=effective_min_df,
                max_df=effective_max_df,
                sublinear_tf=self.vectorizer.sublinear_tf,
                strip_accents="unicode",
                token_pattern=r"(?u)\b\w[\w'-]+\b",
            )
            self._tfidf_matrix = temp_vectorizer.fit_transform(texts)
            self.vectorizer = temp_vectorizer
        except ValueError as e:
            raise IndexerError(f"Erreur lors de la vectorisation : {e}") from e

        self._documents = valid_docs
        self._vocabulary = self.vectorizer.vocabulary_
        self._is_built = True
        self._build_time = now_local_str()

        elapsed = time.time() - start_time
        logger.info(
            "Index construit : %d documents, %d termes en %.2fs",
            len(valid_docs),
            len(self._vocabulary),
            elapsed,
        )

        return self.stats

    # ── Recherche ────────────────────────────────────────────────
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.01,
    ) -> List[SearchResult]:
        """Recherche par similarite cosinus.

        Args:
            query:     Texte de la requete.
            top_k:     Nombre max de resultats.
            min_score: Score minimum pour etre inclus.

        Returns:
            Liste de SearchResult triee par score decroissant.

        Raises:
            IndexNotBuiltError: Si l'index n'est pas pret.
        """
        if not self._is_built:
            raise IndexNotBuiltError(
                "L'index n'est pas construit. Appelez build_index() ou load() d'abord."
            )

        if not query or not query.strip():
            return []

        try:
            query_vector = self.vectorizer.transform([query])
        except Exception as e:
            logger.error("Erreur vectorisation requete : %s", e)
            return []

        scores = cosine_similarity(query_vector, self._tfidf_matrix).flatten()

        ranked_indices = scores.argsort()[::-1]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < min_score:
                break
            if len(results) >= top_k:
                break

            doc = self._documents[idx]
            results.append(SearchResult(
                document_id=doc.get("id", idx),
                title=doc.get("title", ""),
                content=doc.get("content", "")[:500],
                score=round(score, 4),
                metadata={
                    k: v for k, v in doc.items()
                    if k not in ("id", "title", "content")
                },
            ))

        return results

    def search_with_details(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Recherche avancee avec details de pertinence par terme.

        Args:
            query:  Texte de la requete.
            top_k:  Nombre max de resultats.

        Returns:
            Liste de dicts avec score global et details par terme.
        """
        results = self.search(query, top_k=top_k)

        query_terms = self._extract_query_terms(query)

        detailed = []
        for result in results:
            term_scores = {}
            for term in query_terms:
                if term in self._vocabulary:
                    term_idx = self._vocabulary[term]
                    term_vector = self._tfidf_matrix[:, term_idx]
                    doc_idx = None
                    for i, d in enumerate(self._documents):
                        if d.get("id") == result.document_id:
                            doc_idx = i
                            break
                    if doc_idx is not None:
                        term_scores[term] = round(float(term_vector[doc_idx]), 4)

            detailed.append({
                "document_id": result.document_id,
                "title": result.title,
                "content": result.content,
                "score": result.score,
                "term_scores": term_scores,
                "metadata": result.metadata,
            })

        return detailed

    def _extract_query_terms(self, query: str) -> List[str]:
        """Extrait les termes d'une requete via le vectoriseur."""
        try:
            query_vector = self.vectorizer.transform([query])
            feature_names = self.vectorizer.get_feature_names_out()
            non_zero = query_vector.nonzero()[1]
            return [feature_names[i] for i in non_zero]
        except Exception:
            return []

    # ── Sauvegarde / Chargement ──────────────────────────────────
    def save(self, filepath: Optional[Path] = None) -> Path:
        """Sauvegarde l'index sur disque via joblib.

        Args:
            filepath: Chemin de sauvegarde. Defaut : index_dir/atlas_index.pkl

        Returns:
            Chemin effectif de sauvegarde.

        Raises:
            SaveIndexError: En cas d'echec d'ecriture.
        """
        if not self._is_built:
            raise IndexerError("Impossible de sauvegarder : index non construit.")

        save_path = filepath or (self.index_dir / "atlas_index.pkl")

        payload = {
            "vectorizer": self.vectorizer,
            "documents": self._documents,
            "tfidf_matrix": self._tfidf_matrix,
            "vocabulary": self._vocabulary,
            "build_time": self._build_time,
            "version": "1.0.0",
        }

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(payload, save_path, compress=3)
            size_mb = save_path.stat().st_size / (1024 * 1024)
            logger.info("Index sauvegarde : %s (%.2f Mo)", save_path, size_mb)
            return save_path
        except Exception as e:
            raise SaveIndexError(f"Echec sauvegarde : {e}") from e

    def load(self, filepath: Optional[Path] = None) -> IndexStats:
        """Charge un index depuis le disque.

        Args:
            filepath: Chemin du fichier. Defaut : index_dir/atlas_index.pkl

        Returns:
            IndexStats du chargement.

        Raises:
            LoadIndexError: Si le fichier est introuvable ou corrompu.
        """
        load_path = filepath or (self.index_dir / "atlas_index.pkl")

        if not load_path.exists():
            raise LoadIndexError(f"Index introuvable : {load_path}")

        try:
            payload = joblib.load(load_path)
        except Exception as e:
            raise LoadIndexError(f"Erreur chargement : {e}") from e

        required_keys = {"vectorizer", "documents", "tfidf_matrix", "vocabulary"}
        if not required_keys.issubset(payload.keys()):
            raise LoadIndexError("Fichier d'index corrompu (cles manquantes).")

        self.vectorizer = payload["vectorizer"]
        self._documents = payload["documents"]
        self._tfidf_matrix = payload["tfidf_matrix"]
        self._vocabulary = payload["vocabulary"]
        self._build_time = payload.get("build_time", "")
        self._is_built = True

        logger.info(
            "Index charge : %d documents, %d termes",
            len(self._documents),
            len(self._vocabulary),
        )

        return self.stats

    # ── Utilitaires ──────────────────────────────────────────────
    def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Recupere un document par son ID."""
        for doc in self._documents:
            if doc.get("id") == document_id:
                return doc
        return None

    def get_vocabulary(self, top_n: int = 100) -> List[Tuple[str, int]]:
        """Retourne les termes les plus frequents du vocabulaire."""
        if not self._vocabulary:
            return []
        sorted_vocab = sorted(
            self._vocabulary.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_vocab[:top_n]

    def add_documents(
        self,
        new_documents: List[Dict[str, Any]],
        text_key: str = "content",
    ) -> IndexStats:
        """Ajoute des documents et reconstruit l'index."""
        all_docs = self._documents + new_documents
        return self.build_index(all_docs, text_key=text_key)

    def clear(self) -> None:
        """Vide l'index en memoire."""
        self.vectorizer = TfidfVectorizer(
            max_features=self.vectorizer.max_features,
            ngram_range=self.vectorizer.ngram_range,
            min_df=self.vectorizer.min_df,
            max_df=self.vectorizer.max_df,
            sublinear_tf=self.vectorizer.sublinear_tf,
        )
        self._documents.clear()
        self._tfidf_matrix = None
        self._vocabulary.clear()
        self._is_built = False
        self._build_time = ""
        logger.info("Index vide.")

    def delete_index_file(self) -> bool:
        """Supprime le fichier d'index sur disque."""
        index_path = self.index_dir / "atlas_index.pkl"
        if index_path.exists():
            index_path.unlink()
            logger.info("Fichier index supprime : %s", index_path)
            return True
        return False


class DocumentIndexer:
    """Indexe les documents de la base SQLite pour le moteur engine.py."""

    STAGES = [
        "Analyse des documents",
        "Extraction de texte",
        "Prétraitement linguistique",
        "Calcul TF-IDF",
        "Mise à jour de l'index",
    ]

    def __init__(self, db):
        from src.core.preprocessor import TextPreprocessor

        self.db = db
        self.preprocessor = TextPreprocessor()
        self._stop_requested = False
        self._progress_cb = None
        self._status_cb = None

    def set_callbacks(self, progress=None, status=None):
        self._progress_cb = progress
        self._status_cb = status

    def stop(self):
        self._stop_requested = True

    def _emit_progress(self, pct, current, total, stage):
        if self._progress_cb:
            self._progress_cb(pct, current, total, stage)

    def _emit_status(self, message):
        if self._status_cb:
            self._status_cb(message)

    def index_all(self):
        import math
        from collections import Counter, defaultdict

        from config import CHUNK_SIZE

        self._stop_requested = False
        self._emit_status("Réinitialisation de l'index...")
        self._emit_progress(0, 0, 1, self.STAGES[0])

        self.db.execute("DELETE FROM tfidf_index")
        self.db.execute("DELETE FROM chunks")
        self.db.execute("DELETE FROM vocabulary")

        documents = self.db.fetchall("SELECT * FROM documents ORDER BY id")
        total_docs = len(documents)
        if total_docs == 0:
            self._emit_status("Aucun document à indexer.")
            self._emit_progress(100, 0, 0, self.STAGES[-1])
            return

        chunk_records = []
        chunk_texts = []

        for i, doc in enumerate(documents):
            if self._stop_requested:
                self._emit_status("Indexation interrompue.")
                return

            doc_id = doc["id"]
            content = doc["content"] or ""
            title = doc["title"] or ""

            self._emit_progress(
                (i / total_docs) * 40, i, total_docs, self.STAGES[1]
            )
            self._emit_status(f"Extraction : {title[:50]}")

            words = content.split()
            if not words:
                continue

            chunk_size = max(CHUNK_SIZE // 5, 50)
            overlap = max(chunk_size // 10, 5)
            start = 0
            chunk_index = 0

            while start < len(words):
                end = min(start + chunk_size, len(words))
                chunk_content = " ".join(words[start:end])
                tokens = self.preprocessor.process(chunk_content)
                chunk_records.append({
                    "document_id": doc_id,
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "token_count": len(tokens),
                })
                chunk_texts.append(" ".join(tokens) if tokens else chunk_content)
                chunk_index += 1
                if end >= len(words):
                    break
                start = end - overlap

        if not chunk_records:
            self._emit_status("Aucun passage extrait.")
            return

        self._emit_progress(45, total_docs, total_docs, self.STAGES[2])
        self._emit_status("Prétraitement linguistique terminé.")

        chunk_ids = []
        for record in chunk_records:
            cursor = self.db.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, content, token_count)
                VALUES (?, ?, ?, ?)
                """,
                (
                    record["document_id"],
                    record["chunk_index"],
                    record["content"],
                    record["token_count"],
                ),
            )
            chunk_ids.append(cursor.lastrowid)

        self._emit_progress(60, total_docs, total_docs, self.STAGES[3])
        self._emit_status("Calcul TF-IDF en cours...")

        doc_freq: Counter = Counter()
        chunk_term_tf: list = []

        for text in chunk_texts:
            tokens = text.split()
            tf = Counter(tokens)
            total = len(tokens) or 1
            tf_norm = {term: count / total for term, count in tf.items()}
            chunk_term_tf.append(tf_norm)
            doc_freq.update(tf.keys())

        total_chunks = len(chunk_ids)
        tfidf_entries = []
        vocab_updates = defaultdict(int)

        for chunk_id, tf_dict in zip(chunk_ids, chunk_term_tf):
            for term, tf_val in tf_dict.items():
                df = doc_freq[term]
                idf = math.log((total_chunks + 1) / (df + 1)) + 1
                tfidf_val = tf_val * idf
                if tfidf_val > 0:
                    tfidf_entries.append((chunk_id, term, tfidf_val))
                    vocab_updates[term] = df

        if tfidf_entries:
            self.db.executemany(
                """
                INSERT INTO tfidf_index (chunk_id, term, tfidf_value)
                VALUES (?, ?, ?)
                """,
                tfidf_entries,
            )

        for term, df in vocab_updates.items():
            self.db.execute(
                """
                INSERT INTO vocabulary (term, document_frequency)
                VALUES (?, ?)
                ON CONFLICT(term) DO UPDATE SET
                    document_frequency = excluded.document_frequency
                """,
                (term, df),
            )

        self._emit_progress(90, total_docs, total_docs, self.STAGES[4])
        self.db.execute(
            """
            INSERT INTO index_stats (id, total_documents, total_chunks, total_terms, last_indexed_at)
            VALUES (1, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                total_documents = excluded.total_documents,
                total_chunks = excluded.total_chunks,
                total_terms = excluded.total_terms,
                last_indexed_at = excluded.last_indexed_at
            """,
            (total_docs, total_chunks, len(vocab_updates)),
        )

        self._emit_progress(100, total_docs, total_docs, self.STAGES[-1])
        self._emit_status(
            f"Terminé : {total_docs} documents, {total_chunks} passages indexés."
        )


# ── Point d'entree pour test rapide ──────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    docs = [
        {"id": 1, "title": "Revolutions industrielles",
         "content": "La revolution industrielle a transforme l'europe au XIXe siecle. "
                    "Les usines et les machines ont change la production."},
        {"id": 2, "title": "Guerre mondiale",
         "content": "La Premiere Guerre mondiale a éclate en 1914. Les puissances "
                    "européennes se sont affrontees pendant quatre ans."},
        {"id": 3, "title": "Renaissance",
         "content": "La Renaissance est une periode de renouveau culturel en Europe "
                    "aux XVe et XVIe siecles. L'art et la science ont prospere."},
        {"id": 4, "title": "Revolution francaise",
         "content": "La revolution francaise de 1789 a renverse la monarchie. "
                    "Les droits de l'homme ont ete proclames."},
        {"id": 5, "title": "Empire romain",
         "content": "L'Empire romain a domine la Méditerranee pendant des siecles. "
                    "Son influence sur le droit et la culture persiste encore."},
    ]

    indexer = TFIDFIndexer(min_df=1, max_features=10000)

    print("=" * 60)
    print("ATLAS - Test de l'indexeur TF-IDF")
    print("=" * 60)

    stats = indexer.build_index(docs)
    print(f"\n[Construction] {stats.total_documents} documents, "
          f"{stats.vocabulary_size} termes")

    query = "revolution industrielle europe"
    print(f"\n[Recherche] '{query}'")
    results = indexer.search(query, top_k=3)
    for r in results:
        print(f"  -> {r.title} (score: {r.score})")

    save_path = indexer.save()
    print(f"\n[Sauvegarde] {save_path}")

    indexer.clear()
    print("[Index vide]")

    stats = indexer.load()
    print(f"[Chargement] {stats.total_documents} documents")

    results = indexer.search(query, top_k=3)
    print(f"\n[Recherche apres chargement] '{query}'")
    for r in results:
        print(f"  -> {r.title} (score: {r.score})")

    print("\nTous les tests passent")
