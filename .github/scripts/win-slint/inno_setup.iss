; Inno Setup script for the Slint-UI build of PyGlossary.
; Copy of .github/scripts/win/inno_setup.iss with its own AppId, app name,
; exe name and output filename prefix so it can be installed side-by-side
; with the Tk build without colliding with it (different install dir,
; different registry AppId, different Start Menu / Desktop entries).
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#ifndef MyAppName
#define MyAppName "PyGlossary (Slint)"
#endif
;#define MyAppVersion "5.1.0" <<< MUST pass /DMyAppVersion=1235 as cli arg
;#define SourceFilesGlob "dir1\*" <<< MUST pass /DSourceFilesGlob="dir1\*" as cli arg
#define MyAppPublisher "github.com/ilius/pyglossary"
#define MyAppURL "https://github.com/ilius/pyglossary"
#ifndef MyAppExeName
#define MyAppExeName "PyGlossarySlint.exe"
#endif
#ifndef OutputBaseFilenamePrefix
#define OutputBaseFilenamePrefix "PyGlossarySlint"
#endif
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".dsl"
#define MyAppAssocExt ".bgl"
#define MyAppAssocExt ".dz"
#define MyAppAssocExt ".mdx"

#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: distinct AppId from the Tk build's installer, so both can be
; installed side-by-side without one uninstalling the other.
AppId={{9C7E5C39-6B0B-4B12-9C7D-2C2C9E2F6B31}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
; "ArchitecturesAllowed=x64compatible" specifies that Setup cannot run
; on anything but x64 and Windows 11 on Arm.
ArchitecturesAllowed=x64compatible
; "ArchitecturesInstallIn64BitMode=x64compatible" requests that the
; install be done in "64-bit mode" on x64 or Windows 11 on Arm,
; meaning it should use the native 64-bit Program Files directory and
; the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; #### defined via cli arg as /DLicenseFile="/path/to/license.txt"
LicenseFile={#LicenseFile}
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename={#OutputBaseFilenamePrefix}-{#MyAppVersion}-Windows-x64-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]

Source: "{#SourceFilesGlob}"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".dsl"; ValueData: ""

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
