Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[demo-stop] $Message" -ForegroundColor Cyan
}

function Stop-PortListener {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($null -eq $connections) {
        Write-Step "No listener on port $Port."
        return
    }

    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Step "Stopped PID ${procId} on port ${Port}."
        } catch {
            Write-Host "[demo-stop] Failed to stop PID ${procId} on port ${Port} - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Write-Step "Stopping demo stack listeners..."
Stop-PortListener -Port 5173
Stop-PortListener -Port 8110
Stop-PortListener -Port 8101
Write-Host "Demo stack stop routine complete." -ForegroundColor Green
