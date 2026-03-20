# NAS SMB 挂载脚本
# 用法: .\scripts\mount-nas.ps1 -NasHost nas.local -Share "Video\\Link" -MountLetter Z:

param(
    [string]$NasHost = "nas.local",
    [string]$Share = "Video\\Link",
    [string]$MountLetter = "Z:",
    [string]$Username,
    [string]$Password
)

if (-not $Username) {
    $Username = Read-Host "请输入 NAS 用户名"
}

if (-not $Password) {
    $secure = Read-Host "请输入 NAS 密码" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
}

$RemotePath = "\\$NasHost\$Share"

Write-Host "正在挂载 NAS 共享文件夹..." -ForegroundColor Green
Write-Host "NAS 地址: $NasHost" -ForegroundColor Gray
Write-Host "共享路径: $RemotePath" -ForegroundColor Gray
Write-Host "挂载盘符: $MountLetter" -ForegroundColor Gray
Write-Host ""

$existing = Get-WmiObject -Class Win32_NetworkConnection | Where-Object { $_.RemoteName -eq $RemotePath }
if ($existing) {
    Write-Host "检测到已存在挂载，先断开..." -ForegroundColor Yellow
    net use $MountLetter /delete 2>$null | Out-Null
    net use $RemotePath /delete 2>$null | Out-Null
}

Write-Host "正在连接..." -ForegroundColor Cyan
$result = net use $MountLetter $RemotePath /user:$Username $Password /persistent:yes 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "挂载成功" -ForegroundColor Green
    Write-Host "你现在可以继续运行：" -ForegroundColor Cyan
    Write-Host "  docker compose -f docker-compose.nas.yml up -d" -ForegroundColor White
} else {
    Write-Host "挂载失败" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
}
