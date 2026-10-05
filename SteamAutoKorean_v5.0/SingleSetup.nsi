Unicode true
Name "Steam Auto Korean"
OutFile "SteamAutoKorean_Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\SteamAutoKorean"
RequestExecutionLevel user
Icon "app.ico"
Page directory
Page instfiles
Section "Steam Auto Korean"
 SetOutPath "$INSTDIR"
 File /r "dist\SteamAutoKorean\*"
 CreateShortcut "$DESKTOP\Steam Auto Korean.lnk" "$INSTDIR\SteamAutoKorean.exe" "" "$INSTDIR\SteamAutoKorean.exe" 0
 CreateDirectory "$SMPROGRAMS\Steam Auto Korean"
 CreateShortcut "$SMPROGRAMS\Steam Auto Korean\Steam Auto Korean.lnk" "$INSTDIR\SteamAutoKorean.exe" "" "$INSTDIR\SteamAutoKorean.exe" 0
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SteamAutoKorean" "DisplayName" "Steam Auto Korean"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SteamAutoKorean" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SteamAutoKorean" "DisplayVersion" "4.9"
SectionEnd
Section -Run
 Exec "$INSTDIR\SteamAutoKorean.exe"
SectionEnd
Section "Uninstall"
 Delete "$DESKTOP\Steam Auto Korean.lnk"
 Delete "$SMPROGRAMS\Steam Auto Korean\Steam Auto Korean.lnk"
 RMDir "$SMPROGRAMS\Steam Auto Korean"
 RMDir /r "$INSTDIR"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SteamAutoKorean"
SectionEnd
