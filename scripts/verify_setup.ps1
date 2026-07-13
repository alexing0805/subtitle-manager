# Subtitle Manager repository verification script

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  字幕管理器仓库校验" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "README.md",
    "backend/api_server.py",
    "backend/config.py",
    "backend/subtitle_manager.py",
    "web/package.json",
    "web/vite.config.js"
)

Write-Host "检查必要文件..." -ForegroundColor Yellow
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (缺失)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""

$requiredDirs = @(
    "backend/subtitle_sources",
    "web/src/views",
    "web/src/components",
    "docs",
    "scripts"
)

Write-Host "检查目录结构..." -ForegroundColor Yellow
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dir (缺失)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""
Write-Host "检查 Docker 环境..." -ForegroundColor Yellow
$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
if (Test-Path $dockerPath) {
    Write-Host "  ✓ Docker 客户端已安装" -ForegroundColor Green
} else {
    Write-Host "  ✗ Docker 未安装" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  ✅ 仓库结构校验通过" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  部分检查未通过" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
