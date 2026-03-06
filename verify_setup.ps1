# 字幕管理器系统验证脚本
# 检查所有必要的配置和文件

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  字幕管理器系统验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# 检查文件是否存在
$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "api_server.py",
    "config.py",
    "subtitle_manager.py",
    "deploy.ps1",
    "web/package.json",
    "web/vite.config.js",
    "web/dist/index.html"
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

# 检查目录结构
$requiredDirs = @(
    "subtitle_sources",
    "web/src/views",
    "web/src/components",
    "web/src/stores",
    "web/dist",
    "test/movies",
    "test/tvshows"
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

# 检查 Docker
Write-Host "检查 Docker 环境..." -ForegroundColor Yellow
$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
if (Test-Path $dockerPath) {
    Write-Host "  ✓ Docker 客户端已安装" -ForegroundColor Green
    
    # 检查 Docker 引擎
    $env:Path += ";C:\Program Files\Docker\Docker\resources\bin"
    $dockerInfo = & $dockerPath info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker 引擎正在运行" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Docker 引擎未运行 (需要启动 Docker Desktop)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Docker 未安装" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# 检查端口
Write-Host "检查端口占用..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "  ⚠ 端口 8080 已被占用" -ForegroundColor Yellow
    Write-Host "    进程: $($portInUse.OwningProcess)" -ForegroundColor Gray
} else {
    Write-Host "  ✓ 端口 8080 可用" -ForegroundColor Green
}

Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  ✅ 所有检查通过！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "你可以使用以下命令启动系统：" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. 构建镜像:" -ForegroundColor Yellow
    Write-Host "     .\deploy.ps1 -Build" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. 启动服务:" -ForegroundColor Yellow
    Write-Host "     .\deploy.ps1 -Start" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. 访问 Web 界面:" -ForegroundColor Yellow
    Write-Host "     http://localhost:8080" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "  ⚠️  部分检查未通过" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
}

Write-Host ""
Read-Host "按 Enter 键继续"
