param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,
    [Parameter(Mandatory = $true)]
    [string]$TxtPath,
    [int]$MinimumPages = 70,
    [ValidateRange(0, 2147483647)]
    [int]$BackendSourceLines = 0,
    [ValidateRange(0, 2147483647)]
    [int]$TotalSourceLines = 0,
    [ValidateRange(1, 100)]
    [int]$MinimumBackendRatioPercent = 85
)
$ErrorActionPreference = 'Stop'
$DocxPath = [System.IO.Path]::GetFullPath($DocxPath)
$TxtPath = [System.IO.Path]::GetFullPath($TxtPath)
if (-not (Test-Path -LiteralPath $DocxPath -PathType Leaf)) { throw "代码 Word 不存在：$DocxPath" }
if (-not (Test-Path -LiteralPath $TxtPath -PathType Leaf)) { throw "代码 TXT 不存在：$TxtPath" }
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Read-ZipEntryText {
    param([System.IO.Compression.ZipArchive]$Zip, [string]$EntryName)
    $entry = $Zip.GetEntry($EntryName)
    if ($null -eq $entry) { throw "DOCX 缺少条目：$EntryName" }
    $stream = $entry.Open()
    try {
        $reader = [System.IO.StreamReader]::new($stream, [System.Text.UTF8Encoding]::new($false, $true), $true)
        try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
    } finally { $stream.Dispose() }
}
$zip = [System.IO.Compression.ZipFile]::OpenRead($DocxPath)
try {
    [xml]$documentXml = Read-ZipEntryText -Zip $zip -EntryName 'word/document.xml'
} finally {
    $zip.Dispose()
}
$ns = [System.Xml.XmlNamespaceManager]::new($documentXml.NameTable)
$ns.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
$paragraphs = $documentXml.SelectNodes('//w:body/w:p', $ns)
$blankParagraphs = 0
$hardPageBreaks = 0
$pageBreakBefore = 0
$spacingViolations = 0
$fontViolations = 0
foreach ($paragraph in $paragraphs) {
    $textNodes = $paragraph.SelectNodes('.//w:t', $ns)
    $text = ($textNodes | ForEach-Object { $_.'#text' }) -join ''
    if ([string]::IsNullOrWhiteSpace($text)) { $blankParagraphs++ }
    $hardPageBreaks += $paragraph.SelectNodes('.//w:br[@w:type="page"]', $ns).Count
    $pageBreakBefore += $paragraph.SelectNodes('./w:pPr/w:pageBreakBefore', $ns).Count
    $spacing = $paragraph.SelectSingleNode('./w:pPr/w:spacing', $ns)
    if ($null -eq $spacing -or $spacing.GetAttribute('before', $ns.LookupNamespace('w')) -ne '0' -or $spacing.GetAttribute('after', $ns.LookupNamespace('w')) -ne '0') {
        $spacingViolations++
    }
    foreach ($run in $paragraph.SelectNodes('./w:r[w:t]', $ns)) {
        $runText = ($run.SelectNodes('./w:t', $ns) | ForEach-Object { $_.'#text' }) -join ''
        if ([string]::IsNullOrEmpty($runText)) { continue }
        $runPr = $run.SelectSingleNode('./w:rPr', $ns)
        $fonts = if ($null -ne $runPr) { $runPr.SelectSingleNode('./w:rFonts', $ns) } else { $null }
        $size = if ($null -ne $runPr) { $runPr.SelectSingleNode('./w:sz', $ns) } else { $null }
        $color = if ($null -ne $runPr) { $runPr.SelectSingleNode('./w:color', $ns) } else { $null }
        $asciiFont = if ($null -ne $fonts) { $fonts.GetAttribute('ascii', $ns.LookupNamespace('w')) } else { '' }
        $sizeValue = if ($null -ne $size) { $size.GetAttribute('val', $ns.LookupNamespace('w')) } else { '' }
        $colorValue = if ($null -ne $color) { $color.GetAttribute('val', $ns.LookupNamespace('w')) } else { '' }
        if ($asciiFont -ne 'Courier New' -or $sizeValue -ne '17' -or $colorValue -ne '000000') { $fontViolations++ }
    }
}
$txtBytes = [System.IO.File]::ReadAllBytes($TxtPath)
$hasBom = $txtBytes.Length -ge 3 -and $txtBytes[0] -eq 0xEF -and $txtBytes[1] -eq 0xBB -and $txtBytes[2] -eq 0xBF
$utf8 = [System.Text.UTF8Encoding]::new($false, $true)
$null = $utf8.GetString($txtBytes)
$txtLines = [System.IO.File]::ReadAllLines($TxtPath, $utf8)
$blankTxtLines = @($txtLines | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count
$backendPathPattern = '(?i)(^|[/\\])(backend|server|api|services?|domain|models?|repositories?|persistence|algorithms?|rules?|state|engines?)([/\\]|$)|算法|规则|状态机|领域|服务|模型|仓储|持久化|数据处理'
$frontendStyleStructurePattern = '(?i)\.(css|scss|sass|less|styl|html?|vue|jsx|tsx)$|(^|[/\\])(styles?|css|scss|less)([/\\]|$)'
$archiveHeaders = @($txtLines | Where-Object { $_.StartsWith('// 文件归档:') })
$uniqueArchiveHeaders = @($archiveHeaders | Sort-Object -Unique)
$frontendStyleStructureHeaders = @($archiveHeaders | Where-Object { $_ -match $frontendStyleStructurePattern })
$duplicateArchiveHeaders = $archiveHeaders.Count - $uniqueArchiveHeaders.Count
$detectedTotalSourceLines = 0
$detectedBackendSourceLines = 0
$currentIsBackend = $false
$backendPathPattern = '(?i)(^|[/\\])(backend|server|api|services?|domain|models?|repositories?|persistence|algorithms?|rules?|state|engines?)([/\\]|$)|算法|规则|状态机|领域|服务|模型|仓储|持久化|数据处理'
$frontendStyleStructurePattern = '(?i)\.(css|scss|sass|less|styl|html?|vue|jsx|tsx)$|(^|[/\\])(styles?|css|scss|less)([/\\]|$)'
foreach ($line in $txtLines) {
    if ($line.StartsWith('// 文件归档:')) {
        $archivePath = $line.Substring('// 文件归档:'.Length).Trim()
        $currentIsBackend = $archivePath -match $backendPathPattern
        continue
    }
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $detectedTotalSourceLines++
    if ($currentIsBackend) { $detectedBackendSourceLines++ }
}
$effectiveTotalSourceLines = if ($TotalSourceLines -gt 0) { $TotalSourceLines } else { $detectedTotalSourceLines }
$effectiveBackendSourceLines = if ($BackendSourceLines -gt 0) { $BackendSourceLines } else { $detectedBackendSourceLines }
$backendRatioPercent = if ($effectiveTotalSourceLines -gt 0) { [math]::Round(($effectiveBackendSourceLines / $effectiveTotalSourceLines) * 100, 2) } else { 0 }
$pageCount = $null
$measurement = $null
$application = $null
$document = $null
foreach ($progId in @('Word.Application', 'KWPS.Application')) {
    try {
        $type = [type]::GetTypeFromProgID($progId)
        if ($null -eq $type) { continue }
        $application = New-Object -ComObject $progId
        $application.Visible = $false
        $application.DisplayAlerts = 0
        $document = $application.Documents.Open($DocxPath, $false, $true)
        $document.Repaginate()
        $pageCount = [int]$document.ComputeStatistics(2)
        $measurement = $progId
        break
    } catch {
        if ($null -ne $document) { try { $document.Close($false) } catch {} }
        if ($null -ne $application) { try { $application.Quit() } catch {} }
        $document = $null
        $application = $null
    }
}
if ($null -ne $document) { try { $document.Close($false) } catch {} }
if ($null -ne $application) { try { $application.Quit() } catch {} }
[GC]::Collect()
[GC]::WaitForPendingFinalizers()
$result = [ordered]@{
    passed = $false
    minimum_pages = $MinimumPages
    backend_source_lines = $effectiveBackendSourceLines
    total_source_lines = $effectiveTotalSourceLines
    backend_ratio_percent = $backendRatioPercent
    minimum_backend_ratio_percent = $MinimumBackendRatioPercent
    measured_pages = $pageCount
    measurement = $measurement
    docx_paragraphs = $paragraphs.Count
    docx_blank_paragraphs = $blankParagraphs
    hard_page_breaks = $hardPageBreaks
    page_break_before = $pageBreakBefore
    spacing_violations = $spacingViolations
    font_violations = $fontViolations
    txt_lines = $txtLines.Count
    txt_blank_lines = $blankTxtLines
    txt_utf8_bom = $hasBom
    source_file_headers = $archiveHeaders.Count
    unique_source_file_headers = $uniqueArchiveHeaders.Count
    duplicate_source_file_headers = $duplicateArchiveHeaders
    frontend_style_structure_headers = $frontendStyleStructureHeaders.Count
    docx_txt_line_count_match = ($paragraphs.Count -eq $txtLines.Count)
}
$result.passed = (
    $pageCount -ge $MinimumPages -and
    $backendRatioPercent -ge $MinimumBackendRatioPercent -and
    $blankParagraphs -eq 0 -and
    $hardPageBreaks -eq 0 -and
    $pageBreakBefore -eq 0 -and
    $spacingViolations -eq 0 -and
    $fontViolations -eq 0 -and
    $blankTxtLines -eq 0 -and
    -not $hasBom -and
    $archiveHeaders.Count -gt 0 -and
    $duplicateArchiveHeaders -eq 0 -and
    $frontendStyleStructureHeaders.Count -eq 0 -and
    $paragraphs.Count -eq $txtLines.Count
)
$result | ConvertTo-Json -Depth 4
if (-not $result.passed) { exit 2 }
exit 0
