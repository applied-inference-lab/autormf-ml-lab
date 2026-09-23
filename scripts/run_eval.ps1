# scripts/run_eval.ps1
# PowerShell script to run evaluation of local model control mappings in .venv.

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    # Fallback to standard python in PATH if .venv is not yet set up
    $PythonExe = "python"
}

$ScriptPath = Join-Path $PSScriptRoot "evaluate_local_model.py"
$LogPath = Join-Path $PSScriptRoot "evaluation_history.log"

Write-Host "Running local model evaluation..." -ForegroundColor Cyan
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

"==================================================" | Out-File $LogPath -Append -Encoding utf8
"EVALUATION RUN AT: $Timestamp" | Out-File $LogPath -Append -Encoding utf8
"==================================================" | Out-File $LogPath -Append -Encoding utf8

Push-Location $WorkspaceRoot
& $PythonExe $ScriptPath | Tee-Object -FilePath $LogPath -Append
Pop-Location

Write-Host "Evaluation completed. Results appended to $LogPath" -ForegroundColor Green
