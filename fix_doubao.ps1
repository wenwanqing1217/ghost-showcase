# Step 1: Remove Doubao from startup
Write-Host "=== Removing Doubao from startup ===" -ForegroundColor Yellow
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "doubao" -ErrorAction SilentlyContinue
Write-Host "Doubao startup entry removed." -ForegroundColor Green

# Step 2: Kill all Doubao processes
Write-Host ""
Write-Host "=== Closing Doubao ===" -ForegroundColor Yellow
Stop-Process -Name Doubao -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$remaining = Get-Process Doubao -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Some Doubao processes still running." -ForegroundColor Red
} else {
    Write-Host "All Doubao processes closed." -ForegroundColor Green
}

# Step 3: Show memory after
Write-Host ""
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)" -ForegroundColor Cyan
