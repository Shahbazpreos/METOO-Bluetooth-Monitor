# METOO Bluetooth Monitor

A lightweight Windows system-tray utility that monitors the Bluetooth connection state of a METOO BT5.0 mouse.

**Dev: Shabbi**

> **Important:** This project monitors Bluetooth connection status. It does **not** read or estimate the mouse's battery percentage. The tested mouse did not expose a standard Bluetooth Battery Service / Battery Level characteristic.

## Features

- Windows 10/11 system-tray application
- Green tray icon when the mouse is connected
- Red tray icon when the mouse is disconnected or unavailable
- Windows notifications for disconnect/reconnect events
- Optional **Start with Windows** setting
- No administrator privileges required for normal use
- Local operation; no account, cloud service, or network connection required

## Device support

The initial configuration targets the following tested device:

- Display name: `BT5.0 Mouse`
- Bluetooth address: `E2:07:5E:F8:69:A1`
- Manufacturer string: `BEKEN`
- Software revision: `5.3.5.6`

Other METOO models may use different names, Bluetooth identifiers, or connection behavior. The app may need configuration changes for those devices.

## Requirements for running from source

- Windows 10 or Windows 11
- Python 3.12 (tested with Python 3.12.10)
- Bluetooth enabled and the mouse paired in Windows

## Run from source

Open PowerShell in the project folder:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

The application runs in the notification area/system tray. Use the tray icon's context menu to view status, enable startup, or quit.

## Build the standalone EXE

Run:

```powershell
.\build.bat
```

The executable will be created at:

```text
dist\METOO-Bluetooth-Monitor.exe
```

The EXE is built for Windows. It is not a macOS or Linux application.

## Windows startup

Choose **Start with Windows** from the tray menu. This creates or removes an entry under the current Windows user's `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` registry key. It does not require administrator privileges.

## Logs

Runtime logs are stored at:

```text
%LOCALAPPDATA%\METOO-Battery-Monitor\logs\app.log
```

## Troubleshooting

### The mouse is not found

1. Make sure Bluetooth is enabled.
2. Pair the mouse in Windows Settings.
3. Check that Windows shows the device as `BT5.0 Mouse`.
4. Restart the application.

### The tray icon remains red

The initial connection-state mapping was verified against one physical mouse using its observed WinRT status values. Different firmware or device variants may report different values. Check the device configuration and report the model/firmware and log output in an issue.

### Windows warns about the EXE

A newly built, unsigned executable may trigger Microsoft Defender SmartScreen or antivirus reputation warnings. Only download releases from the official repository, inspect the source, and publish checksums. Code signing can reduce warnings but requires a signing certificate.

## Privacy

The application checks the paired Bluetooth device locally through Windows Bluetooth APIs. It does not transmit device information to a server. Logs are stored locally on the PC.

## Third-party components

This project uses third-party Python packages listed in `requirements.txt`. Those packages retain their own licenses. Review their license terms before redistributing a bundled executable.

## Contributing

Bug reports and pull requests are welcome. Please include your Windows version, Python version (if running from source), mouse model, and relevant log excerpts. Do not include personal information in logs.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
