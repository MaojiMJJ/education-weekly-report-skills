param(
    [Parameter(Mandatory = $true)]
    [string]$InputPptx,

    [Parameter(Mandatory = $true)]
    [string]$OutputPdf
)

$inputPath = [System.IO.Path]::GetFullPath($InputPptx)
$outputPath = [System.IO.Path]::GetFullPath($OutputPdf)

if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
    throw "PPTX does not exist: $inputPath"
}

$outputDirectory = [System.IO.Path]::GetDirectoryName($outputPath)
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($inputPath, $true, $false, $false)
    # ppSaveAsPDF = 32. SaveAs is more stable than the overloaded
    # ExportAsFixedFormat method across Windows PowerShell COM binding versions.
    $presentation.SaveAs($outputPath, 32)
}
finally {
    if ($presentation) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    if ($powerPoint) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
    throw "PowerPoint PDF export failed: $outputPath"
}

Get-Item -LiteralPath $outputPath
