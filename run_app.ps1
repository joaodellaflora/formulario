Param(
  [switch]$Foreground
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $root

# Prefer .venv python if present
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
  $py = $venvPython
} else {
  $pyCmd = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pyCmd) { Write-Error 'Python não encontrado no PATH e .venv não existe.'; Pop-Location; exit 1 }
  $py = $pyCmd.Source
}

# Install dependencies idempotently
Write-Output "Using python: $py"
& $py -m pip install -r .\requirements.txt | Out-Null

# Ensure logs directory
$logDir = Join-Path $root 'logs'
if (-not (Test-Path $logDir)) { New-Item -Path $logDir -ItemType Directory | Out-Null }
$out = Join-Path $logDir 'server_out.log'
$err = Join-Path $logDir 'server_err.log'

if ($Foreground) {
  Write-Output 'Starting app in foreground... (Ctrl+C to stop)'
  & $py .\app.py
} else {
  Write-Output "Starting app in background. Logs: $out , $err"
  Start-Process -FilePath $py -ArgumentList '.\app.py' -WorkingDirectory $root -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden | Out-Null
}

Pop-Location
