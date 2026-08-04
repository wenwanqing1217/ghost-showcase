# Force kill vmmemWSL using taskkill
Write-Host "=== Method 1: taskkill ===" -ForegroundColor Cyan
taskkill /F /IM vmmemWSL.exe 2>&1 | Out-Null
Start-Sleep -Seconds 2

$vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
if ($vmmem) {
    Write-Host "Method 1 failed. Trying Method 2..." -ForegroundColor Yellow
    
    # Method 2: Kill the parent process tree
    Write-Host "=== Method 2: Kill parent process ===" -ForegroundColor Cyan
    $parent = (Get-CimInstance Win32_Process -Filter "ProcessId = $($vmmem.Id)").ParentProcessId
    Write-Host "Parent PID: $parent"
    if ($parent -and $parent -ne 0) {
        Stop-Process -Id $parent -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
    
    $vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
    if ($vmmem) {
        Write-Host "Method 2 failed. Trying Method 3..." -ForegroundColor Yellow
        
        # Method 3: Use wmic to terminate
        Write-Host "=== Method 3: WMIC terminate ===" -ForegroundColor Cyan
        wmic process where "name='vmmemWSL.exe'" delete 2>&1
        Start-Sleep -Seconds 3
        
        $vmmem = Get-Process vmmemWSL -ErrorAction SilentlyContinue
        if ($vmmem) {
            Write-Host "Method 3 failed. Last resort: reboot required." -ForegroundColor Red
        } else {
            Write-Host "Success! vmmemWSL killed." -ForegroundColor Green
        }
    } else {
        Write-Host "Success! vmmemWSL killed." -ForegroundColor Green
    }
} else {
    Write-Host "Success! vmmemWSL already stopped." -ForegroundColor Green
}

Start-Sleep -Seconds 2
Write-Host ""
$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
Write-Host "Memory: $usedGB GB / $totalGB GB ($pct% used)" -ForegroundColor Cyan
