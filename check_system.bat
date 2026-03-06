@echo off
chcp 65001 >nul
echo ========================================
echo   字幕管理器系统验证
echo ========================================
echo.

echo 检查必要文件...
if exist "Dockerfile" (echo   [OK] Dockerfile) else (echo   [MISSING] Dockerfile)
if exist "docker-compose.yml" (echo   [OK] docker-compose.yml) else (echo   [MISSING] docker-compose.yml)
if exist "requirements.txt" (echo   [OK] requirements.txt) else (echo   [MISSING] requirements.txt)
if exist "api_server.py" (echo   [OK] api_server.py) else (echo   [MISSING] api_server.py)
if exist "deploy.ps1" (echo   [OK] deploy.ps1) else (echo   [MISSING] deploy.ps1)
if exist "web\package.json" (echo   [OK] web/package.json) else (echo   [MISSING] web/package.json)
if exist "web\dist\index.html" (echo   [OK] web/dist/index.html) else (echo   [MISSING] web/dist/index.html)

echo.
echo 检查目录结构...
if exist "subtitle_sources" (echo   [OK] subtitle_sources) else (echo   [MISSING] subtitle_sources)
if exist "web\src\views" (echo   [OK] web/src/views) else (echo   [MISSING] web/src/views)
if exist "web\dist" (echo   [OK] web/dist) else (echo   [MISSING] web/dist)
if exist "test\movies" (echo   [OK] test/movies) else (echo   [MISSING] test/movies)
if exist "test\tvshows" (echo   [OK] test/tvshows) else (echo   [MISSING] test/tvshows)

echo.
echo 检查 Docker 环境...
if exist "C:\Program Files\Docker\Docker\resources\bin\docker.exe" (
    echo   [OK] Docker 客户端已安装
) else (
    echo   [MISSING] Docker 未安装
)

echo.
echo ========================================
echo 检查完成！
echo ========================================
echo.
echo 使用方法:
echo   1. 构建镜像: .\deploy.ps1 -Build
echo   2. 启动服务: .\deploy.ps1 -Start
echo   3. 访问界面: http://localhost:8080
echo.
pause
