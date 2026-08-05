' Flow API 后台启动脚本（无窗口）
' 双击运行，进程在后台静默运行
' 查看日志：D:/MW/flow/apps/api/logs/

Dim shell, fso
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 确保日志目录存在
Dim logDir : logDir = "D:\MW\flow\apps\api\logs"
If Not fso.FolderExists(logDir) Then
    fso.CreateFolder(logDir)
End If

Dim cmd : cmd = "cmd /c cd /d D:\MW\flow\apps\api && set PORT=3036 && set HOST=127.0.0.1 && npx tsx src\index.ts > logs\output.log 2>&1"

' 0 = 隐藏窗口
shell.Run cmd, 0, False
