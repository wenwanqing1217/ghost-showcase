# ════════════════════════════════════════════════════════════════════
# Ghost Platform — PostgreSQL 备份脚本
# 用法:   powershell -File scripts/backup.ps1 [-db ghost] [-keep 7]
# 默认:   备份全部业务库（ghost/nebula/alpha_id/gateway），保留最近 7 份
# ════════════════════════════════════════════════════════════════════

param(
  [string]$db = "",              # 指定单个库；留空则备份全部
  [int]$keep = 7                 # 每库保留最近 N 份
)

$ErrorActionPreference = "Stop"
$CONTAINER = "mw-db-1"
$DB_USER = "ghost"
$BACKUP_DIR = Join-Path $PSScriptRoot "..\backups"
$DATABASES = @("ghost", "nebula", "alpha_id", "gateway")

# 确保备份目录存在
New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null

# 检查容器
$running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$CONTAINER$"
if (-not $running) {
  Write-Host "ERROR: 数据库容器 $CONTAINER 未运行。请先 docker compose up -d db" -ForegroundColor Red
  exit 1
}

# 确定要备份的库
$targets = if ($db) { @($db) } else { $DATABASES }

foreach ($name in $targets) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $tmp = "/tmp/${name}-${stamp}.dump"
  $dest = Join-Path $BACKUP_DIR "${name}-${stamp}.dump"

  Write-Host "── 备份 [$name] → $dest" -ForegroundColor Cyan
  try {
    docker exec $CONTAINER pg_dump -U $DB_USER -d $name -F c -f $tmp 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "pg_dump 失败 (exit $LASTEXITCODE)" }
    docker cp "${CONTAINER}:${tmp}" $dest | Out-Null
    docker exec $CONTAINER rm -f $tmp
    $size = (Get-Item $dest).Length / 1KB
    Write-Host "  OK  ($([math]::Round($size,1)) KB)" -ForegroundColor Green
  } catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    continue
  }

  # 清理：保留最近 $keep 份
  $older = Get-ChildItem $BACKUP_DIR -Filter "${name}-*.dump" | Sort-Object Name -Descending | Select-Object -Skip $keep
  foreach ($f in $older) {
    Remove-Item $f.FullName -Force
    Write-Host "  清理旧备份: $($f.Name)" -ForegroundColor DarkGray
  }
}

# 汇总
Write-Host "`n══════════════════════════════════════" -ForegroundColor Cyan
$total = Get-ChildItem $BACKUP_DIR -Filter "*.dump" | Measure-Object
$totalSize = (Get-ChildItem $BACKUP_DIR -Filter "*.dump" | Measure-Object Length -Sum).Sum / 1MB
Write-Host "备份完成: $($total.Count) 份文件, 共 $([math]::Round($totalSize,1)) MB" -ForegroundColor Green
Write-Host "目录: $BACKUP_DIR" -ForegroundColor DarkGray
