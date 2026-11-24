; Inno Setup script for Lazer Shark Kill! Kill!
; build_windows_installer.py compiles this after PyInstaller has filled dist\LazerSharkKillKill,
; passing the version with /DMyAppVersion=x.y.z

#ifndef MyAppVersion
  #define MyAppVersion "3.0.0"
#endif
#define MyAppName "Lazer Shark Kill! Kill!"
#define MyAppPublisher "wheidal"
#define MyAppURL "https://github.com/wheidal/LazerShark"
#define MyAppExeName "LazerSharkKillKill.exe"

[Setup]
; Keep this AppId: Windows uses it to recognise an upgrade of an earlier install
AppId={{A8B3C4D5-E6F7-4A5B-9C3D-2E1F0A9B8C7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\LazerSharkKillKill
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=LazerSharkKillKill_Setup_v{#MyAppVersion}
SetupIconFile=assets\shark_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Settings and high scores live in %APPDATA%, so no admin rights are needed.
; The player can still choose an install for everyone.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\LazerSharkKillKill\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Readme"; Filename: "{app}\README.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
