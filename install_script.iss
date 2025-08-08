[Setup]
AppName=PLC Video Controller
AppVersion=1.0
DefaultDirName={pf}\PLCVideoController
DefaultGroupName=PLC Video Controller
OutputBaseFilename=PLCVideoControllerInstaller
Compression=lzma
SolidCompression=yes
SetupIconFile="icon.ico"
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\PLCVideoController.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "python-3.10.11-amd64.exe"; DestDir: "{tmp}"; Flags: ignoreversion
Source: "prereq_installer.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PLC Video Controller"; Filename: "{app}\PLCVideoController.exe"
Name: "{commondesktop}\PLC Video Controller"; Filename: "{app}\PLCVideoController.exe"; Tasks: desktopicon

[Run]
Filename: "{tmp}\python-3.10.11-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"; Check: NeedsPython; Flags: waituntilterminated
Filename: "{cmd}"; Parameters: "/C prereq_installer.bat"; WorkingDir: "{app}"; Flags: runhidden waituntilterminated
Filename: "{app}\PLCVideoController.exe"; Description: "Launch application"; Flags: nowait postinstall skipifsilent

[Code]
function NeedsPython(): Boolean;
var
  ResultCode: Integer;
begin
  Result := (not Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode));
end;
