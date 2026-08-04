Write-Host "=== Current Memory Usage ===" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)"

Write-Host ""
Write-Host "=== WSL related processes ===" -ForegroundColor Cyan
Get-Process -Name "vmmem*","wsl*","bash*","ubuntu*" -ErrorAction SilentlyContinue | Select-Object Name, Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, Status | Format-Table -AutoSize
