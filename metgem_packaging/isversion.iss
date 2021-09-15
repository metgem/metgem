// -- IsVersion.iss --
// Include file with support functions for version check
//

[CustomMessages]
english.UninstallOldVersion=Version %1 of {#AppName} is already installed. Would you like to uninstall it before?
french.UninstallOldVersion=La version %1 de {#AppName} est déjà  installée. Voulez-vous la désinstaller ?
english.AlreadyInstalled=Version %1 of {#AppName} is already installed. Would you like to continue installation?
french.AlreadyInstalled=La version %1 de {#AppName} est déjà  installée. Voulez-vous poursuivre l'installation ?
english.UninstallFailed=Failed to uninstall {#AppName} version %1. Please restart Windows and run setup again.
french.UninstallFailed=Impossible de désinstaller {#AppName} version %1. Merci de redémarrer Windows et de relancer l'installation.

[Code]
function GetNumber(var temp: String): Integer;
var
  part: String;
  pos1: Integer;
begin
  if Length(temp) = 0 then
  begin
    Result := -1;
    Exit;
  end;
    pos1 := Pos('.', temp);
    if (pos1 = 0) then
    begin
      Result := StrToInt(temp);
    temp := '';
    end
    else
    begin
    part := Copy(temp, 1, pos1 - 1);
      temp := Copy(temp, pos1 + 1, Length(temp));
      Result := StrToInt(part);
    end;
end;

function CompareInner(var temp1, temp2: String): Integer;
var
  num1, num2: Integer;
begin
    num1 := GetNumber(temp1);
  num2 := GetNumber(temp2);
  if (num1 = -1) or (num2 = -1) then
  begin
    Result := 0;
    Exit;
  end;
      if (num1 > num2) then
      begin
        Result := 1;
      end
      else if (num1 < num2) then
      begin
        Result := -1;
      end
      else
      begin
        Result := CompareInner(temp1, temp2);
      end;
end;

function CompareVersion(str1, str2: String): Integer;
var
  temp1, temp2: String;
begin
    temp1 := str1;
    temp2 := str2;
    Result := CompareInner(temp1, temp2);
end;

function InitializeSetup(): Boolean;
var
  oldVersion: String;
  uninstaller: String;
  ErrorCode: Integer;
begin
  if IsPortable() then
  begin
    Result := True;
  end
  else
  begin
    if RegKeyExists(HKEY_LOCAL_MACHINE,
      'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1') then
    begin
      RegQueryStringValue(HKEY_LOCAL_MACHINE,
        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1',
        'DisplayVersion', oldVersion);
      if (CompareVersion(oldVersion, '{#AppVersion}') < 0) then
      begin
        if MsgBox(FmtMessage(CustomMessage('UninstallOldVersion'), [oldVersion]), mbConfirmation, MB_YESNO) = IDYES then
        begin
            RegQueryStringValue(HKEY_LOCAL_MACHINE,
              'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppID}_is1',
              'UninstallString', uninstaller);
            ShellExec('runas', uninstaller, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
            if (ErrorCode <> 0) then
            begin
              MsgBox(CustomMessage('UninstallFailed}'), mbError, MB_OK );
              Result := False;
            end
            else
            begin
              Result := True;
            end;
        end
        else
        begin
          Result := True;
        end;
      end
      else
      begin
        if MsgBox(FmtMessage(CustomMessage('AlreadyInstalled'), [oldVersion]), mbInformation, MB_YESNO) = IDNO then
        begin
          Result := False;
        end
        else
        begin
          Result := True;
        end;
      end;
    end
    else
    begin
      Result := True;
    end;
  end;
end;