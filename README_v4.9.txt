Steam Auto Korean v4.9 — Upgrade Safety
- User writable data is stored under %LOCALAPPDATA%\SteamAutoKorean\data
- Program binaries remain under %LOCALAPPDATA%\Programs\SteamAutoKorean
- Reinstall/upgrade does not overwrite user glossary/learned/profile data
- Uninstall removes program binaries but intentionally preserves user localization data
- GitHub Windows QA creates a sentinel user-data file, reinstalls Setup.exe, verifies the file,
  launches the upgraded app, then uninstalls and verifies user data still remains.
