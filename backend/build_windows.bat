@echo off
echo ==========================================
echo DONG GOI UNG DUNG KIEM TOAN CAU
echo ==========================================
echo Dang cai dat thu vien PyInstaller...
pip install pyinstaller

echo Tien hanh bien dich API Server sang file EXE doc lap...
pyinstaller --name "BridgeAuditor_Backend" --onefile --log-level=WARN main.py

echo.
echo ==========================================
echo Thanh cong! Ung dung .exe da duoc dat tai thu muc /dist/
echo Ban co the chay truc tiep BridgeAuditor_Backend.exe ma khong can cai Python.
pause
