[app]

# Titre de l'application
title = Atlas

# Nom du package
package.name = atlas

# Nom du package Android
package.domain = org.atlas

# Source du code
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Version
version = 1.0.0

# Dépendances
requirements = python3,
    kivy,
    kivy-garden,
    plyer,
    scikit-learn,
    numpy,
    nltk,
    PyPDF2,
    python-docx,
    sqlite3

# Fichiers à inclure
source.include_patterns = assets/*,data/*

# Répertoires à exclure
source.exclude_patterns = src/*,windows/*

# Permissions Android
android.permissions = READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    INTERNET

# SDK cible
android.api = 33
android.minapi = 21
android.ndk = 25b

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# activité principale
android.entrypoint = main.py

# Label
android.label = Atlas

# Icône de l'application (512x512 PNG, sans texte, boussole seule)
icon.filename = %(source.dir)s/assets/icons/icon.png

# Splash screen (1080x1920 PNG, boussole + Atlas + tagline)
presplash.filename = %(source.dir)s/assets/icons/splash.png

# Arrière-plan (couleur derrière le splash screen)
android.background = #0a1628

# Thème
android.theme = Material

# Gradle
android.gradle_args = -PdependencyCacheEnabled=false

# Build
android.arch = arm64-v8a

# Logs
log_level = 2

# Mode de débogage
p4a.bootstrap = sdl2

# Build optimisé
android.enable_optimizations = true

# Compresser l'APK
android.enable_compression = true
