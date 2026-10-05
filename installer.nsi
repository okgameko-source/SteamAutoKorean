Unicode true
Name "Steam Auto Korean"
OutFile "SteamAutoKorean_Windows11_Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\SteamAutoKorean"
RequestExecutionLevel user
Icon "app.ico"
Page directory
Page instfiles
Section "Install"
 SetOutPath "$INSTDIR"
 File /r "dist\SteamAutoKorean\*"
 CreateShortcut "$DESKTOP\Steam Auto Korean.lnk" "$INSTDIR\SteamAutoKorean.exe" "" "$INSTDIR\SteamAutoKorean.exe" 0
 CreateDirectory "$SMPROGRAMS\Steam Auto Korean"
 CreateShortcut "$SMPROGRAMS\Steam Auto Korean\Steam Auto Korean.lnk" "$INSTDIR\SteamAutoKorean.exe" "" "$INSTDIR\SteamAutoKorean.exe" 0
 WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd
Section -Post
 Exec "$INSTDIR\SteamAutoKorean.exe"
SectionEnd
Section "Uninstall"
 Delete "$DESKTOP\Steam Auto Korean.lnk"
 Delete "$SMPROGRAMS\Steam Auto Korean\Steam Auto Korean.lnk"
 RMDir "$SMPROGRAMS\Steam Auto Korean"
 RMDir /r "$INSTDIR"
SectionEnd
