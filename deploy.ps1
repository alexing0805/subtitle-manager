# Subtitle Manager Docker Deploy Script
param(
    [switch]$Build,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status
)

$dockerPath = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$dockerComposePath = "C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"
$env:Path += ";C:\Program Files\Docker\Docker\resources\bin"

function Test-Docker {
    Write-Host "Checking Docker environment..."
    
    if (-not (Test-Path $dockerPath)) {
        Write-Host "Docker not installed" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Docker client installed" -ForegroundColor Green
    
    $info = & $dockerPath info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker engine not running, starting..." -ForegroundColor Yellow
        $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerDesktop) {
            Start-Process $dockerDesktop
            $attempts = 0
            while ($attempts -lt 30) {
                Start-Sleep -Seconds 2
                $attempts++
                Write-Host "Waiting for Docker... ($attempts/30)"
                $info = & $dockerPath info 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Docker engine started" -ForegroundColor Green
                    break
                }
            }
            if ($attempts -eq 30) {
                Write-Host "Docker start timeout" -ForegroundColor Red
                return $false
            }
        } else {
            Write-Host "Docker Desktop not found" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "Docker engine running" -ForegroundColor Green
    }
    return $true
}

function Build-Images {
    Write-Host ""
    Write-Host "Building Docker images..." -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Docker)) { exit 1 }
    
    New-Item -ItemType Directory -Force -Path test\movies, test\tvshows, logs, data | Out-Null
    
    if (-not (Test-Path "test\movies\Test.Movie.2024.1080p.mkv")) {
        New-Item -ItemType File -Force -Path test\movies\Test.Movie.2024.1080p.mkv | Out-Null
    }
    if (-not (Test-Path "test\tvshows\Test.Show.S01E01.mkv")) {
        New-Item -ItemType File -Force -Path test\tvshows\Test.Show.S01E01.mkv | Out-Null
    }
    
    & $dockerComposePath build --no-cache
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Build successful" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Build failed" -ForegroundColor Red
        exit 1
    }
}

function Start-Service {
    Write-Host ""
    Write-Host "Starting subtitle manager service..." -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Docker)) { exit 1 }
    
    New-Item -ItemType Directory -Force -Path test\movies, test\tvshows, logs, data | Out-Null
    
    & $dockerComposePath up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Service started" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access URLs:" -ForegroundColor Cyan
        Write-Host "  Web UI: http://localhost:8080"
        Write-Host "  API Docs: http://localhost:8080/docs"
        Write-Host "  Health: http://localhost:8080/health"
    } else {
        Write-Host ""
        Write-Host "Failed to start service" -ForegroundColor Red
        exit 1
    }
}

function Stop-Service {
    Write-Host ""
    Write-Host "Stopping subtitle manager service..." -ForegroundColor Cyan
    Write-Host ""
    
    & $dockerComposePath down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Service stopped" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Failed to stop service" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host ""
    Write-Host "Viewing logs..." -ForegroundColor Cyan
    Write-Host ""
    & $dockerComposePath logs -f
}

function Show-Status {
    Write-Host ""
    Write-Host "Service status:" -ForegroundColor Cyan
    Write-Host ""
    & $dockerComposePath ps
}

if ($Build) {
    Build-Images
} elseif ($Start) {
    Start-Service
} elseif ($Stop) {
    Stop-Service
} elseif ($Restart) {
    Stop-Service
    Start-Sleep -Seconds 2
    Start-Service
} elseif ($Logs) {
    Show-Logs
} elseif ($Status) {
    Show-Status
} else {
    Write-Host ""
    Write-Host "Subtitle Manager Deploy Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\deploy.ps1 -Build    Build images"
    Write-Host "  .\deploy.ps1 -Start    Start service"
    Write-Host "  .\deploy.ps1 -Stop     Stop service"
    Write-Host "  .\deploy.ps1 -Restart  Restart service"
    Write-Host "  .\deploy.ps1 -Logs     View logs"
    Write-Host "  .\deploy.ps1 -Status   View status"
    Write-Host ""
    Write-Host "Quick start:"
    Write-Host "  1. .\deploy.ps1 -Build"
    Write-Host "  2. .\deploy.ps1 -Start"
    Write-Host "  3. Open http://localhost:8080"
}
