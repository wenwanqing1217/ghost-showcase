# Try to forcefully terminate WSL VM process
Write-Host "Attempting to stop WSL..." -ForegroundColor Yellow
Stop-Process -Name vmmemWSL -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Check if it worked
$vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
if ($vmmem) {
    Write-Host "vmmemWSL still running. Trying wsl --shutdown..." -ForegroundColor Yellow
    wsl --shutdown
    Start-Sleep -Seconds 5
    $vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
    if ($vmmem) {
        Write-Host "WSL shutdown did not work. You may need to restart your computer." -ForegroundColor Red
    } else {
        Write-Host "WSL shutdown successful!" -ForegroundColor Green
    }
} else {
    Write-Host "vmmemWSL stopped successfully!" -ForegroundColor Green
}

Write-Host ""
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Current Memory: $usedGB GB / $totalGB GB ($pct% used)"
