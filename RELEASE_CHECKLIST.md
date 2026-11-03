# GitHub Release Checklist

## Before publishing

- [ ] Test connect/disconnect detection several times.
- [ ] Test after restarting Windows.
- [ ] Test Start with Windows on and off.
- [ ] Test notifications.
- [ ] Confirm the app exits cleanly.
- [ ] Build the EXE on Windows using `build.bat`.
- [ ] Test the EXE on a machine/user account without Python installed, if possible.
- [ ] Scan the EXE with Microsoft Defender.
- [ ] Review third-party dependency licenses.
- [ ] Add screenshots to `docs/screenshots/` and update README.
- [ ] Confirm README accurately says connection monitor, not battery percentage.

## GitHub repository

Suggested repository name: `METOO-Bluetooth-Monitor`

Suggested description:
"Lightweight Windows system-tray utility for monitoring a METOO Bluetooth mouse connection."

Suggested topics:
`windows`, `bluetooth`, `python`, `system-tray`, `pyinstaller`, `metoo-mouse`

## First push

```powershell
git init
git add .
git commit -m "Initial release: METOO Bluetooth Monitor"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/METOO-Bluetooth-Monitor.git
git push -u origin main
```

## Publish the EXE as a GitHub Release

1. Build the EXE with `build.bat`.
2. Open the repository on GitHub.
3. Select **Releases** → **Draft a new release**.
4. Create tag `v0.1.0`.
5. Use release title `METOO Bluetooth Monitor v0.1.0`.
6. Upload `dist/METOO-Bluetooth-Monitor.exe` as a release asset.
7. Include release notes describing supported device and limitations.
8. Publish the release.

Recommended: also publish a SHA-256 checksum for the EXE:

```powershell
Get-FileHash .\dist\METOO-Bluetooth-Monitor.exe -Algorithm SHA256
```

Copy the resulting hash into the release notes.

## Important

Do not commit large build folders, virtual environments, logs, or temporary files. Keep the EXE attached to the GitHub Release rather than committing it to the source tree.
