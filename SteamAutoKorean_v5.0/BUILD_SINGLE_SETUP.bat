@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Steam Auto Korean - Single Setup Builder
echo [1/4] 앱 빌드
py -m venv .build
call .build\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --icon app.ico --name SteamAutoKorean app.py
if errorlevel 1 goto FAIL

echo [2/4] OCR 런타임 확인
if not exist tesseract\tesseract.exe (
 echo tesseract 폴더에 Windows Tesseract portable 파일을 넣어야 합니다.
 echo 필요한 tessdata 언어팩도 tesseract\tessdata 폴더에 넣으세요.
 pause
 exit /b 1
)
xcopy /E /I /Y tesseract dist\SteamAutoKorean\tesseract >nul

echo [3/4] 설치 프로그램 생성
where makensis >nul 2>nul || (
 echo 빌드 PC에 NSIS가 필요합니다. 최종 사용자 PC에는 필요하지 않습니다.
 pause
 exit /b 1
)
makensis SingleSetup.nsi
if errorlevel 1 goto FAIL

echo [4/4] 완료
echo SteamAutoKorean_Setup.exe
explorer /select,"%CD%\SteamAutoKorean_Setup.exe"
pause
exit /b 0
:FAIL
echo 빌드 실패
pause
exit /b 1
