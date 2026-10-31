' Aegis AI - Windows Silent Desktop Application Launcher
' Launches Aegis AI completely windowless directly into the background / system tray.

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

strPythonw = strDir & "\.venv\Scripts\pythonw.exe"
strAegis = strDir & "\aegis.py"

If fso.FileExists(strPythonw) Then
    WshShell.CurrentDirectory = strDir
    WshShell.Run Chr(34) & strPythonw & Chr(34) & " " & Chr(34) & strAegis & Chr(34), 0, False
Else
    MsgBox "Aegis AI virtual environment not found in .venv!" & vbCrLf & "Please run .\scripts\setup_env.ps1 first.", 16, "Aegis AI Launcher"
End If

Set WshShell = Nothing
Set fso = Nothing
