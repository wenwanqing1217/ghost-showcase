# ════════════════════════════════════════════════════════════════════
# Ghost Platform — PostgreSQL 恢复脚本
# 用法:   powershell -File scripts/restore.ps1 -db ghost -file backups/ghost-20260805-134900.dump
# ⚠ 危险操作：恢复将覆盖目标库现有数据，请确认备份文件
# ════════════════════════════════════════════════════════════════════

param(
  [Parameter(Mandatory = $true)][string]$db,       # 目标库名
  [Parameter(Mandatory = $true)][string]$file      # 备份文件路径
)

$ErrorActionPreference = "Stop"
$CONTAINER = "mw-db-1"
$DB_USER = "ghost"

# 校验备份文件
$dump = Resolve-Path $file -ErrorAction SilentlyContinue
if (-not $dump) { Write-Host "ERROR: 备份文件不存在: $file" -ForegroundColor Red; exit 1 }

# 校验文件名与目标库匹配（防止恢复错库）
$base = Split-Path $dump.Path -Leaf
if ($base -notmatch "^${db}-") {
  Write-Host "WARNING: 备份文件名 $base 与目标库 $db 不匹配，请再次确认！" -ForegroundColor Yellow
}

# 检查容器
$running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$CONTAINER$"
if (-not $running) {
  Write-Host "ERROR: 数据库容器 $CONTAINER 未运行。" -ForegroundColor Red
  exit 1
}

Write-Host "即将恢复：库 [$db] ← $($dump.Path)" -ForegroundColor Yellow
Write-Host "此操作会覆盖现有数据！输入 YES 继续:" -NoNewline
$confirm = Read-Host
if ($confirm -ne "YES") { Write-Host "已取消。" -ForegroundColor DarkGray; exit 0 }

$tmp = "/tmp/restore-$(Get-Date -Format 'yyyyMMddHHmmss').dump"
try {
  docker cp $dump.Path "${CONTAINER}:${tmp}" | Out-Null
  docker exec $CONTAINER pg_restore -U $DB_USER -d $db --clean --if-exists $tmp 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "pg_restore 失败 (exit $LASTEXITCODE)" }
  docker exec $CONTAINER rm -f $tmp
  Write-Host "✅ 恢复完成: $db" -ForegroundColor Green
} catch {
  Write-Host "FAIL: $_" -ForegroundColor Red
  exit 1
}
