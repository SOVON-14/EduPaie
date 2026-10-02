#define MyAppName "EduPaie"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "EduPaie"
#define MyAppExeName "EduPaie.exe"

[Setup]
AppId={{7D132B02-645A-447B-B4A9-27CBE310D787}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=..\dist
OutputBaseFilename=EduPaie-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le bureau"; GroupDescription: "Raccourcis supplémentaires :"; Flags: unchecked

[Files]
Source: "..\dist\EduPaie\*"; DestDir: "{app}"; Excludes: "_internal\data\edupaie.db"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\EduPaie\_internal\data\edupaie.db"; DestDir: "{app}\_internal\data"; Flags: onlyifdoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer EduPaie"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent