param(
    [Parameter(Mandatory = $true)]
    [string]$InputJson,

    [Parameter(Mandatory = $true)]
    [string]$Output,

    [Parameter(Mandatory = $true)]
    [string]$SourcesOutput,

    [Parameter(Mandatory = $true)]
    [string]$QualityOutput,

    [Parameter(Mandatory = $true)]
    [string]$SlidesSkillDir,

    [string]$ScratchDir,
    [string]$PythonPath = "python",
    [string]$NodePath = "node"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$layout = Join-Path $skillDir "assets\colleague-template\layout.json"
$cover = Join-Path $skillDir "assets\colleague-template\cover.jpg"
$validator = Join-Path $scriptDir "report_quality.py"
$builderSource = Join-Path $scriptDir "build_biweekly_pptx.mjs"
$setupScript = Join-Path $SlidesSkillDir "container_tools\setup_artifact_tool_workspace.mjs"

if (-not (Test-Path -LiteralPath $InputJson)) {
    throw "Input JSON not found: $InputJson"
}
foreach ($required in @($layout, $cover, $validator, $builderSource, $setupScript)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required file not found: $required"
    }
}

if (-not $ScratchDir) {
    $ScratchDir = Join-Path ([System.IO.Path]::GetTempPath()) ("education-biweekly-" + [guid]::NewGuid().ToString("N"))
}
New-Item -ItemType Directory -Path $ScratchDir -Force | Out-Null

$outputDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($Output))
$sourcesDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($SourcesOutput))
$qualityDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($QualityOutput))
foreach ($directory in @($outputDir, $sourcesDir, $qualityDir)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

& $PythonPath $validator $InputJson --layout $layout --sources-output $SourcesOutput --quality-output $QualityOutput
if ($LASTEXITCODE -ne 0) {
    throw "Report JSON failed the fixed-template quality gate."
}

$previousLocation = Get-Location
try {
    if ($env:USERPROFILE -and (Test-Path -LiteralPath $env:USERPROFILE)) {
        Set-Location -LiteralPath $env:USERPROFILE
    }
    & $NodePath $setupScript --workspace $ScratchDir
}
finally {
    Set-Location -LiteralPath $previousLocation.Path
}
if ($LASTEXITCODE -ne 0) {
    throw "Failed to initialize the artifact-tool workspace."
}

$builderRuntime = Join-Path $ScratchDir "build_biweekly_pptx.mjs"
Copy-Item -LiteralPath $builderSource -Destination $builderRuntime -Force
$qaDir = Join-Path $ScratchDir "qa"

& $NodePath $builderRuntime --input $InputJson --layout $layout --cover $cover --output $Output --qa-dir $qaDir
if ($LASTEXITCODE -ne 0) {
    throw "Failed to build the fixed-template PPTX."
}

Write-Output "Written: $Output"
Write-Output "Written: $SourcesOutput"
Write-Output "Written: $QualityOutput"
Write-Output "QA preview: $qaDir"
