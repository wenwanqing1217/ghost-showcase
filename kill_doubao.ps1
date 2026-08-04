Stop-Process -Name Doubao -Force -ErrorAction SilentlyContinue
$remaining = Get-Process Doubao -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Some Doubao processes could not be closed"
} else {
    Write-Host "All Doubao processes stopped successfully"
}
