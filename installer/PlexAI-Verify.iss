#define MyAppName "PlexAI Verify"
#define MyAppVersion "10.0.0"
#define MyAppExeName "PlexAI-Verify.exe"

[Setup]
AppId={{8BFEF2CE-BF98-4B3D-9D01-9EA11F0DC777}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\PlexAI Verify
DefaultGroupName=PlexAI Verify
OutputDir=output
OutputBaseFilename=PlexAI-Verify-Setup-v10.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "..\dist\PlexAI-Verify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PlexAI Verify"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PlexAI Verify"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer PlexAI Verify"; Flags: nowait postinstall skipifsilent
