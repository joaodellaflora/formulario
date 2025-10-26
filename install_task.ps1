# install_task.ps1
# Registers a Scheduled Task that runs run_app.ps1 at user logon.

$ErrorActionPreference = 'Stop'
$taskName = 'DeslocamentoApp'
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$runScript = Join-Path $root 'run_app.ps1'

# PowerShell executable
$psPath = (Get-Command powershell).Source

# Create action and trigger
$action = New-ScheduledTaskAction -Execute $psPath -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Register the task for current user
Try {
  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description 'Start Deslocamento app at logon' -User $env:USERNAME -RunLevel Limited -Force
  Write-Output "Scheduled Task '$taskName' registered for user $env:USERNAME"
} Catch {
  Write-Error "Failed to register scheduled task: $_"
}
