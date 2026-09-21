; IziBox v2.1.0 — Inno Setup installer
; Пакет: один IziBox.exe (PyInstaller one-file, фронтенд внутри).
; Данные пользователя (data\ — БД, ключ шифрования) создаются приложением
; в {app}\data при запуске. Inno трекает только установленные файлы, поэтому
; data\ НЕ удаляется ни при апгрейде, ни при деинсталляции (персистентность).

#define AppName "IziBox"
#define AppVersion "2.1.0"
#define AppPublisher "IziBox"
#define AppExeName "IziBox.exe"

[Setup]
AppId={{8C4F3E2B-1D5E-4F9C-8A2E-3E6D7C8B9A0F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=IziBox-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
; Не удалять data\ при деинсталляции — это пользовательские данные.
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[Files]
Source: "..\backend\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; Flags: nowait postinstall skipifsilent
