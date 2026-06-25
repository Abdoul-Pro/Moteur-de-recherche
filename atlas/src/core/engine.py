import math
import sqlite3
from collections import Counter
from typing import Dict, List, Optional, Tuple

from src.core.preprocessor import TextPreprocessor
from src.database.connection import Database

from config import CHUNK_SIZE, TOP_N_TFIDF


class SearchEngine:
    """Moteur de recherche TF-IDF avec similarité cosinus."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.preprocessor = TextPreprocessor()
        self._idf_cache: Dict[str, float] = {}
        self._vocab_cache: Dict[str, int] = {}
        self._load_vocab_cache()

    def _load_vocab_cache(self):
        try:
            rows = self.db.fetchall("SELECT term, id FROM vocabulary")
        except Exception:
            rows = []
        self._vocab_cache = {row["term"]: row["id"] for row in rows}

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        counts = Counter(tokens)
        total = len(tokens)
        if total == 0:
            return {}
        return {term: count / total for term, count in counts.items()}

    def _compute_idf(self, term: str) -> float:
        if term in self._idf_cache:
            return self._idf_cache[term]

        row = self.db.fetchone(
            "SELECT document_frequency FROM vocabulary WHERE term = ?",
            (term,)
        )
        if not row or row["document_frequency"] == 0:
            return 0.0

        total_docs_row = self.db.fetchone("SELECT COUNT(*) as cnt FROM documents")
        total_docs = total_docs_row["cnt"] if total_docs_row else 1
        idf = math.log((total_docs + 1) / (row["document_frequency"] + 1)) + 1
        self._idf_cache[term] = idf
        return idf

    def search(
        self,
        query: str,
        period: Optional[str] = None,
        region: Optional[str] = None,
        author: Optional[str] = None,
        doc_type: Optional[str] = None,
        language: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int, float]:
        """Recherche par TF-IDF avec filtres optionnels.

        Returns:
            (results, total_count, search_time_ms)
        """
        import time
        start = time.perf_counter()

        query_tokens = self.preprocessor.process(query)
        if not query_tokens:
            return [], 0, 0.0

        query_tf = self._compute_tf(query_tokens)
        query_vector = {}
        for term, tf in query_tf.items():
            idf = self._compute_idf(term)
            if idf > 0:
                query_vector[term] = tf * idf

        if not query_vector:
            return [], 0, 0.0

        query_norm = math.sqrt(sum(v * v for v in query_vector.values()))
        if query_norm == 0:
            return [], 0, 0.0

        filter_clauses, filter_params = self._build_filter_clauses(
            period, region, author, doc_type, language, year_from, year_to
        )

        candidate_chunks = self._get_candidate_chunks(query_tokens, filter_clauses, filter_params)

        scored_results: Dict[int, float] = {}
        chunk_contents: Dict[int, str] = {}
        chunk_doc_ids: Dict[int, int] = {}

        for chunk_id, term, tfidf_val in candidate_chunks:
            if term in query_vector:
                if chunk_id not in scored_results:
                    scored_results[chunk_id] = 0.0
                scored_results[chunk_id] += query_vector[term] * tfidf_val

        for chunk_id in scored_results:
            row = self.db.fetchone(
                "SELECT c.content, c.document_id FROM chunks c WHERE c.id = ?",
                (chunk_id,)
            )
            if row:
                chunk_contents[chunk_id] = row["content"]
                chunk_doc_ids[chunk_id] = row["document_id"]

        chunk_norms = self._compute_chunk_norms(list(scored_results.keys()))

        final_scores = []
        for chunk_id, dot_product in scored_results.items():
            chunk_norm = chunk_norms.get(chunk_id, 1.0)
            similarity = dot_product / (query_norm * chunk_norm) if chunk_norm > 0 else 0.0
            final_scores.append((chunk_id, similarity))

        final_scores.sort(key=lambda x: x[1], reverse=True)

        total_count = len(final_scores)
        paginated = final_scores[offset:offset + limit]

        results = []
        for chunk_id, score in paginated:
            doc_id = chunk_doc_ids.get(chunk_id)
            doc_row = self.db.fetchone(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            )
            if doc_row:
                snippet = self._extract_snippet(
                    chunk_contents.get(chunk_id, ""),
                    query_tokens
                )
                results.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "title": doc_row["title"],
                    "author": doc_row["author"],
                    "period": doc_row["period"],
                    "region": doc_row["region"],
                    "source": doc_row["source"],
                    "date_publication": doc_row["date_publication"],
                    "snippet": snippet,
                    "score": round(score * 100, 1),
                    "file_path": doc_row["file_path"],
                })

        elapsed_ms = (time.perf_counter() - start) * 1000
        return results, total_count, elapsed_ms

    def _build_filter_clauses(
        self, period, region, author, doc_type, language, year_from, year_to
    ) -> Tuple[str, list]:
        clauses = []
        params = []

        if period:
            clauses.append("d.period LIKE ?")
            params.append(f"%{period}%")
        if region:
            clauses.append("d.region LIKE ?")
            params.append(f"%{region}%")
        if author:
            clauses.append("d.author LIKE ?")
            params.append(f"%{author}%")
        if doc_type:
            clauses.append("d.doc_type = ?")
            params.append(doc_type)
        if language:
            clauses.append("d.language = ?")
            params.append(language)
        if year_from:
            clauses.append("d.date_publication >= ?")
            params.append(str(year_from))
        if year_to:
            clauses.append("d.date_publication <= ?")
            params.append(str(year_to))

        clause_str = (" AND " + " AND ".join(clauses)) if clauses else ""
        return clause_str, params

    def _get_candidate_chunks(
        self, query_tokens: List[str], filter_clauses: str, filter_params: list
    ) -> List[Tuple[int, str, float]]:
        placeholders = ",".join("?" for _ in query_tokens)
        sql = f"""
            SELECT t.chunk_id, t.term, t.tfidf_value
            FROM tfidf_index t
            JOIN chunks c ON t.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE t.term IN ({placeholders})
            {filter_clauses}
            ORDER BY t.tfidf_value DESC
        """
        return self.db.fetchall(sql, tuple(query_tokens) + tuple(filter_params))

    def _compute_chunk_norms(self, chunk_ids: List[int]) -> Dict[int, float]:
        if not chunk_ids:
            return {}
        placeholders = ",".join("?" for _ in chunk_ids)
        sql = f"""
            SELECT chunk_id, SUM(tfidf_value * tfidf_value) as norm_sq
            FROM tfidf_index
            WHERE chunk_id IN ({placeholders})
            GROUP BY chunk_id
        """
        rows = self.db.fetchall(sql, tuple(chunk_ids))
        return {row["chunk_id"]: math.sqrt(row["norm_sq"]) for row in rows}

    def _extract_snippet(self, content: str, query_tokens: List[str], context_words: int = 30) -> str:
        words = content.split()
        best_start = 0
        best_score = 0

        for i in range(len(words) - context_words):
            window = " ".join(words[i:i + context_words * 2])
            window_tokens = set(self.preprocessor.process(window))
            score = len(set(query_tokens) & window_tokens)
            if score > best_score:
                best_score = score
                best_start = i

        snippet_words = words[best_start:best_start + context_words * 2]
        snippet = " ".join(snippet_words)
        if best_start > 0:
            snippet = "..." + snippet
        if best_start + context_words * 2 < len(words):
            snippet = snippet + "..."
        return snippet

    def log_search(self, query: str, filters: dict, result_count: int, search_time_ms: float):
        import json
        self.db.execute(
            "INSERT INTO search_history (query, filters, result_count, search_time_ms) VALUES (?, ?, ?, ?)",
            (query, json.dumps(filters), result_count, search_time_ms)
        )

    def get_stats(self) -> Dict:
        docs = self.db.fetchone("SELECT COUNT(*) as cnt FROM documents")
        chunks = self.db.fetchone("SELECT COUNT(*) as cnt FROM chunks")
        searches = self.db.fetchone("SELECT COUNT(*) as cnt FROM search_history")
        avg_time = self.db.fetchone("SELECT AVG(search_time_ms) as avg_ms FROM search_history")

        return {
            "total_documents": docs["cnt"] if docs else 0,
            "total_chunks": chunks["cnt"] if chunks else 0,
            "total_searches": searches["cnt"] if searches else 0,
            "avg_search_time_ms": round(avg_time["avg_ms"] or 0, 2),
        }

    def get_search_history(self, limit: int = 50) -> List[Dict]:
        rows = self.db.fetchall(
            "SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in rows]

    def get_analytics(self) -> Dict:
        precision_rows = self.db.fetchall(
            """
            SELECT searched_at, query, result_count
            FROM search_history
            ORDER BY searched_at DESC
            LIMIT 100
            """
        )

        period_rows = self.db.fetchall(
            "SELECT period, COUNT(*) as cnt FROM documents GROUP BY period ORDER BY cnt DESC"
        )

        frequent_queries = self.db.fetchall(
            "SELECT query, COUNT(*) as cnt FROM search_history GROUP BY query ORDER BY cnt DESC LIMIT 10"
        )

        return {
            "searches_over_time": [dict(r) for r in precision_rows],
            "documents_by_period": [dict(r) for r in period_rows],
            "frequent_queries": [dict(r) for r in frequent_queries],
        }
