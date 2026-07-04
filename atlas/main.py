"""
main.py — Point d'entrée principal de l'application Atlas.

Détecte automatiquement la plateforme et lance l'interface appropriée :
- Windows/Linux/macOS : Interface CustomTkinter
- Android : Interface Kivy
"""

import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def is_android() -> bool:
    """Détecte si l'application tourne sur Android."""
    return sys.platform == "android"


def main():
    """Point d'entrée principal."""
    if is_android():
        # Lancement de l'interface Android (Kivy)
        from android.main import AtlasAndroidApp
        AtlasAndroidApp().run()
    else:
        # Lancement de l'interface Windows (CustomTkinter)
        from windows.app import AtlasApp
        app = AtlasApp()
        app.mainloop()


if __name__ == "__main__":
    main()
