<#
.SYNOPSIS
  Runs the QET agent suite (Understanding -> Test Cases -> Test Data -> Playwright
  -> Execution -> Report) against a target application source.

.DESCRIPTION
  Edit $SourcePath below and re-run this script whenever you want to point the
  suite at a different codebase (a folder, or an already-built .zip).

.EXAMPLE
  .\run_agent_suite.ps1
  .\run_agent_suite.ps1 -SourcePath "C:\path\to\other_app" -StartSampleApp:$false
#>

param(
    # ==================== EDIT THIS TO SWITCH TARGETS ====================
    [string]$SourcePath = "sample_test_target_app",
    # =======================================================================

    [string]$BaseUrl = "http://127.0.0.1:5000",
    [string]$AllowedTestHost = "127.0.0.1",
    [string]$GeminiApiKey = $env:GEMINI_API_KEY,
    [bool]$StartSampleApp = $true,
    [bool]$InstallDeps = $false
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if ($InstallDeps) {
    Write-Host "Installing dependencies ..." -ForegroundColor Cyan
    pip install -r requirements.txt --quiet --disable-pip-version-check
    pip install fastapi uvicorn python-multipart httpx --quiet --disable-pip-version-check
    pip install -r sample_test_target_app\requirements.txt --quiet --disable-pip-version-check
    python -m playwright install chromium
}

$RunId = "RUN-CLI-" + (Get-Date -Format "yyyyMMddHHmmss")
$env:QET_TEST_BASE_URL = $BaseUrl
$env:QET_ALLOWED_TEST_HOST = $AllowedTestHost
if ($GeminiApiKey) { $env:GEMINI_API_KEY = $GeminiApiKey }
$env:FLASK_DEBUG = "0"

$appProcess = $null
if ($StartSampleApp) {
    Write-Host "Starting sample_test_target_app on $BaseUrl ..." -ForegroundColor Cyan
    $appProcess = Start-Process -FilePath "python" -ArgumentList "sample_test_target_app\app.py" -PassThru -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $resp = Invoke-WebRequest -Uri "$BaseUrl/api/v1/health" -UseBasicParsing -TimeoutSec 2
            if ($resp.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
    }
    if (-not $ready) {
        Write-Warning "Sample app did not report healthy in time; continuing anyway."
    } else {
        Write-Host "Sample app is up." -ForegroundColor Green
    }
}

$exitCode = 0
try {
    Write-Host "`nRunning agent suite against '$SourcePath' (Run ID: $RunId) ..." -ForegroundColor Cyan
    python scripts\run_agent_suite.py --source $SourcePath --run-id $RunId
    $exitCode = $LASTEXITCODE
}
finally {
    if ($appProcess) {
        Write-Host "`nStopping sample app (PID $($appProcess.Id)) ..." -ForegroundColor Cyan
        Stop-Process -Id $appProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`nArtifacts: uploads\$RunId\artifacts\" -ForegroundColor Yellow
exit $exitCode
