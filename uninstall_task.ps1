# uninstall_task.ps1
# Removes the scheduled task created by install_task.ps1

$taskName = 'DeslocamentoApp'
Try {
  if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Output "Scheduled Task '$taskName' removed"
  } else {
    Write-Output "Scheduled Task '$taskName' not found"
  }
} Catch {
  Write-Error "Failed to unregister scheduled task: $_"
}
