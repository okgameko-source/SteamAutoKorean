@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul || (echo Python 3.11+ 필요&pause&exit /b 1)
py -m venv .buildvenv
call .buildvenv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --icon app.ico --name SteamAutoKorean app.py
if errorlevel 1 goto fail
where makensis >nul 2>nul || (echo NSIS를 설치한 후 다시 실행하세요.&pause&exit /b 1)
makensis installer.nsi
if errorlevel 1 goto fail
echo 생성 완료: SteamAutoKorean_Windows11_Setup.exe
pause
exit /b 0
:fail
echo 빌드 실패
pause
exit /b 1
