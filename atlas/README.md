# Atlas

**Moteur de recherche de documents historiques**  

Atlas est une application de bureau permettant d'indexer, rechercher et consulter des documents historiques. Elle utilise l'algorithme **TF-IDF** (Term Frequency–Inverse Document Frequency) couplé à la **similarité cosinus** pour retrouver les passages les plus pertinents dans un corpus de documents.

---

## Fonctionnalités

| Module | Description |
|--------|-------------|
| **Recherche simple** | Requête en langage naturel avec résultats classés par pertinence |
| **Recherche avancée** | Filtres par période historique, région, auteur, type de document et plage d'années |
| **Import de documents** | Import de fichiers `.txt`, `.pdf`, `.docx` avec extraction automatique du contenu |
| **Saisie manuelle** | Création directe de documents avec métadonnées |
| **Indexation** | Indexation TF-IDF en temps réel avec barre de progression et journal |
| **Statistiques** | Nombre de documents, passages, vocabulaire, temps moyen de recherche |
| **Historique** | Consultation de toutes les recherches effectuées |
| **Export** | Export CSV ou JSON avec choix de l'emplacement de sauvegarde |
| **Sauvegarde** | Copie de sécurité de la base de données SQLite |
| **À propos** | Informations sur l'équipe et les technologies utilisées |

---

## Aperçu

L'application propose une interface en **mode sombre** avec un thème navy/or, une barre latérale de navigation et des pages scrollables.

```
┌──────────────┬────────────────────────────────────────────┐
│              │  🔍 Rechercher...                    [Go]  │
│  🧭 Atlas    │────────────────────────────────────────────│
│              │                                            │
│  🏠 Accueil  │  #  Titre du document             85.5%  │
│  🔍 Recherche│     Extrait contenant les mots-clés...     │
│  🔬 Avancée  │     Auteur · Période · Région              │
│  📊 Analyse  │────────────────────────────────────────────│
│  📋 Historiq │  #  Deuxième résultat              72.3%  │
│  ⚙️ Indexat. │     Autre extrait pertinent...             │
│  📄 Importer │     Auteur · Période · Région              │
│  📤 Export   │                                            │
│  💾 Sauveg.  │                                            │
│  ℹ️ À propos │                                            │
│──────────────│  ← 1  2  3  →                              │
│ ● Opérationnel│                                            │
└──────────────┴────────────────────────────────────────────┘
```

---

## Installation

### Prérequis

- **Python 3.10** ou supérieur
- **pip** (gestionnaire de paquets)

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/Abdoul-Pro/Moteur-de-recherche.git

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

> Au premier lancement, les documents de démonstration sont chargés automatiquement dans la base de données.

---

## Structure du projet

```
atlas/
├── main.py                         # Point d'entrée de l'application
├── config.py                       # Configuration générale (chemins, constantes)
├── requirements.txt                # Dépendances Python
├── README.md                       # Ce fichier
│
├── src/
│   ├── core/
│   │   ├── preprocessing.py        # Nettoyage, tokenisation, stemming (NLP)
│   │   ├── preprocessor.py         # Préprocesseur alternatif (NLTK)
│   │   ├── indexer.py              # Indexation TF-IDF avec scikit-learn
│   │   ├── engine.py               # Moteur de recherche (DB-based)
│   │   ├── search_engine.py        # Moteur de recherche (in-memory)
│   │   └── statistics.py           # Collecte et affichage des statistiques
│   │
│   ├── database/
│   │   ├── database.py             # Schéma SQL, requêtes CRUD
│   │   └── connection.py           # Gestionnaire de connexion SQLite
│   │
│   ├── ui/
│   │   ├── theme.py                # Thème global, couleurs, polices, helpers
│   │   ├── components/
│   │   │   ├── sidebar.py          # Barre latérale de navigation
│   │   │   └── widgets.py          # SearchBar, ResultCard, StatCard, Pagination
│   │   └── pages/
│   │       ├── home.py             # Page d'accueil
│   │       ├── search.py           # Page de résultats de recherche
│   │       ├── advanced.py         # Recherche avancée avec filtres
│   │       ├── analytics.py        # Tableau d'analyse et métriques
│   │       ├── history.py          # Historique des recherches
│   │       ├── indexing.py         # Page d'indexation avec progression
│   │       ├── import_doc.py       # Import de documents (fichier + manuel)
│   │       ├── document.py         # Consultation d'un document
│   │       └── about.py            # Page À propos
│   │
│   └── utils/
│       ├── constants.py            # Constantes partagées
│       └── datetime.py             # Utilitaires de date/heure
│
├── data/
│   ├── atlas.db                    # Base de données SQLite
│   └── index/                      # Sauvegarde de l'index TF-IDF
│
├── backups/                        # Sauvegardes de la base de données
├── exports/                        # Fichiers exportés (CSV/JSON)
```

---

## Technologies

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.10+ | Langage principal |
| **CustomTkinter** | ≥5.2.0 | Interface graphique moderne (mode sombre) |
| **scikit-learn** | ≥1.3.0 | Vectorisation TF-IDF et similarité cosinus |
| **NLTK** | ≥3.8.0 | Tokenisation et stemming (Snowball) |
| **SQLite** | — | Base de données locale |
| **NumPy** | ≥1.24.0 | Calculs numériques |
| **PyPDF2** | ≥3.0.0 | Extraction de texte depuis PDF |
| **python-docx** | ≥0.8.11 | Extraction de texte depuis Word |

---

## Architecture

### Pipeline de recherche

```
Requête utilisateur
       │
       ▼
┌─────────────┐
│ Prétraitement│  ← Nettoyage, tokenisation, stemming
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Vectorisation│  ← Transformation en vecteur TF-IDF
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Similarité       │  ← Calcul cosinus avec tous les documents
│ cosinus          │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│ Classement   │  ← Tri par score de pertinence
│ + Filtres    │  ← Application des filtres optionnels
└──────┬──────┘
       │
       ▼
  Résultats affichés
```

### Base de données

| Table | Description |
|-------|-------------|
| `documents` | Documents historiques avec métadonnées |
| `chunks` | Passages découpés pour l'indexation |
| `tfidf_index` | Index inversé des valeurs TF-IDF |
| `vocabulary` | Vocabulaire avec fréquence documentaire |
| `search_history` | Historique des recherches effectuées |
| `index_stats` | Statistiques globales d'indexation |

---

## Utilisation

### Recherche simple

1. Ouvrir l'application
2. Saisir une requête dans la barre de recherche (Accueil ou Recherche)
3. Appuyer sur **Entrée** ou cliquer sur **Rechercher**
4. Les résultats s'affichent avec un score de pertinence et des extraits surlignés

### Recherche avancée

1. Naviguer vers **Recherche avancée**
2. Saisir une requête
3. Appliquer les filtres souhaités (période, région, auteur, type, années)
4. Cliquer sur **Appliquer les filtres**

### Import de documents

**Par fichier :**
1. Naviguer vers **Ajouter un document**
2. Cliquer sur **Choisir un fichier** (`.txt`, `.pdf`, `.docx`)
3. Cliquer sur **Importer et indexer**

**Saisie manuelle :**
1. Remplir les champs (Titre obligatoire, Auteur, Source, etc.)
2. Saisir le contenu dans la zone de texte
3. Cliquer sur **Importer et indexer**

### Indexation

1. Naviguer vers **Indexation**
2. Cliquer sur **Démarrer l'indexation**
3. Suivre la progression en temps réel
4. Les statistiques se mettent à jour automatiquement

### Export

1. Naviguer vers **Export**
2. Choisir le format (CSV ou JSON)
3. Cliquer sur **Exporter**
4. Choisir l'emplacement de sauvegarde

---

## Exemples de recherches

| Requête | Résultats |
|---------|-----------|
| `Empire du Mali` | Documents sur l'histoire et l'expansion de l'Empire du Mali |
| `Thomas Sankara` | Documents relatifs à la révolution burkinabè |
| `AES` | Documents concernant l'Alliance des États du Sahel |
| `Mossi` | Documents sur les royaumes mossi |
| `Samory Touré` | Documents sur la résistance africaine à la colonisation |
| `Burkina Faso` | Documents sur l'histoire politique et sociale |
| `Colonisation Afrique Ouest` | Documents sur la période coloniale |
| `Indépendance` | Documents relatifs aux indépendances africaines |

---

## Notes techniques

### TF-IDF

**Term Frequency–Inverse Document Frequency** mesure l'importance d'un mot dans un document par rapport au corpus entier :

- **TF** (fréquence du terme) : nombre d'occurrences du mot dans le document
- **IDF** (fréquence inverse) : `log(N / df)` où `N` = nombre total de documents et `df` = nombre de documents contenant le mot

Un mot fréquent dans un document mais rare dans le corpus aura un score TF-IDF élevé.

### Similarité cosinus

Mesure l'angle entre le vecteur de la requête et chaque vecteur document. Le score varie de **0** (aucune similarité) à **1** (identique). Formule :

```
similarité = (A · B) / (‖A‖ × ‖B‖)
```

### Découpage en passages (Chunking)

Les documents sont découpés en passages de **500 mots** avec un chevauchement de **50 mots** pour maintenir le contexte entre les segments.

---

## Équipe

| Membre | Rôle |
|--------|------|
| **SORE Abdoul Fadal** | Chef de projet & Intégration |
| **SAWADOGO Idrissa** | Base de données SQLite |
| **GOUEM Aboubacar Sidiki** | Prétraitement NLP |
| **SAWADOGO Djemila** | TF-IDF et moteur de recherche |
| **DICKO Idrissa Barkey Kalilou** | Interface graphique CustomTkinter |

---

## Licence

Projet réalisé dans le cadre académique — Groupe 5.
Usage éducatif.
