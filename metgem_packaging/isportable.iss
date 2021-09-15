// -- IsPortable.iss --
// Include file with support functions for portable mode
//

[Messages]
HelpTextNote=/PORTABLE=1%nEnable portable mode.

[Code]
function CreateFile(
    lpFileName             : String;
    dwDesiredAccess        : Cardinal;
    dwShareMode            : Cardinal;
    lpSecurityAttributes   : Cardinal;
    dwCreationDisposition  : Cardinal;
    dwFlagsAndAttributes   : Cardinal;
    hTemplateFile          : Integer
): THandle;
external 'CreateFileW@kernel32.dll stdcall';

function CloseHandle(hHandle: THandle): BOOL;
external 'CloseHandle@kernel32.dll stdcall';

const
  { Win32 constants }
  GENERIC_READ         = $80000000;
  GENERIC_WRITE        = $40000000;
  OPEN_EXISTING        = 3;
  INVALID_HANDLE_VALUE = -1;
  CREATE_NEW           = 1;
  //FILE_ATTRIBUTE_TEMPORARY = $100;
  FILE_FLAG_DELETE_ON_CLOSE = $4000000;

function IsDirectoryWriteable(const AName: string): Boolean; 
var 
  FileName: String; 
  H: THandle; 
begin 
  FileName := AddBackslash(AName) + 'chk.tmp'; 
  H := CreateFile(FileName, GENERIC_READ or GENERIC_WRITE, 0, 0, 
    CREATE_NEW, FILE_ATTRIBUTE_TEMPORARY or FILE_FLAG_DELETE_ON_CLOSE, 0); 
  Result := H <> INVALID_HANDLE_VALUE; 
  if Result then CloseHandle(H);
end;

function IsPortable: Boolean;
begin
  Result := ExpandConstant('{param:portable|0}') = '1';
end;

function GetDefaultDirName(Param: String): String;
begin
  if IsPortable then
  begin
    if IsDirectoryWriteable(ExpandConstant('{src}')) then
      Result := '{src}'
    else
      Result := '{userdesktop}'
  end
  else
    Result := '{autopf}';
  Result := ExpandConstant(AddBackslash(Result) + Param);
end;

<event('InitializeWizard')>
procedure IsPortableInitializeWizard;
begin
  if IsPortable then
  begin
    WizardForm.DirEdit.Text := GetDefaultDirName('{#AppName}');
  end;
end;

<event('ShouldSkipPage')>
function ShouldSkipSelectDirPage(PageID: Integer): Boolean;
begin
  Result := (PageID = wpSelectDir) and not IsPortable;
end;

<event('ShouldSkipPage')>
function ShouldSkipSelectProgramGroupPage(PageID: Integer): Boolean;
begin
  Result := (PageID = wpSelectProgramGroup) and IsPortable;
end;