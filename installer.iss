
#define MyAppName "METOO Bluetooth Monitor"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Shabbi"
#define MyAppURL "https://github.com/Shahbazpreos"
#define MyAppExeName "METOO-Bluetooth-Monitor.exe"

[Setup]
AppId={{9D62343E-9DA3-4A3A-B07D-782C44CFA3BB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern dark
DisableProgramGroupPage=yes
SetupLogging=yes
CloseApplications=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=dist
OutputBaseFilename=METOO-Bluetooth-Monitor-Setup
Compression=lzma2
SolidCompression=yes
LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\METOO-Bluetooth-Monitor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM METOO-Bluetooth-Monitor.exe /T"; Flags: runhidden; RunOnceId: "StopMETOO"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\METOO-Battery-Monitor"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch METOO Bluetooth Monitor"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    RegDeleteValue(
      HKEY_CURRENT_USER,
      'Software\Microsoft\Windows\CurrentVersion\Run',
      'METOOBluetoothMonitor'
    );
  end;
end;
