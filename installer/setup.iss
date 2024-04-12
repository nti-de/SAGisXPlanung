#define MyAppName "SAGis XPlanung"
#define MyAppPublisher "NTI Deutschland GmbH"
#define MyAppURL "https://www.nti-group.com/de/produkte/sagis-loesungen/"

#ifndef SAGIS_VERSION
  #define SAGIS_VERSION "2.4.0-dev"
#endif

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{48626255-FF2B-4145-BDB7-B1A76C2F0D46}
AppName={#MyAppName}
AppVersion={#SAGIS_VERSION}
;AppVerName={#MyAppName} {#SAGIS_VERSION}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={userappdata}\QGIS\QGIS3\profiles\default\python\plugins\SAGisXPlanung
#ifndef WITH_CIVIL_IMPORT
  #define WITH_CIVIL_IMPORT False
  OutputBaseFilename={#MyAppName}_{#SAGIS_VERSION}
#else
  #define WITH_CIVIL_IMPORT True
  OutputBaseFilename={#MyAppName}_{#SAGIS_VERSION}_c3d
#endif

DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
DisableWelcomePage=no
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardSmallImageFile=sagis_icon.bmp
SetupIconFile=sagis_icon.ico

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "SAGisXPlanung\*"; DestDir: "{app}"; Check: CheckWithCivilImport; Flags: recursesubdirs
Source: "dependencies\*"; DestDir: "{app}\dependencies"; Flags: recursesubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

; removes potential "XPlanung" folder from installations of older versions
; removes python dependency files after installation
[InstallDelete]
Type: filesandordirs; Name: "{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\XPlanung"
Type: filesandordirs; Name: "{userappdata}\QGIS\QGIS3\profiles\default\python\plugins\SAGisXPlanung\dependencies"

[Run]
Filename: "cmd.exe"; Parameters: "/C ""OSGeo4W.bat o4w_env & python3 -m ensurepip --upgrade"""; WorkingDir: "{code:GetDir|0}"; StatusMsg: Python Paketmanager (pip) installieren...; Flags: runhidden waituntilterminated; BeforeInstall: SetMarqueeProgress(True)
Filename: "cmd.exe"; Parameters: "/C ""OSGeo4W.bat o4w_env & for %x in ({app}\dependencies\*.whl) do python3 -m pip install %x"""; WorkingDir: "{code:GetDir|0}"; StatusMsg: Python Abhängigkeiten installieren...; Flags: runhidden waituntilterminated; AfterInstall: SetMarqueeProgress(False)
Filename: "cmd.exe"; Parameters: "/C ""OSGeo4W.bat o4w_env & (qgis || qgis-ltr)"""; WorkingDir: "{code:GetDir|0}"; Description: QGIS starten; Flags: runhidden nowait postinstall skipifsilent

[Code]
var
  Page: TInputDirWizardPage;
  FilePath: string;

procedure SetMarqueeProgress(Marquee: Boolean);
begin
  if Marquee then
  begin
    WizardForm.ProgressGauge.Style := npbstMarquee;
  end
    else
  begin
    WizardForm.ProgressGauge.Style := npbstNormal;
  end;
end;

function GetDir(Param: string): string;
begin
  Result := Page.Values[StrToInt(Param)];
end;

procedure InitializeWizard;
begin
  Page := CreateInputDirPage(wpWelcome,
    'QGIS Installationsordner wählen', 'Bitte wählen sie den Installationsordner von QGIS auf diesem Rechner',
    'Der Installer benötigt diese Angabe um SAGis XPlanung korrekt zu installieren.' + #13#10 +
      'Typische Orte der Installation sind C:\OSGeo4W\ oder C:\Program Files\QGIS 3.*',
    False, 'New Folder');

  Page.Add('QGIS Ordner');

  Page.Values[0] := ('C:\OSGeo4W');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = Page.ID then
  begin
    FilePath := Page.Values[0] + '\OSGeo4W.bat'
    if not FileExists(FilePath) then
    begin
      MsgBox('Installer konnte Teile der QGIS-Installation nicht finden. Überprüfen Sie den angegebenen Ordner.', mbError, MB_OK);
      Result := False;
    end;

  end;
end;

function CheckWithCivilImport: Boolean;
begin
  if ({#WITH_CIVIL_IMPORT} = 0) and (ExtractFileName(CurrentFileName) = 'import_civil.py') then
  begin
    Result := False
  end
  else 
  begin
    Result := True;
  end;
end;
