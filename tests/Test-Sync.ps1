Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
}

$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-github-sync-test-" + [Guid]::NewGuid().ToString('N'))
try {
    $sourceRoot = Join-Path $testRoot 'source'
    $repositoryRoot = Join-Path $testRoot 'repository'
    New-Item -ItemType Directory -Path $repositoryRoot -Force | Out-Null

    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'config.toml') -Content "model = 'example'`nexperimental_bearer_token = 'sk-this-must-not-be-copied-1234567890'`n"
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'skills\custom\SKILL.md') -Content "# Custom`nToken ghp_abcdefghijklmnopqrstuvwxyz123456`n"
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'skills\.system\internal\SKILL.md') -Content '# Built in'
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'hooks\daily.ps1') -Content 'Write-Host custom-hook'
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'prompts\notes.md') -Content 'safe prompt'
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'rules\default.rules') -Content 'safe rule'
    Write-Utf8NoBom -Path (Join-Path $sourceRoot 'skills\custom\.env') -Content 'DO_NOT_COPY=true'

    $syncScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'Sync-CodexBackup.ps1'
    & $syncScript -SourceRoot $sourceRoot -RepositoryRoot $repositoryRoot -SkipGit
    if ($LASTEXITCODE -ne 0) { throw 'The sync script returned failure.' }

    $backup = Join-Path $repositoryRoot 'backup'
    if (-not (Test-Path -LiteralPath (Join-Path $backup 'skills\custom\SKILL.md'))) { throw 'Custom skill was not copied.' }
    if (Test-Path -LiteralPath (Join-Path $backup 'skills\.system')) { throw 'Built-in skill directory was copied.' }
    if (Test-Path -LiteralPath (Join-Path $backup 'skills\custom\.env')) { throw '.env file was copied.' }
    $safeConfig = [System.IO.File]::ReadAllText((Join-Path $backup 'config.toml'))
    $safeSkill = [System.IO.File]::ReadAllText((Join-Path $backup 'skills\custom\SKILL.md'))
    if ($safeConfig -notmatch '__REDACTED__') { throw 'Config token was not redacted.' }
    if ($safeSkill -notmatch '__REDACTED_SECRET__') { throw 'Skill token was not redacted.' }
    if ($safeConfig -match 'sk-this-must-not-be-copied') { throw 'Original config token remains.' }

    Write-Host 'All tests passed.'
    exit 0
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
