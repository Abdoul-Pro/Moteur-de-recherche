# Atlas

**Moteur de recherche de documents historiques — Multiplateforme**

Atlas est une application multiplateforme permettant d'indexer, rechercher et consulter des documents historiques. Elle utilise l'algorithme **TF-IDF** couplé à la **similarité cosinus** pour retrouver les passages les plus pertinents dans un corpus de documents.

Supporte **Windows** (CustomTkinter) et **Android** (Kivy) avec une seule base de code Python.

---

## Fonctionnalités

| Module | Description |
|--------|-------------|
| **Recherche simple** | Requête en langage naturel avec résultats classés par pertinence |
| **Recherche avancée** | Filtres par période historique, région, auteur, type de document et plage d'années |
| **Import de documents** | Import de fichiers `.txt`, `.pdf`, `.docx` avec extraction automatique du contenu |
| **Saisie manuelle** | Création directe de documents avec métadonnées |
| **Indexation** | Indexation TF-IDF en temps réel avec barre de progression et journal |
| **Analyse** | Tableau de bord avec métriques, graphiques et distribution des documents |
| **Historique** | Consultation de toutes les recherches effectuées |
| **Export** | Export CSV ou JSON avec choix de l'emplacement de sauvegarde |
| **Sauvegarde** | Gestion complète des sauvegardes : création avec nom personnalisé, restauration, suppression |
| **Réinitialiser** | Vider la base de données et repartir à zéro pour des recherches personnelles |
| **À propos** | Informations sur l'équipe et les technologies utilisées |

---

## Aperçu de l'interface

### Windows (CustomTkinter)

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
│  🗑️ Réinit.  │                                            │
│  ℹ️ À propos │                                            │
│──────────────│  ← 1  2  3  →                              │
│ ● Opérationnel│                                            │
└──────────────┴────────────────────────────────────────────┘
```

### Android (Kivy)

```
┌─────────────────────────────────┐
│  🧭 Atlas                       │
│  Explorer l'histoire.           │
│─────────────────────────────────│
│  [Rechercher...        ] [🔍]   │
│─────────────────────────────────│
│  📚 Documents     📄 Passages   │
│       66              126       │
│─────────────────────────────────│
│  📋 Recherches    ⏱️ Temps moy. │
│       0               0 ms     │
│─────────────────────────────────│
│  [🔍 Recherche]  [🔬 Avancée]   │
│  [📊 Analyse]    [📋 Historique]│
│  [⚙️ Indexation] [💾 Sauvegarde]│
│  [📄 Importer]   [📤 Export]    │
│  [🗑️ Réinit.]    [ℹ️ À propos]  │
└─────────────────────────────────┘
```

---

## Installation

### Prérequis

- **Python 3.10** ou supérieur
- **pip** (gestionnaire de paquets)

### Windows

```bash
# 1. Cloner le dépôt
git clone https://github.com/Abdoul-Pro/Moteur-de-recherche.git
cd Moteur-de-recherche

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

### Android

```bash
# Via WSL (Windows Subsystem for Linux)
wsl --install -d Ubuntu
# Après redémarrage, dans Ubuntu :
sudo apt update && sudo apt install -y python3 python3-pip
pip3 install buildozer
buildozer android debug
```

Ou exécuter directement depuis Windows :
```batch
build_apk.bat
```

---

## Structure du projet

```
atlas/
├── main.py                          # Point d'entrée (détection Windows/Android)
├── config.py                        # Configuration centralisée (chemins, constantes)
│
├── core/                            # Logique métier (partagée)
│   ├── preprocessing.py             # Nettoyage, tokenisation, stemming (NLP)
│   ├── preprocessor.py              # Préprocesseur NLTK
│   ├── indexer.py                   # Indexation TF-IDF avec scikit-learn
│   └── engine.py                    # Moteur de recherche DB-based
│
├── database/                        # Couche d'accès aux données (partagée)
│   ├── connection.py                # Gestionnaire de connexion SQLite
│   └── database.py                  # Schéma SQL, CRUD et réinitialisation
│
├── utils/                           # Utilitaires (partagés)
│   └── datetime.py                  # Utilitaires de date/heure
│
├── windows/                         # Interface Windows (CustomTkinter)
│   ├── app.py                       # Application principale Windows
│   ├── theme.py                     # Thème et couleurs
│   ├── components/
│   │   ├── sidebar.py               # Barre latérale de navigation
│   │   └── widgets.py               # SearchBar, ResultCard, Pagination
│   └── pages/
│       ├── home.py                  # Page d'accueil
│       ├── search.py                # Page de résultats de recherche
│       ├── advanced.py              # Recherche avancée avec filtres
│       ├── analytics.py             # Tableau d'analyse
│       ├── history.py               # Historique des recherches
│       ├── indexing.py              # Page d'indexation
│       ├── import_doc.py            # Import de documents
│       ├── document.py              # Consultation d'un document
│       ├── sauvegarde.py            # Gestion des sauvegardes
│       ├── reset_db.py              # Réinitialisation de la base
│       └── about.py                 # Page À propos
│
├── android/                         # Interface Android (Kivy)
│   ├── main.py                      # Application principale Android
│   ├── theme.py                     # Thème et couleurs
│   └── screens/                     # Écrans Android
│
├── data/
│   ├── atlas.db                     # Base de données SQLite
│   ├── backups/                     # Sauvegardes de la base de données
│   └── index/                       # Sauvegarde de l'index TF-IDF
│
├── assets/                          # Ressources graphiques
│   └── icons/                       # Icônes
│
├── requirements.txt                 # Dépendances Windows
├── requirements-android.txt         # Dépendances Android
├── buildozer.spec                   # Configuration Buildozer (Android)
├── build_windows.bat                # Script de build Windows (.exe)
├── build_apk.bat                    # Script de build Android (.apk)
└── build_apk_wsl.sh                 # Script de build Android (WSL/Linux)
```

---

## Technologies

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.10+ | Langage principal |
| **CustomTkinter** | ≥5.2.0 | Interface graphique Windows (mode sombre) |
| **Kivy** | ≥2.2.0 | Interface graphique Android |
| **scikit-learn** | ≥1.3.0 | Vectorisation TF-IDF et similarité cosinus |
| **NLTK** | ≥3.8.0 | Tokenisation et stemming (Snowball) |
| **SQLite** | — | Base de données locale |
| **NumPy** | ≥1.24.0 | Calculs numériques |
| **PyPDF2** | ≥3.0.0 | Extraction de texte depuis PDF |
| **python-docx** | ≥0.8.11 | Extraction de texte depuis Word |

---

## Architecture

### Séparation des couches

L'architecture suit le principe de séparation des responsabilités :

```
┌─────────────────────────────────────────────────────────┐
│                    Interface Utilisateur                 │
│         windows/ (CustomTkinter)  │  android/ (Kivy)    │
├─────────────────────────────────────────────────────────┤
│                    Logique Métier                        │
│                    core/ (Partagé)                       │
│         preprocessing → preprocessor → engine            │
│                         indexer                          │
├─────────────────────────────────────────────────────────┤
│                    Accès aux Données                     │
│                    database/ (Partagé)                   │
│                    connection → database                 │
├─────────────────────────────────────────────────────────┤
│                    Utilitaires                           │
│                    utils/ (Partagé)                      │
│                    datetime                              │
└─────────────────────────────────────────────────────────┘
```

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

### Sauvegarde

1. Naviguer vers **Sauvegarde**
2. Saisir un nom pour identifier la sauvegarde
3. Cliquer sur **Sauvegarder**
4. Pour restaurer : cliquer sur **Restaurer** à côté de la sauvegarde souhaitée
5. Pour supprimer : cliquer sur **Supprimer** à côté de la sauvegarde

### Réinitialisation de la base de données

Pour repartir à zéro avec vos propres documents :

1. Naviguer vers **Réinitialiser**
2. Voir l'état actuel (nombre de documents, passages, termes)
3. Choisir une option :
   - **Réinitialiser tout** — Supprime documents, index, vocabulaire et historique
   - **Supprimer les documents** — Supprime documents et index, conserve l'historique
4. Confirmer l'action
5. Importer vos propres documents via **Ajouter un document**

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

Mesure l'angle entre le vecteur de la requête et chaque vecteur document. Le score varie de **0** (aucune similarité) à **1** (identique).

```
similarité = (A · B) / (‖A‖ × ‖B‖)
```

### Découpage en passages (Chunking)

Les documents sont découpés en passages de **500 mots** avec un chevauchement de **50 mots** pour maintenir le contexte entre les segments.

### Gestion multiplateforme

La configuration centralisée dans `config.py` gère automatiquement les chemins selon la plateforme :

- **Windows/Linux/macOS** : Chemins basés sur `Path(__file__).parent`
- **Android** : Chemins basés sur `android.storage.app_storage_path()`

---

## Build

### Windows (.exe)

```batch
build_windows.bat
```

L'exécutable sera généré dans `dist/Atlas.exe`.

### Android (.apk)

```bash
# Via WSL
wsl -d Ubuntu -- bash -c "cd ~/atlas_build && ~/.local/bin/buildozer android debug"
```

Ou directement depuis Windows :
```batch
build_apk.bat
```

L'APK sera généré dans `bin/atlas-debug.apk`.

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
