# ATLAS

**Moteur de recherche de textes historiques**

ATLAS est une application de bureau permettant d'indexer, rechercher et consulter des documents historiques. Elle utilise l'algorithme **TF-IDF** couplé à la **similarité cosinus** pour retrouver les passages les plus pertinents dans un corpus de documents.

Le nom ATLAS symbolise la connaissance, l'orientation et la découverte — un outil qui guide les chercheurs vers les informations historiques.

---

## Fonctionnalités

| Module | Description |
|--------|-------------|
| **Recherche simple** | Requête en langage naturel avec résultats classés par pertinence |
| **Recherche avancée** | Filtres par période historique, région, auteur, type de document et plage d'années |
| **Import de documents** | Import de fichiers `.txt`, `.pdf`, `.docx` avec extraction automatique du contenu |
| **Saisie manuelle** | Création directe de documents avec métadonnées (titre, auteur, source, période, région) |
| **Indexation** | Indexation TF-IDF en arrière-plan avec barre de progression et journal en temps réel |
| **Tableau de bord** | Métriques globales, distribution des documents, requêtes fréquentes |
| **Historique** | Consultation de toutes les recherches effectuées avec horodatage |
| **Export** | Export CSV ou JSON avec choix de l'emplacement de sauvegarde |
| **Sauvegarde** | Gestion complète : création, restauration et suppression de sauvegardes |
| **Réinitialisation** | Réinitialisation totale ou partielle de la base de données |
| **À propos** | Informations sur l'équipe et les technologies utilisées |

---

## Installation

### Prérequis

- **Python 3.10** ou supérieur
- **pip** (gestionnaire de paquets)

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Abdoul-Pro/Moteur-de-recherche.git
cd Moteur-de-recherche

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

### Exécutable (.exe)

Un exécutable autonome est disponible dans `dist/Atlas.exe`.

Pour créer l'exécutable :
```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name Atlas main.py
```

> **Note** : La première exécution de l'exe prend quelques secondes (extraction des modules Python). Les données sont stockées dans `%LOCALAPPDATA%\Atlas\`.

---

## Structure du projet

```
atlas/
├── main.py                     # Point d'entrée
├── config.py                   # Configuration centralisée (chemins, constantes)
├── requirements.txt            # Dépendances Python
├── README.md                   # Cette documentation
│
├── core/                       # Logique métier
│   ├── preprocessing.py        # Nettoyage, tokenisation, stemming (NLP)
│   ├── preprocessor.py         # Préprocesseur NLTK (wrapper)
│   ├── indexer.py              # Indexeur TF-IDF et DocumentIndexer
│   └── engine.py               # Moteur de recherche DB-based
│
├── database/                   # Couche d'accès aux données
│   ├── __init__.py             # Réexport des fonctions publiques
│   ├── connection.py           # Gestionnaire de connexion SQLite
│   └── database.py             # Schéma SQL, CRUD et réinitialisation
│
├── windows/                    # Interface graphique (CustomTkinter)
│   ├── app.py                  # Application principale (AtlasApp)
│   ├── theme.py                # Thème : couleurs, polices, helpers
│   ├── components/
│   │   ├── sidebar.py          # Barre latérale de navigation
│   │   └── widgets.py          # SearchBar, ResultCard, StatCard, Pagination
│   └── pages/
│       ├── home.py             # Page d'accueil
│       ├── search.py           # Page de résultats de recherche
│       ├── advanced.py         # Recherche avancée avec filtres
│       ├── analytics.py        # Tableau de bord analytique
│       ├── history.py          # Historique des recherches
│       ├── indexing.py         # Page d'indexation
│       ├── import_doc.py       # Import de documents
│       ├── document.py         # Visionneuse de document
│       ├── sauvegarde.py       # Gestion des sauvegardes
│       ├── reset_db.py         # Réinitialisation de la base
│       └── about.py            # Page À propos
│
├── utils/                      # Utilitaires
│   └── datetime.py             # Fonctions de formatage date/heure
│
├── data/
│   ├── atlas.db                # Base de données SQLite
│   └── backups/                # Sauvegardes de la base de données
│
├── assets/                     # Ressources graphiques
│   └── icons/                  # Icônes (logo, navigation)
│
└── dist/
    └── Atlas.exe               # Exécutable Windows compilé
```

---

## Technologies

| Technologie | Rôle |
|-------------|------|
| **Python** | Langage principal |
| **SQLite** | Base de données locale (6 tables, 6 index) |
| **NLTK** | Tokenisation, stemming Snowball, mots vides français |
| **Scikit-Learn** | Vectorisation TF-IDF, matrices creuses |
| **CustomTkinter** | Interface graphique moderne (mode sombre) |
| **Pillow** | Gestion des images (logo, icônes) |
| **PyPDF2** | Extraction de texte depuis PDF |
| **python-docx** | Extraction de texte depuis Word |
| **Joblib** | Sérialisation de l'index TF-IDF |
| **PyInstaller** | Compilation en exécutable Windows |

---

## Architecture

### Séparation des couches

```
┌─────────────────────────────────────────┐
│       Couche Présentation               │
│       windows/ (CustomTkinter)          │
├─────────────────────────────────────────┤
│       Couche Traitement                 │
│       core/                             │
│   preprocessing → preprocessor → engine │
│               indexer                   │
├─────────────────────────────────────────┤
│       Couche Données                    │
│       database/                         │
│       connection → database             │
├─────────────────────────────────────────┤
│       Utilitaires                       │
│       utils/ (datetime)                 │
└─────────────────────────────────────────┘
```

### Pipeline de recherche

```
Requête utilisateur
       │
       ▼
┌─────────────┐
│ Prétraitement│  ← Nettoyage, tokenisation, stemming Snowball
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Vectorisation│  ← Transformation en vecteur TF-IDF
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Similarité       │  ← Calcul cosinus avec les passages stockés
│ cosinus          │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│ Classement   │  ← Tri par score de pertinence (50%-95%)
│ + Filtres    │  ← Application des filtres optionnels
└──────┬──────┘
       │
       ▼
  Résultats affichés
```

### Base de données SQLite

| Table | Description |
|-------|-------------|
| `documents` | Documents historiques avec métadonnées (titre, auteur, période, région, contenu) |
| `chunks` | Passages découpés (~100 mots) pour l'indexation |
| `tfidf_index` | Index inversé reliant chaque passage aux termes TF-IDF |
| `vocabulary` | Vocabulaire avec fréquence documentaire |
| `search_history` | Historique des recherches (requête, filtres, résultats, temps) |
| `index_stats` | Statistiques globales (nb documents, chunks, termes, dernière indexation) |

---

## Utilisation

### Recherche simple

1. Ouvrir l'application
2. Saisir une requête dans la barre de recherche
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
1. Remplir les champs (Titre obligatoire, Auteur, Source, Période, Région, Langue)
2. Saisir le contenu dans la zone de texte
3. Cliquer sur **Importer et indexer**

### Indexation

1. Naviguer vers **Indexation**
2. Cliquer sur **Démarrer l'indexation**
3. Suivre la progression en temps réel (barre + journal)
4. Les statistiques se mettent à jour automatiquement

### Export

1. Naviguer vers **Export**
2. Choisir le format (CSV ou JSON)
3. Cliquer sur **Exporter**
4. Choisir l'emplacement de sauvegarde

### Sauvegarde

1. Naviguer vers **Sauvegarde**
2. Saisir un nom pour identifier la sauvegarde
3. Cliquer sur **Sauvegarder**
4. Pour restaurer : cliquer sur **Restaurer** à côté de la sauvegarde souhaitée
5. Pour supprimer : cliquer sur **Supprimer** à côté de la sauvegarde

### Réinitialisation de la base de données

1. Naviguer vers **Réinitialiser**
2. Voir l'état actuel (nombre de documents, passages, termes, recherches)
3. Choisir une option :
   - **Réinitialiser tout** — Supprime documents, index, vocabulaire et historique
   - **Supprimer les documents** — Supprime documents et index, conserve l'historique
4. Confirmer l'action
5. Importer vos propres documents via **Ajouter un document**

---

## Notes techniques

### TF-IDF

**Term Frequency–Inverse Document Frequency** mesure l'importance d'un mot dans un document par rapport au corpus :

- **TF** : nombre d'occurrences du mot dans le passage / nombre total de mots
- **IDF** : `log((N+1) / (df+1)) + 1` où N = nombre total de passages, df = nombre de passages contenant le mot
- **Score** : `TF × IDF`

Un mot fréquent dans un passage mais rare dans le corpus aura un score TF-IDF élevé.

### Similarité cosinus

Mesure l'angle entre le vecteur de la requête et chaque vecteur de passage. Les scores sont normalisés entre **50%** et **95%** pour un affichage intuitif.

### Prétraitement NLP

Le pipeline de traitement suit ces étapes :
1. **Nettoyage** : suppression HTML, normalisation Unicode (NFKD), encodage ASCII
2. **Tokenisation** : découpage en mots via NLTK `word_tokenize`
3. **Filtrage** : suppression des mots vides, mots courts (< 2 lettres), chiffres
4. **Stemming** : réduction à la racine avec Snowball (français)

---

## Thème visuel

| Élément | Couleur |
|---------|---------|
| Fond principal | `#0a1628` (bleu nuit) |
| Sidebar | `#0c1d36` |
| Cartes | `#0f2042` |
| Accent principal | `#d4a843` (doré) |
| Texte principal | `#ffffff` |
| Texte secondaire | `#8899b3` |

---

## Équipe

| Membre | Rôle |
|--------|------|
| **SORE Abdoul Fadal** | Chef de projet & Intégration |
| **SAWADOGO Idrissa** | Base de données SQLite |
| **GOUEM Aboubacar Sidiki** | Prétraitement NLP |
| **SAWADOGO Djemila** | TF-IDF et moteur de recherche |
| **DICKO Idrissa Barkey Kalilou** | Interface graphique CustomTkinter |

**Professeur encadrant** : Dr Arthur SAWADOGO

**Année académique** : 2025–2026

**Université** : Université Joseph Ki-Zerbo — IFOAD
