[Setup]
AppId={{E4859E81-680C-4BB9-9ABC-8E5F45E87F43}
AppName=CrackeCraft
AppVersion=0.1.0
DefaultDirName={autopf}\CrackeCraft
DefaultGroupName=CrackeCraft
OutputDir=dist\installer
OutputBaseFilename=CrackeCraft-Setup
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\CrackeCraft\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CrackeCraft"; Filename: "{app}\CrackeCraft.exe"
Name: "{autodesktop}\CrackeCraft"; Filename: "{app}\CrackeCraft.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\CrackeCraft.exe"; Description: "Abrir CrackeCraft"; Flags: postinstall nowait skipifsilent
