$proc = Get-CimInstance Win32_Process -Filter "ProcessId = 25728"
Write-Host "Parent PID 25728: $($proc.Name) - $($proc.CommandLine)"

# Try Stop-Process directly on parent
Write-Host ""
Write-Host "Trying Stop-Process on parent (PID 25728)..." -ForegroundColor Yellow
Stop-Process -Id 25728 -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

$vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
if ($vmmem) {
    Write-Host "vmmemWSL still running ($($vmmem.WorkingSet64/1MB) MB). Stopping WSL service..." -ForegroundColor Yellow
    Stop-Service -Name LxssManager -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Start-Service -Name LxssManager -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    
    $vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
    if ($vmmem) {
        Write-Host "Still running. Try Ctrl+Shift+Esc -> End Task on vmmemWSL manually." -ForegroundColor Red
    } else {
        Write-Host "Success! vmmemWSL stopped." -ForegroundColor Green
    }
} else {
    Write-Host "Success! vmmemWSL stopped." -ForegroundColor Green
}

Start-Sleep -Seconds 2
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host ""
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)" -ForegroundColor Cyan
