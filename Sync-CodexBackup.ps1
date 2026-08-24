[CmdletBinding()]
param(
    [string]$SourceRoot,
    [string]$RepositoryRoot = $PSScriptRoot,
    [switch]$SkipGit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Utf8NoBomEncoding {
    return New-Object System.Text.UTF8Encoding($false)
}

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, (Get-Utf8NoBomEncoding))
}

function Test-TextFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    $textExtensions = @(
        '.bat', '.cmd', '.conf', '.config', '.css', '.csv', '.html', '.ini', '.js',
        '.json', '.md', '.ps1', '.py', '.rules', '.sh', '.toml', '.ts', '.tsx', '.txt',
        '.xml', '.yaml', '.yml'
    )
    return $textExtensions -contains ([System.IO.Path]::GetExtension($Path).ToLowerInvariant())
}

function ConvertTo-SafeText {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [switch]$ConfigFile
    )

    $result = $Content
    if ($ConfigFile) {
        $result = [regex]::Replace(
            $result,
            '(?im)^(\s*[^#\r\n=]*(?:api[_-]?key|token|secret|password|authorization|credential)[^=\r\n]*)\s*=\s*.*$',
            '$1 = "__REDACTED__"'
        )
    }

    # Prevent common token formats from reaching a Git remote even if a user pasted one
    # into a skill, hook, or prompt. File names such as .env and private-key extensions
    # are excluded before this point.
    $secretPatterns = @(
        '(?i)gh[pousr]_[A-Za-z0-9_]{20,}',
        '(?i)github_pat_[A-Za-z0-9_]{20,}',
        '(?i)sk-[A-Za-z0-9_-]{20,}',
        '(?i)AKIA[0-9A-Z]{16}',
        '-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z]+)? PRIVATE KEY-----'
    )
    foreach ($pattern in $secretPatterns) {
        $result = [regex]::Replace($result, $pattern, '__REDACTED_SECRET__')
    }
    return $result
}

function Test-ExcludedFile {
    param([Parameter(Mandatory = $true)][System.IO.FileInfo]$File)

    $excludedNames = @('.env', 'auth.json', 'credentials.json', 'id_rsa', 'id_ed25519')
    $excludedExtensions = @('.key', '.pem', '.pfx', '.p12')
    return ($excludedNames -contains $File.Name.ToLowerInvariant()) -or
        ($excludedExtensions -contains $File.Extension.ToLowerInvariant())
}

function Copy-SafeTree {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [string[]]$ExcludeTopLevelNames = @()
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        return 0
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $sourceFull = [System.IO.Path]::GetFullPath($Source).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $filesCopied = 0
    foreach ($file in Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force) {
        $relativePath = $file.FullName.Substring($sourceFull.Length).TrimStart([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
        $topLevelName = ($relativePath -split '[\\/]')[0]
        if (($ExcludeTopLevelNames -contains $topLevelName) -or (Test-ExcludedFile -File $file)) {
            continue
        }

        $target = Join-Path $Destination $relativePath
        $targetParent = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $targetParent)) {
            New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
        }

        if (Test-TextFile -Path $file.FullName) {
            $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
            Write-Utf8File -Path $target -Content (ConvertTo-SafeText -Content $content)
        }
        else {
            [System.IO.File]::Copy($file.FullName, $target, $true)
        }
        $filesCopied++
    }
    return $filesCopied
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$Repository,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $output = & git -C $Repository @Arguments 2>&1
    foreach ($line in $output) {
        Write-Host $line
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git -C `"$Repository`" $($Arguments -join ' ')"
    }
    return @($output)
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$Parent
    )

    $childFull = [System.IO.Path]::GetFullPath($Child)
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    if (-not $childFull.StartsWith($parentFull + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe path rejected: $childFull"
    }
}

try {
    if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
        $SourceRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
    }
    $sourceRootFull = [System.IO.Path]::GetFullPath($SourceRoot)
    $repositoryRootFull = [System.IO.Path]::GetFullPath($RepositoryRoot)
    if (-not (Test-Path -LiteralPath $sourceRootFull -PathType Container)) {
        throw "Codex directory was not found: $sourceRootFull"
    }
    if (-not (Test-Path -LiteralPath $repositoryRootFull -PathType Container)) {
        throw "Backup repository was not found: $repositoryRootFull"
    }

    $stagingRoot = Join-Path $repositoryRootFull 'backup.staging'
    $backupRoot = Join-Path $repositoryRootFull 'backup'
    $previousRoot = Join-Path $repositoryRootFull 'backup.previous'
    Assert-ChildPath -Child $stagingRoot -Parent $repositoryRootFull
    Assert-ChildPath -Child $backupRoot -Parent $repositoryRootFull
    Assert-ChildPath -Child $previousRoot -Parent $repositoryRootFull

    if (Test-Path -LiteralPath $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $stagingRoot -Force | Out-Null

    $copied = [ordered]@{}
    $copied['skills'] = Copy-SafeTree -Source (Join-Path $sourceRootFull 'skills') -Destination (Join-Path $stagingRoot 'skills') -ExcludeTopLevelNames @('.system')
    $copied['hooks'] = Copy-SafeTree -Source (Join-Path $sourceRootFull 'hooks') -Destination (Join-Path $stagingRoot 'hooks')
    $copied['rules'] = Copy-SafeTree -Source (Join-Path $sourceRootFull 'rules') -Destination (Join-Path $stagingRoot 'rules')
    $copied['prompts'] = Copy-SafeTree -Source (Join-Path $sourceRootFull 'prompts') -Destination (Join-Path $stagingRoot 'prompts')

    foreach ($fileName in @('config.toml', 'AGENTS.md')) {
        $sourceFile = Join-Path $sourceRootFull $fileName
        if (Test-Path -LiteralPath $sourceFile -PathType Leaf) {
            $content = [System.IO.File]::ReadAllText($sourceFile, [System.Text.Encoding]::UTF8)
            Write-Utf8File -Path (Join-Path $stagingRoot $fileName) -Content (ConvertTo-SafeText -Content $content -ConfigFile:($fileName -eq 'config.toml'))
        }
    }

    $manifest = [ordered]@{
        schemaVersion = 1
        createdAtUtc = [DateTime]::UtcNow.ToString('o')
        source = 'CODEX_HOME or %USERPROFILE%\\.codex'
        included = @('skills (excluding .system)', 'config.toml (redacted)', 'AGENTS.md', 'hooks', 'rules', 'prompts')
        excluded = @('authentication', 'sessions', 'memories', 'logs', 'cache', 'plugins cache', '.env files', 'private keys')
        copiedFiles = $copied
    }
    Write-Utf8File -Path (Join-Path $stagingRoot 'manifest.json') -Content (($manifest | ConvertTo-Json -Depth 5) + [Environment]::NewLine)

    if (Test-Path -LiteralPath $previousRoot) {
        Remove-Item -LiteralPath $previousRoot -Recurse -Force
    }
    if (Test-Path -LiteralPath $backupRoot) {
        Move-Item -LiteralPath $backupRoot -Destination $previousRoot
    }
    Move-Item -LiteralPath $stagingRoot -Destination $backupRoot
    if (Test-Path -LiteralPath $previousRoot) {
        Remove-Item -LiteralPath $previousRoot -Recurse -Force
    }

    Write-Host "Codex files copied to $backupRoot"
    if ($SkipGit) {
        exit 0
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git was not found. Install Git for Windows and run the script again.'
    }
    $gitDirectory = Join-Path $repositoryRootFull '.git'
    if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) {
        throw "The backup directory is not a Git repository: $repositoryRootFull"
    }

    Invoke-Git -Repository $repositoryRootFull -Arguments @('add', '--all', '--', 'backup') | Out-Null
    & git -C $repositoryRootFull diff --cached --quiet -- backup
    $hasChanges = $LASTEXITCODE -ne 0
    if (-not $hasChanges) {
        Write-Host 'No Codex backup changes to commit.'
        exit 0
    }

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss K'
    Invoke-Git -Repository $repositoryRootFull -Arguments @('commit', '-m', "Backup Codex configuration $timestamp", '--', 'backup') | Out-Null
    $branch = (& git -C $repositoryRootFull branch --show-current).Trim()
    if ([string]::IsNullOrWhiteSpace($branch)) {
        throw 'Cannot determine the current Git branch.'
    }
    Invoke-Git -Repository $repositoryRootFull -Arguments @('push', 'origin', $branch) | Out-Null
    Write-Host 'Codex backup committed and pushed successfully.'
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
