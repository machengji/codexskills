param(
  [Parameter(Mandatory=$true)][string]$DocxPath,
  [Parameter(Mandatory=$true)][string]$PdfPath
)
$ErrorActionPreference = 'Continue'
$app = $null
$doc = $null
foreach ($progId in @('Word.Application', 'KWPS.Application')) {
    try {
        $type = [type]::GetTypeFromProgID($progId)
        if ($null -eq $type) { continue }
        $app = New-Object -ComObject $progId
        $app.Visible = $false
        $app.DisplayAlerts = 0
        $doc = $app.Documents.Open($DocxPath, $false, $true)
        $doc.SaveAs([ref]$PdfPath, [ref]17)
        $pages = [int]$doc.ComputeStatistics(2)
        Write-Output "EXPORTED pages=$pages via $progId"
        break
    } catch {
        Write-Output "ERR $progId : $($_.Exception.Message)"
    }
}
if ($null -ne $doc) { try { $doc.Close($false) } catch {} }
if ($null -ne $app) { try { $app.Quit() } catch {} }
