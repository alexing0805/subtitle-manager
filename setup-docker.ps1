# 字幕管理器 Docker 设置脚本
# 用于配置 Docker 环境并启动服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  字幕管理器 Docker 设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否安装
$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
if (-not (Test-Path $dockerPath)) {
    Write-Host "❌ Docker 未安装，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "   可以从 https://www.docker.com/products/docker-desktop 下载" -ForegroundColor Yellow
    exit 1
}

# 添加 Docker 到 PATH
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"

# 检查 Docker 版本
Write-Host "✓ Docker 客户端已安装" -ForegroundColor Green
& $dockerPath version --format '{{.Client.Version}}' | Out-Null
if ($LASTEXITCODE -eq 0) {
    $version = & $dockerPath version --format '{{.Client.Version}}'
    Write-Host "  版本: $version" -ForegroundColor Gray
}

# 检查 Docker Desktop 是否运行
Write-Host ""
Write-Host "检查 Docker Desktop 状态..." -ForegroundColor Cyan
$dockerInfo = & $dockerPath info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker Desktop 引擎未运行" -ForegroundColor Yellow
    Write-Host "   正在启动 Docker Desktop..." -ForegroundColor Yellow
    
    # 启动 Docker Desktop
    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktop) {
        Start-Process $dockerDesktop
        Write-Host "   请等待 Docker Desktop 启动完成..." -ForegroundColor Yellow
        
        # 等待 Docker 引擎启动
        $maxAttempts = 30
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            Start-Sleep -Seconds 2
            $attempt++
            Write-Host "   等待中... ($attempt/$maxAttempts)" -ForegroundColor Gray
            
            $dockerInfo = & $dockerPath info 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Docker 引擎已启动" -ForegroundColor Green
                break
            }
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Host "❌ Docker 引擎启动超时，请手动启动 Docker Desktop" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ 找不到 Docker Desktop" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Docker 引擎正在运行" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker 环境配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 docker-compose
$composePath = "C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"
if (Test-Path $composePath) {
    Write-Host "✓ docker-compose 已安装" -ForegroundColor Green
} else {
    Write-Host "⚠️  docker-compose 未找到，将使用 docker compose 命令" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "现在可以构建和启动字幕管理器了：" -ForegroundColor Cyan
Write-Host "  1. cd e:\work\subtitle-manager" -ForegroundColor White
Write-Host "  2. docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "或者使用以下命令：" -ForegroundColor Cyan
Write-Host "  docker compose up -d" -ForegroundColor White
Write-Host ""
