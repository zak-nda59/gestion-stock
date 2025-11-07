@echo off
title Boutique Mobile - Lanceur
color 0A

echo ========================================
echo    BOUTIQUE MOBILE - LANCEUR AUTO
echo ========================================
echo.
echo Demarrage de l'application...
echo.

REM Aller dans le repertoire du script
cd /d "%~dp0"

REM Lancer avec Python
python launcher.py

REM Si Python n'est pas trouve, essayer py
if errorlevel 1 (
    echo.
    echo Tentative avec py...
    py launcher.py
)

REM Si toujours pas trouve, essayer python3
if errorlevel 1 (
    echo.
    echo Tentative avec python3...
    python3 launcher.py
)

REM Si rien ne marche
if errorlevel 1 (
    echo.
    echo ERREUR: Python n'est pas installe ou introuvable
    echo.
    echo Veuillez installer Python depuis: https://python.org
    echo.
    pause
)

pause
