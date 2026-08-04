Write-Host "Force killing WSL VM process..." -ForegroundColor Yellow
Stop-Process -Name vmmemWSL -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
if ($vmmem) {
    Write-Host "vmmemWSL still running after force kill. Restart recommended." -ForegroundColor Red
} else {
    Write-Host "WSL VM stopped!" -ForegroundColor Green
}

Start-Sleep -Seconds 2
Write-Host ""
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)" -ForegroundColor Cyan
