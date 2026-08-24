[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^(https://github\.com/|git@github\.com:)')]
    [string]$RepositoryUrl,

    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string]$Time = '20:00',

    [ValidatePattern('^[A-Za-z0-9._/-]+$')]
    [string]$Branch = 'main',

    [string]$TaskName = 'Codex Daily GitHub Sync'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-GitSetup {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $output = & git -C $PSScriptRoot @Arguments 2>&1
    foreach ($line in $output) {
        Write-Host $line
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($Arguments -join ' ')"
    }
}

try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git was not found. Install Git for Windows first: https://git-scm.com/download/win'
    }
    $scriptPath = Join-Path $PSScriptRoot 'Sync-CodexBackup.ps1'
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Sync script is missing: $scriptPath"
    }

    Invoke-GitSetup -Arguments @('init')
    $originUrl = (& git -C $PSScriptRoot remote get-url origin 2>$null)
    if ($LASTEXITCODE -eq 0) {
        Invoke-GitSetup -Arguments @('remote', 'set-url', 'origin', $RepositoryUrl)
    }
    else {
        Invoke-GitSetup -Arguments @('remote', 'add', 'origin', $RepositoryUrl)
    }
    Invoke-GitSetup -Arguments @('checkout', '-B', $Branch)

    $authorName = (& git -C $PSScriptRoot config user.name).Trim()
    $authorEmail = (& git -C $PSScriptRoot config user.email).Trim()
    if ([string]::IsNullOrWhiteSpace($authorName) -or [string]::IsNullOrWhiteSpace($authorEmail)) {
        throw 'Set your Git author first, for example: git config --global user.name "Your Name"; git config --global user.email "you@example.com"'
    }

    & $scriptPath -RepositoryRoot $PSScriptRoot -SkipGit
    if ($LASTEXITCODE -ne 0) {
        throw 'Initial backup copy failed.'
    }

    Invoke-GitSetup -Arguments @('add', '--all')
    & git -C $PSScriptRoot diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Invoke-GitSetup -Arguments @('commit', '-m', 'Initialize Codex backup automation')
    }
    Invoke-GitSetup -Arguments @('push', '--set-upstream', 'origin', $Branch)

    $taskAction = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -RepositoryRoot `"$PSScriptRoot`""
    $taskTrigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::ParseExact($Time, 'HH:mm', $null))
    $userId = "$env:USERDOMAIN\$env:USERNAME"
    $taskPrincipal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $TaskName -Action $taskAction -Trigger $taskTrigger -Principal $taskPrincipal -Description 'Backs up custom Codex skills and safe configuration to GitHub each day.' -Force | Out-Null

    Write-Host "Completed. The task '$TaskName' will run every day at $Time while $userId is signed in."
    Write-Host 'GitHub authentication is provided by your existing Git Credential Manager login or SSH key; no credential is stored in this project.'
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
