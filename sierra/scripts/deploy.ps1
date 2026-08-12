<#
.SYNOPSIS
    Deploy ACSIL study sources into a Sierra Chart ACS_Source folder.

.DESCRIPTION
    Copies every .cpp and .h in sierra/studies/ into the ACS_Source folder of a
    Sierra Chart installation. Afterwards, rebuild inside Sierra Chart:
    Analysis > Build Custom Studies DLL.

    There is deliberately NO default target. Sierra Chart installs somewhere
    different on every machine, so the target must come from one of:

      1. -Target <path>
      2. the OPTD_SC_ACS_SOURCE environment variable

    If neither is set the script stops and tells you how to set one. It never
    guesses a path.

    Finding ACS_Source: it sits directly inside your Sierra Chart installation
    folder, alongside Data\ and is the folder Sierra Chart compiles from when
    you open Analysis > Build Custom Studies DLL.

.PARAMETER Target
    Path to the Sierra Chart ACS_Source folder.

.PARAMETER WhatIf
    List what would be copied without writing anything.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1 -Target "<SierraChart>\ACS_Source"

.EXAMPLE
    $env:OPTD_SC_ACS_SOURCE = "<SierraChart>\ACS_Source"
    powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1 -WhatIf
#>
[CmdletBinding()]
param(
    [string]$Target,
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

# Resolve the source folder relative to this script, never from a fixed path,
# so the repo works wherever it is cloned.
$SierraDir = Split-Path -Parent $PSScriptRoot
$SourceDir = Join-Path $SierraDir 'studies'

if ([string]::IsNullOrWhiteSpace($Target)) {
    $Target = $env:OPTD_SC_ACS_SOURCE
}

if ([string]::IsNullOrWhiteSpace($Target)) {
    Write-Host "ERROR: no target ACS_Source folder specified." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Pass it explicitly:"
    Write-Host '    powershell -ExecutionPolicy Bypass -File sierra\scripts\deploy.ps1 -Target "<SierraChart>\ACS_Source"'
    Write-Host ""
    Write-Host "  Or set it once for the session:"
    Write-Host '    $env:OPTD_SC_ACS_SOURCE = "<SierraChart>\ACS_Source"'
    Write-Host ""
    Write-Host "  ACS_Source sits inside your Sierra Chart installation folder. It is the"
    Write-Host "  folder Analysis > Build Custom Studies DLL compiles from."
    exit 1
}

Write-Host "Source : $SourceDir"
Write-Host "Target : $Target"
Write-Host ""

if (-not (Test-Path -LiteralPath $SourceDir)) {
    Write-Host "ERROR: source folder not found: $SourceDir" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path -LiteralPath $Target)) {
    Write-Host "ERROR: target ACS_Source not found: $Target" -ForegroundColor Red
    Write-Host "       Check the path, or point -Target at the right Sierra Chart install." -ForegroundColor Red
    exit 1
}

$files = @(Get-ChildItem -LiteralPath $SourceDir -File | Where-Object { $_.Extension -in '.cpp', '.h' })

if ($files.Count -eq 0) {
    Write-Host "Nothing to deploy - no .cpp or .h files in sierra/studies/." -ForegroundColor Yellow
    exit 0
}

$copied = 0
foreach ($f in $files) {
    $dest = Join-Path $Target $f.Name
    if ($WhatIf) {
        Write-Host ("  WOULD COPY  {0,-34} {1,8} bytes" -f $f.Name, $f.Length)
    } else {
        Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
        Write-Host ("  deployed    {0,-34} {1,8} bytes" -f $f.Name, $f.Length)
        $copied++
    }
}

Write-Host ""
if ($WhatIf) {
    Write-Host "Dry run - nothing was written."
} else {
    Write-Host "Deployed $copied file(s) to $Target"
    Write-Host ""
    Write-Host "Next: in Sierra Chart -> Analysis > Build Custom Studies DLL > Build > OPTD_Studies"
    Write-Host "      Then on the chart -> Analysis > Studies > Add Custom Study."
    Write-Host "      A study already on the chart picks up new CODE on rebuild, but changed"
    Write-Host "      DEFAULTS/colors/draw styles only appear if you remove and re-add it."
}
