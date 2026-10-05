@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo Steam Auto Korean - Windows 11 Release Builder
echo ================================================
where py >nul 2>nul || (echo Python 3.11+ 설치가 필요합니다.& pause & exit /b 1)
py -m venv .buildvenv
call .buildvenv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo [1/3] 무설치 EXE 빌드...
pyinstaller --noconfirm --clean --windowed --name SteamAutoKorean --collect-all pytesseract --collect-all PIL app.py
if errorlevel 1 goto :fail

echo [2/3] 무설치 ZIP 생성...
powershell -NoProfile -Command "Compress-Archive -Force -Path '.\dist\SteamAutoKorean\*' -DestinationPath '.\SteamAutoKorean_Windows11_Portable.zip'"

echo [3/3] 설치형 EXE 준비...
where makensis >nul 2>nul
if errorlevel 1 (
 echo NSIS가 없어 설치형 EXE는 아직 생성하지 못했습니다.
 echo https://nsis.sourceforge.io/ 에서 NSIS 설치 후 이 BAT를 다시 실행하세요.
) else (
 makensis installer.nsi
)
echo.
echo 완료:
echo - SteamAutoKorean_Windows11_Portable.zip
echo - SteamAutoKorean_Windows11_Setup.exe ^(NSIS 설치 시^)
pause
exit /b 0
:fail
echo 빌드 실패. 위 오류를 확인하세요.
pause
exit /b 1
