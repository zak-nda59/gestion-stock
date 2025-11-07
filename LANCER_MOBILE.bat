@echo off
title Boutique Mobile - Acces Telephone
color 0B

echo ==========================================
echo   BOUTIQUE MOBILE - ACCES TELEPHONE
echo ==========================================
echo.
echo Configuration pour acces mobile...
echo.

REM Aller dans le repertoire du script
cd /d "%~dp0"

REM Afficher l'IP locale
echo Recherche de votre adresse IP...
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%j in ("%%i") do (
        echo.
        echo ========================================
        echo   ADRESSE IP TROUVEE: %%j
        echo ========================================
        echo.
        echo 📱 SUR VOTRE TELEPHONE :
        echo    1. Connectez-vous au meme WiFi
        echo    2. Ouvrez votre navigateur
        echo    3. Tapez: http://%%j:5000
        echo.
        echo ========================================
        echo.
        set IP_ADDRESS=%%j
        goto :found_ip
    )
)

:found_ip
echo Demarrage du serveur accessible mobile...
echo.
echo IMPORTANT: Laissez cette fenetre ouverte
echo Pour arreter: Ctrl+C
echo.

REM Lancer l'application
python app_minimal.py

pause
