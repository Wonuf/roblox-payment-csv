@echo off
REM Builds dist\RobloxPayoutCSV.exe (single file, no Python needed to run it).
python -m pip install --upgrade pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --onefile --name RobloxPayoutCSV --add-data "index.html;." app.py || exit /b 1
echo.
echo Built dist\RobloxPayoutCSV.exe
