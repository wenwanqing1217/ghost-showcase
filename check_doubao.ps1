Write-Host "=== Checking if Doubao is running ===" -ForegroundColor Cyan
$doubao = Get-Process Doubao -ErrorAction SilentlyContinue
if ($doubao) {
    foreach ($p in $doubao) {
        Write-Host "  PID: $($p.Id)  Memory: $([math]::Round($p.WorkingSet64/1MB,1)) MB  CPU: $([math]::Round($p.CPU,1))s  Path: $($p.Path)"
    }
} else {
    Write-Host "  Doubao is NOT currently running."
}

Write-Host ""
Write-Host "=== Startup programs ===" -ForegroundColor Cyan
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-List
