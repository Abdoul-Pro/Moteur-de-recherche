@echo off
REM ── Build Android APK via WSL ──────────────────────────────────────
REM Lance la construction de l'APK Android via WSL (Windows Subsystem for Linux).
REM Prérequis : WSL installé avec Ubuntu et buildozer configuré.

echo ════════════════════════════════════════════════════════════════
echo   Atlas — Build Android APK
echo ════════════════════════════════════════════════════════════════
echo.

wsl -d Ubuntu -- bash -c "cd ~ && git clone https://github.com/Abdoul-Pro/Moteur-de-recherche.git 2>/dev/null; cd Moteur-de-recherche && python3 -m pip install --upgrade buildozer 2>/dev/null && buildozer android debug"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo   BUILD REUSSI — APK dans bin/
    echo ════════════════════════════════════════════════════════════════
) else (
    echo.
    echo ════════════════════════════════════════════════════════════════
    echo   ECHEC DU BUILD — Verifiez les logs ci-dessus
    echo ════════════════════════════════════════════════════════════════
)

pause
