[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = 'Codex Daily GitHub Sync'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess($TaskName, 'Remove scheduled task')) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task: $TaskName"
    }
}
else {
    Write-Host "Scheduled task not found: $TaskName"
}
