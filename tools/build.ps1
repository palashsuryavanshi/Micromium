<#
.SYNOPSIS
  One-command Micromium configure + build for Windows / Linux / Android.
.EXAMPLE
  .\tools\build.ps1 -Platform windows -CheckoutDir D:\chromium-src
  .\tools\build.ps1 -Platform android -CheckoutDir D:\chromium-src
#>
param(
  [ValidateSet("windows", "linux", "android")]
  [string]$Platform = "windows",
  [string]$CheckoutDir = "D:\chromium-src",
  [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "== Micromium preflight =="
python "$RepoRoot\tools\verify.py"
if ($LASTEXITCODE -ne 0) { throw "verify.py failed — fix problems above first." }

$SrcDir = Join-Path $CheckoutDir "src"
if (!(Test-Path -LiteralPath (Join-Path $SrcDir "BUILD.gn"))) {
  throw "No Chromium checkout at $SrcDir. Run tools\fetch_chromium.ps1 first."
}

Write-Host "== Applying overlay =="
python "$RepoRoot\tools\apply_patches.py" --src $SrcDir --patches "$RepoRoot\patches"
if ($LASTEXITCODE -ne 0) { throw "patches failed — rebase needed." }
python "$RepoRoot\tools\apply_patches.py" --src $SrcDir --overlay
if ($LASTEXITCODE -ne 0) { throw "overlay copy failed." }

if ([string]::IsNullOrEmpty($OutDir)) {
  $OutDir = @{ windows = "out\Micromium"; linux = "out/Micromium"; android = "out/Micromium-Android" }[$Platform]
}
$Target = @{ windows = "micromium"; linux = "micromium"; android = "micromium_apk" }[$Platform]
$ArgsFile = "//micromium/build/args/$Platform.gn"

Push-Location $SrcDir
try {
  Write-Host "== gn gen $OutDir ($ArgsFile) =="
  & gn gen $OutDir --args="import(`"$ArgsFile`")"
  if ($LASTEXITCODE -ne 0) { throw "gn gen failed." }
  Write-Host "== autoninja $Target =="
  & autoninja -C $OutDir $Target
  if ($LASTEXITCODE -ne 0) { throw "build failed." }
} finally {
  Pop-Location
}
Write-Host "BUILD OK: $CheckoutDir\src\$OutDir"
