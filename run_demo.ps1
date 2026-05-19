param(
    [switch]$SkipDependencyInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[demo] $Message" -ForegroundColor Cyan
}

function Stop-PortListener {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($null -eq $connections) {
        return
    }
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Step "Stopped existing process on port ${Port} (PID ${procId})."
        } catch {
            Write-Host "[demo] Failed to stop PID ${procId} on port ${Port} - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

function Wait-Http {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 45
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$gatewayDir = Join-Path $root "llm_gatewayV3"
$frontendDir = Join-Path $root "frontend"

if (-not (Test-Path $gatewayDir)) {
    throw "Could not find llm_gatewayV3 at $gatewayDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Could not find frontend at $frontendDir"
}

Write-Step "Preparing demo startup..."
Stop-PortListener -Port 8101
Stop-PortListener -Port 8110
Stop-PortListener -Port 5173

if (-not $SkipDependencyInstall) {
    Write-Step "Running uv sync..."
    Push-Location $root
    uv sync
    Pop-Location

    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Step "Installing frontend dependencies..."
        Push-Location $frontendDir
        npm install
        Pop-Location
    }
}

Write-Step "Starting Gateway (port 8101)..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$gatewayDir'; uv run python main.py"
) | Out-Null

if (-not (Wait-Http -Url "http://localhost:8101/v1/providers" -TimeoutSeconds 60)) {
    throw "Gateway failed to become healthy at http://localhost:8101/v1/providers"
}
Write-Step "Gateway is up."

Write-Step "Starting Demo API (port 8110)..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; uv run python demo_api.py"
) | Out-Null

if (-not (Wait-Http -Url "http://localhost:8110/api/project-meta" -TimeoutSeconds 60)) {
    throw "Demo API failed to become healthy at http://localhost:8110/api/project-meta"
}
Write-Step "Demo API is up."

Write-Step "Starting Frontend (port 5173)..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontendDir'; npm run dev"
) | Out-Null

if (-not (Wait-Http -Url "http://localhost:5173" -TimeoutSeconds 75)) {
    throw "Frontend failed to become healthy at http://localhost:5173"
}
Write-Step "Frontend is up."

Write-Step "Opening demo UI in browser..."
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "Demo stack started successfully:" -ForegroundColor Green
Write-Host "  Gateway:   http://localhost:8101"
Write-Host "  Demo API:  http://localhost:8110"
Write-Host "  Frontend:  http://localhost:5173"
Write-Host ""
Write-Host "Tip: run with -SkipDependencyInstall for faster repeat runs."
