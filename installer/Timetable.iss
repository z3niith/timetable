#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6E1D2C54-8B7A-4F3E-9C41-5A0B7D2E8F13}
AppName=Timetable
AppVersion={#AppVersion}
AppPublisher=z3niith
AppPublisherURL=https://github.com/z3niith/timetable
AppSupportURL=https://github.com/z3niith/timetable/issues
DefaultDirName={autopf}\Timetable
DefaultGroupName=Timetable
DisableProgramGroupPage=yes
; Per-user install: no admin prompt, and winget treats it as user scope.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=Timetable-Setup-{#AppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\Timetable.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\Timetable\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Timetable"; Filename: "{app}\Timetable.exe"
Name: "{autodesktop}\Timetable"; Filename: "{app}\Timetable.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Timetable.exe"; Description: "Launch Timetable"; Flags: nowait postinstall skipifsilent
