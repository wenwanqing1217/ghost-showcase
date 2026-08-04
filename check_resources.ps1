Write-Host "=== System Resources ===" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)"

$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Host "CPU Load: $cpu%"

Write-Host ""
Write-Host "=== Top 15 Processes by Memory ===" -ForegroundColor Cyan
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 Name, Id, @{N='CPU(s)';E={[math]::Round($_.CPU,1)}}, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize

Write-Host "=== Top 15 Processes by CPU ===" -ForegroundColor Cyan
Get-Process | Where-Object {$_.CPU -gt 0} | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, @{N='CPU(s)';E={[math]::Round($_.CPU,1)}}, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize

Write-Host "=== Docker Containers ===" -ForegroundColor Cyan
try {
    $containers = docker ps --format "{{.Names}}\t{{.Status}}\t{{.ID}}" 2>$null
    if ($containers) { $containers } else { Write-Host "No containers running" }
} catch { Write-Host "Docker not available" }

Write-Host ""
Write-Host "=== Disk Usage ===" -ForegroundColor Cyan
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $freeGB = [math]::Round($_.FreeSpace/1GB, 1)
    $sizeGB = [math]::Round($_.Size/1GB, 1)
    Write-Host "$($_.DeviceID) $freeGB GB free / $sizeGB GB total"
}
