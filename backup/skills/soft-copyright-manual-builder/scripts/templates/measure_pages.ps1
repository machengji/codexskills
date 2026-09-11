param([Parameter(Mandatory=$true)][string]$DocxPath)

$ErrorActionPreference = 'Continue'
$app = $null
$document = $null
foreach ($progId in @('Word.Application', 'KWPS.Application', 'WPS.Application')) {
    try {
        $type = [type]::GetTypeFromProgID($progId)
        if ($null -eq $type) { Write-Output "skip $progId (not installed)"; continue }
        $app = New-Object -ComObject $progId
        $app.Visible = $false
        $app.DisplayAlerts = 0
        $document = $app.Documents.Open($DocxPath, $false, $true)
        $document.Repaginate()
        $pages = [int]$document.ComputeStatistics(2)
        Write-Output "PAGES=$pages via $progId"
        break
    } catch {
        Write-Output "ERR $progId : $($_.Exception.Message)"
    }
}
if ($null -ne $document) { try { $document.Close($false) } catch {} }
if ($null -ne $app) { try { $app.Quit() } catch {} }
