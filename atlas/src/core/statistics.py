"""
statistics.py — Tableau de bord et statistiques pour Atlas.

Fonctionnalites :
    - Nombre de documents indexes
    - Nombre de recherches effectuees
    - Temps moyen de recherche
    - Statistiques TF-IDF
    - Graphiques simples avec matplotlib (optionnel)

Usage :
    from src.core.statistics import StatsCollector, DashboardPanel

    stats = StatsCollector()
    stats.record_search("revolution", 5, 12.3)
    print(stats.get_summary())
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from src.utils.datetime import now_local_str
from typing import Any, Dict, List, Optional, Tuple

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ── Couleurs du theme Atlas ──────────────────────────────────────────
GOLD = "#d4a843"
GOLD_LIGHT = "#e6b955"
BG_DARK = "#0a1628"
BG_CARD = "#0f2042"
TEXT_WHITE = "#ffffff"
TEXT_SECONDARY = "#8899b3"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_BLUE = "#3a7bd5"
ACCENT_ORANGE = "#f39c12"


# ── Dataclasses ──────────────────────────────────────────────────────
@dataclass
class SearchRecord:
    """Enregistrement d'une recherche."""
    query: str
    result_count: int
    time_ms: float
    timestamp: str = field(default_factory=now_local_str)
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentStats:
    """Statistiques d'un document."""
    doc_id: int
    title: str
    chunk_count: int
    avg_tfidf: float = 0.0
    top_terms: List[Tuple[str, float]] = field(default_factory=list)


@dataclass
class TFIDFStats:
    """Statistiques globales TF-IDF."""
    total_terms: int = 0
    avg_doc_length: float = 0.0
    vocabulary_richness: float = 0.0
    top_terms: List[Tuple[str, int]] = field(default_factory=list)
    avg_tfidf_per_doc: float = 0.0


# ── Collecteur de statistiques ───────────────────────────────────────
class StatsCollector:
    """Collecte et calcule les statistiques de l'application."""

    def __init__(self):
        self._documents: List[Dict[str, Any]] = []
        self._searches: List[SearchRecord] = []
        self._chunks_count: int = 0
        self._vocabulary_size: int = 0
        self._tfidf_stats: Optional[TFIDFStats] = None
        self._start_time = time.time()

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def set_documents(self, documents: List[Dict[str, Any]]):
        self._documents = documents

    def set_chunks_count(self, count: int):
        self._chunks_count = count

    def set_vocabulary_size(self, size: int):
        self._vocabulary_size = size

    def set_tfidf_stats(self, stats: TFIDFStats):
        self._tfidf_stats = stats

    def enregistrer_recherche(
        self,
        requete: str,
        nb_resultats: int,
        temps_ms: float,
        filtres: Optional[Dict[str, Any]] = None,
    ):
        """Enregistre une recherche dans l'historique."""
        entree = SearchRecord(
            query=requete,
            result_count=nb_resultats,
            time_ms=temps_ms,
            filters=filtres or {},
        )
        self._searches.append(entree)

    # Alias pour compatibilite
    record_search = enregistrer_recherche

    def get_resume(self) -> Dict[str, Any]:
        """Retourne un resume des statistiques."""
        total = len(self._searches)
        temps_moyen = (
            sum(s.time_ms for s in self._searches) / total if total > 0 else 0.0
        )
        resultats_moyens = (
            sum(s.result_count for s in self._searches) / total if total > 0 else 0.0
        )
        requetes_uniques = len(set(s.query.lower() for s in self._searches))

        return {
            "nb_documents": len(self._documents),
            "nb_passages": self._chunks_count,
            "nb_termes": self._vocabulary_size,
            "nb_recherches": total,
            "nb_requetes_uniques": requetes_uniques,
            "temps_moyen_ms": round(temps_moyen, 2),
            "resultats_moyens": round(resultats_moyens, 1),
            "duree_fonctionnement": round(self.uptime_seconds, 0),
            # Alias anglais pour le tableau de bord et les graphiques
            "total_documents": len(self._documents),
            "total_chunks": self._chunks_count,
            "vocabulary_size": self._vocabulary_size,
            "total_searches": total,
            "unique_queries": requetes_uniques,
            "avg_search_time_ms": round(temps_moyen, 2),
            "avg_results": round(resultats_moyens, 1),
            "uptime_seconds": round(self.uptime_seconds, 0),
        }

    # Alias pour compatibilite
    get_summary = get_resume

    def get_historique(self, limite: int = 50) -> List[Dict[str, Any]]:
        """Retourne l'historique des recherches."""
        return [
            {
                "requete": s.query,
                "nb_resultats": s.result_count,
                "temps_ms": s.time_ms,
                "timestamp": s.timestamp,
                # Alias anglais pour le tableau de bord
                "query": s.query,
                "result_count": s.result_count,
                "time_ms": s.time_ms,
            }
            for s in reversed(self._searches[-limite:])
        ]

    # Alias pour compatibilite
    get_search_history = get_historique

    def get_requetes_frequentes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Retourne les requetes les plus utilisees."""
        compteur: Dict[str, int] = defaultdict(int)
        for s in self._searches:
            compteur[s.query.lower()] += 1
        return sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Alias pour compatibilite
    get_frequent_queries = get_requetes_frequentes

    def get_time_distribution(self) -> List[Dict[str, Any]]:
        if not self._searches:
            return []
        buckets = defaultdict(int)
        for s in self._searches:
            if s.time_ms < 5:
                buckets["< 5ms"] += 1
            elif s.time_ms < 20:
                buckets["5-20ms"] += 1
            elif s.time_ms < 50:
                buckets["20-50ms"] += 1
            elif s.time_ms < 100:
                buckets["50-100ms"] += 1
            else:
                buckets["> 100ms"] += 1
        return [{"range": k, "count": v} for k, v in buckets.items()]

    def get_tfidf_stats(self) -> Dict[str, Any]:
        if self._tfidf_stats:
            return {
                "total_terms": self._tfidf_stats.total_terms,
                "avg_doc_length": self._tfidf_stats.avg_doc_length,
                "vocabulary_richness": self._tfidf_stats.vocabulary_richness,
                "top_terms": self._tfidf_stats.top_terms,
                "avg_tfidf_per_doc": self._tfidf_stats.avg_tfidf_per_doc,
            }
        return {
            "total_terms": self._vocabulary_size,
            "avg_doc_length": 0,
            "vocabulary_richness": 0,
            "top_terms": [],
            "avg_tfidf_per_doc": 0,
        }


# ── Panel de dashboard (CustomTkinter) ──────────────────────────────
def create_dashboard_panel(parent, stats: StatsCollector, **kw):
    """Cree un panel de dashboard complet dans le parent donne."""
    import customtkinter as ctk

    FONT = "Segoe UI"

    frame = ctk.CTkFrame(parent, fg_color="#0a1628", **kw)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)

    # En-tete
    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 0))
    ctk.CTkLabel(header, text="Tableau de bord", font=(FONT, 24, "bold"),
                 text_color=TEXT_WHITE).pack(side="left")
    ctk.CTkLabel(header, text="Statistiques et metriques en temps reel",
                 font=(FONT, 12), text_color=TEXT_SECONDARY).pack(
        side="left", padx=(16, 0), pady=(4, 0))

    # Cartes de metriques
    summary = stats.get_summary()
    metric_frame = ctk.CTkFrame(frame, fg_color="transparent")
    metric_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 0))
    metric_frame.columnconfigure((0, 1, 2, 3), weight=1)

    metric_data = [
        ("Documents indexes", str(summary["total_documents"]), "\U0001f4da"),
        ("Recherches effectuees", str(summary["total_searches"]), "\U0001f50d"),
        ("Temps moyen", f"{summary['avg_search_time_ms']:.0f} ms", "\u23f1\ufe0f"),
        ("Vocabulaire", str(summary["vocabulary_size"]), "\U0001f4d6"),
    ]

    metric_cards = []
    for i, (title, value, icon) in enumerate(metric_data):
        card = ctk.CTkFrame(metric_frame, fg_color="#0f2042", corner_radius=12,
                            border_width=1, border_color="#1a3055")
        card.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(card, text=icon, font=(FONT, 22)).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(card, text=value, font=(FONT, 28, "bold"),
                     text_color=GOLD).grid(row=1, column=0, sticky="w",
                                           padx=16, pady=(4, 0))
        ctk.CTkLabel(card, text=title, font=(FONT, 11),
                     text_color=TEXT_SECONDARY).grid(row=2, column=0,
                                                     sticky="w", padx=16,
                                                     pady=(0, 14))
        metric_cards.append(card)

    # Section graphiques + details
    scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(16, 24))
    scroll.columnconfigure((0, 1), weight=1)

    # Graphique TF-IDF (si matplotlib disponible)
    tfidf_card = ctk.CTkFrame(scroll, fg_color="#0f2042", corner_radius=12,
                               border_width=1, border_color="#1a3055")
    tfidf_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
    tfidf_card.columnconfigure(0, weight=1)

    ctk.CTkLabel(tfidf_card, text="Top termes TF-IDF", font=(FONT, 16, "bold"),
                 text_color=TEXT_WHITE).grid(row=0, column=0, sticky="w",
                                             padx=16, pady=(14, 8))

    top_terms = stats.get_tfidf_stats().get("top_terms", [])
    if top_terms:
        for i, (term, freq) in enumerate(top_terms[:8]):
            row = ctk.CTkFrame(tfidf_card, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=16, pady=2)
            ctk.CTkLabel(row, text=term, font=(FONT, 12),
                         text_color=TEXT_WHITE, width=120,
                         anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, fg_color="#1a3055",
                                     progress_color=GOLD, height=8)
            bar.pack(side="left", fill="x", expand=True, padx=(8, 8))
            max_freq = top_terms[0][1] if top_terms else 1
            bar.set(freq / max_freq if max_freq > 0 else 0)
            ctk.CTkLabel(row, text=str(freq), font=(FONT, 11),
                         text_color=TEXT_SECONDARY, width=40).pack(side="right")
    else:
        ctk.CTkLabel(tfidf_card, text="Aucune donnee TF-IDF",
                     font=(FONT, 12), text_color=TEXT_SECONDARY).grid(
            row=1, column=0, pady=20)

    # Requetes frequentes
    freq_card = ctk.CTkFrame(scroll, fg_color="#0f2042", corner_radius=12,
                              border_width=1, border_color="#1a3055")
    freq_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
    freq_card.columnconfigure(0, weight=1)

    ctk.CTkLabel(freq_card, text="Requetes frequentes", font=(FONT, 16, "bold"),
                 text_color=TEXT_WHITE).grid(row=0, column=0, sticky="w",
                                             padx=16, pady=(14, 8))

    freq = stats.get_frequent_queries(8)
    if freq:
        for i, (query, count) in enumerate(freq):
            row = ctk.CTkFrame(freq_card, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=16, pady=2)
            ctk.CTkLabel(row, text=f"{i+1}.", font=(FONT, 12, "bold"),
                         text_color=GOLD, width=24).pack(side="left")
            ctk.CTkLabel(row, text=query, font=(FONT, 12),
                         text_color=TEXT_WHITE).pack(side="left", padx=(4, 0))
            ctk.CTkLabel(row, text=f"{count}x", font=(FONT, 11),
                         text_color=TEXT_SECONDARY).pack(side="right")
    else:
        ctk.CTkLabel(freq_card, text="Aucune recherche encore",
                     font=(FONT, 12), text_color=TEXT_SECONDARY).grid(
            row=1, column=0, pady=20)

    # Distribution des temps de recherche
    time_card = ctk.CTkFrame(scroll, fg_color="#0f2042", corner_radius=12,
                              border_width=1, border_color="#1a3055")
    time_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
    time_card.columnconfigure(0, weight=1)

    ctk.CTkLabel(time_card, text="Distribution des temps", font=(FONT, 16, "bold"),
                 text_color=TEXT_WHITE).grid(row=0, column=0, sticky="w",
                                             padx=16, pady=(14, 8))

    dist = stats.get_time_distribution()
    if dist:
        max_count = max(d["count"] for d in dist) if dist else 1
        for i, d in enumerate(dist):
            row = ctk.CTkFrame(time_card, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=16, pady=2)
            ctk.CTkLabel(row, text=d["range"], font=(FONT, 12),
                         text_color=TEXT_WHITE, width=80,
                         anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, fg_color="#1a3055",
                                     progress_color=ACCENT_BLUE, height=8)
            bar.pack(side="left", fill="x", expand=True, padx=(8, 8))
            bar.set(d["count"] / max_count if max_count > 0 else 0)
            ctk.CTkLabel(row, text=str(d["count"]), font=(FONT, 11),
                         text_color=TEXT_SECONDARY, width=30).pack(side="right")
    else:
        ctk.CTkLabel(time_card, text="Aucune donnee",
                     font=(FONT, 12), text_color=TEXT_SECONDARY).grid(
            row=1, column=0, pady=20)

    # Dernieres recherches
    recent_card = ctk.CTkFrame(scroll, fg_color="#0f2042", corner_radius=12,
                                border_width=1, border_color="#1a3055")
    recent_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
    recent_card.columnconfigure(0, weight=1)

    ctk.CTkLabel(recent_card, text="Dernieres recherches",
                 font=(FONT, 16, "bold"),
                 text_color=TEXT_WHITE).grid(row=0, column=0, sticky="w",
                                             padx=16, pady=(14, 8))

    history = stats.get_search_history(8)
    if history:
        for i, h in enumerate(history):
            row = ctk.CTkFrame(recent_card, fg_color="transparent")
            row.grid(row=i + 1, column=0, sticky="ew", padx=16, pady=2)

            ctk.CTkLabel(row, text=h["timestamp"], font=(FONT, 10),
                         text_color=TEXT_SECONDARY, width=44).pack(side="left")
            ctk.CTkLabel(row, text=h["query"][:25], font=(FONT, 12),
                         text_color=TEXT_WHITE).pack(side="left", padx=(8, 0))
            ctk.CTkLabel(row, text=f"{h['result_count']}res",
                         font=(FONT, 11), text_color=GOLD).pack(side="right")
    else:
        ctk.CTkLabel(recent_card, text="Aucune activite",
                     font=(FONT, 12), text_color=TEXT_SECONDARY).grid(
            row=1, column=0, pady=20)

    return frame, metric_cards


# ── Graphiques matplotlib ───────────────────────────────────────────
def create_matplotlib_charts(
    parent, stats: StatsCollector, **kw
):
    """Cree des graphiques matplotlib integres dans l'interface.

    Retourne (frame, canvas) ou None si matplotlib indisponible.
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    import customtkinter as ctk

    frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12,
                         border_width=1, border_color="#1a3055", **kw)

    fig = Figure(figsize=(8, 5), dpi=100, facecolor=BG_CARD)
    fig.subplots_adjust(hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_facecolor(BG_CARD)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#1a3055")

    summary = stats.get_summary()

    # 1. Pie chart : documents vs vocabulaire
    sizes = [summary["total_documents"], summary["vocabulary_size"]]
    labels = ["Documents", "Termes"]
    colors = [GOLD, ACCENT_BLUE]
    ax1.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%",
            textprops={"color": TEXT_WHITE, "fontsize": 8}, startangle=90)
    ax1.set_title("Repartition", color=TEXT_WHITE, fontsize=10)

    # 2. Bar chart : requetes frequentes
    freq = stats.get_frequent_queries(5)
    if freq:
        queries = [f[0][:12] for f in freq]
        counts = [f[1] for f in freq]
        ax2.barh(queries, counts, color=GOLD, height=0.6)
        ax2.set_title("Requetes frequentes", color=TEXT_WHITE, fontsize=10)
        ax2.set_xlabel("Nombre", color=TEXT_SECONDARY, fontsize=8)
    else:
        ax2.text(0.5, 0.5, "Aucune donnee", ha="center", va="center",
                 color=TEXT_SECONDARY, fontsize=10, transform=ax2.transAxes)
        ax2.set_title("Requetes frequentes", color=TEXT_WHITE, fontsize=10)

    # 3. Bar chart : temps de recherche
    dist = stats.get_time_distribution()
    if dist:
        ranges = [d["range"] for d in dist]
        counts = [d["count"] for d in dist]
        ax3.bar(ranges, counts, color=ACCENT_GREEN, width=0.6)
        ax3.set_title("Temps de recherche", color=TEXT_WHITE, fontsize=10)
        ax3.set_ylabel("Nombre", color=TEXT_SECONDARY, fontsize=8)
        ax3.tick_params(axis="x", rotation=30)
    else:
        ax3.text(0.5, 0.5, "Aucune donnee", ha="center", va="center",
                 color=TEXT_SECONDARY, fontsize=10, transform=ax3.transAxes)
        ax3.set_title("Temps de recherche", color=TEXT_WHITE, fontsize=10)

    # 4. Bar chart : top termes TF-IDF
    tfidf = stats.get_tfidf_stats()
    top_terms = tfidf.get("top_terms", [])[:6]
    if top_terms:
        terms = [t[0][:10] for t in top_terms]
        vals = [t[1] for t in top_terms]
        ax4.barh(terms, vals, color=ACCENT_ORANGE, height=0.6)
        ax4.set_title("Top termes TF-IDF", color=TEXT_WHITE, fontsize=10)
        ax4.set_xlabel("Frequence", color=TEXT_SECONDARY, fontsize=8)
    else:
        ax4.text(0.5, 0.5, "Aucune donnee", ha="center", va="center",
                 color=TEXT_SECONDARY, fontsize=10, transform=ax4.transAxes)
        ax4.set_title("Top termes TF-IDF", color=TEXT_WHITE, fontsize=10)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    return frame, canvas


# ── Point d'entree pour test ────────────────────────────────────────
if __name__ == "__main__":
    stats = StatsCollector()

    stats.set_documents([{"id": i} for i in range(10)])
    stats.set_chunks_count(38)
    stats.set_vocabulary_size(144)

    stats.set_tfidf_stats(TFIDFStats(
        total_terms=144,
        avg_doc_length=85.0,
        vocabulary_richness=0.72,
        top_terms=[("revolution", 8), ("industrielle", 6), ("europe", 5),
                   ("travail", 4), ("siecle", 4), ("guerre", 3)],
        avg_tfidf_per_doc=0.15,
    ))

    queries = [
        ("revolution industrielle", 4, 5.2),
        ("guerre mondiale", 2, 3.1),
        ("renaissance art", 3, 4.5),
        ("revolution industrielle europe", 4, 5.8),
        ("empire romain", 2, 2.9),
        ("revolution", 5, 6.1),
        ("guerre", 3, 3.4),
    ]
    for q, n, t in queries:
        stats.record_search(q, n, t)

    summary = stats.get_summary()
    print("=" * 50)
    print("ATLAS - Test du module statistics")
    print("=" * 50)
    print(f"  Documents: {summary['total_documents']}")
    print(f"  Recherches: {summary['total_searches']}")
    print(f"  Temps moyen: {summary['avg_search_time_ms']}ms")
    print(f"  Vocabulaire: {summary['vocabulary_size']} termes")
    print(f"  Requetes frequentes: {stats.get_frequent_queries(3)}")
    print(f"  Distribution temps: {stats.get_time_distribution()}")
    print(f"  Top termes TF-IDF: {stats.get_tfidf_stats()['top_terms'][:3]}")
    print("\nTous les tests passent")
