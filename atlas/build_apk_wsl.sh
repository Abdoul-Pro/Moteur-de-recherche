#!/bin/bash
# ── Build Android APK via WSL/Linux ────────────────────────────────
# Lance la construction de l'APK Android.
# Prérequis : Python 3, pip, buildozer installé.

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Atlas — Build Android APK"
echo "════════════════════════════════════════════════════════════════"
echo

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: python3 non trouvé. Installez Python 3."
    exit 1
fi

# Vérifier buildozer
if ! command -v buildozer &> /dev/null; then
    echo "Installation de buildozer..."
    python3 -m pip install --upgrade buildozer
fi

# Nettoyer les builds précédents
buildozer clean 2>/dev/null || true

# Construire l'APK
echo "Construction de l'APK..."
buildozer android debug

if [ $? -eq 0 ]; then
    echo
    echo "════════════════════════════════════════════════════════════════"
    echo "  BUILD RÉUSSI — APK dans bin/"
    echo "════════════════════════════════════════════════════════════════"
    ls -la bin/*.apk 2>/dev/null
else
    echo
    echo "════════════════════════════════════════════════════════════════"
    echo "  ÉCHEC DU BUILD — Vérifiez les logs ci-dessus"
    echo "════════════════════════════════════════════════════════════════"
    exit 1
fi
