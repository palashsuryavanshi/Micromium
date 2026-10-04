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

# Visual Studio detection (Chromium's vs_toolchain only probes default paths
# plus $env:vs2022_install, so resolve custom locations via vswhere first).
# Honors a pre-set vs2022_install / GYP_MSVS_OVERRIDE_PATH if the caller
# already exported them.
if ($Platform -eq "windows" -and [string]::IsNullOrEmpty($env:vs2022_install)) {
  $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
  if (Test-Path -LiteralPath $vswhere) {
    $vsPath = & $vswhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1
    if ($vsPath) {
      $env:vs2022_install = $vsPath
      Write-Host "Detected VS2022 at $vsPath"
    }
  }
  if ([string]::IsNullOrEmpty($env:vs2022_install)) {
    Write-Warning "No VS2022 with MSVC found via vswhere; set `$env:vs2022_install manually."
  }
}
if ($Platform -eq "windows") {
  $env:DEPOT_TOOLS_WIN_TOOLCHAIN = "0"
  if (-not [string]::IsNullOrEmpty($env:vs2022_install) -and [string]::IsNullOrEmpty($env:GYP_MSVS_OVERRIDE_PATH)) {
    $env:GYP_MSVS_OVERRIDE_PATH = $env:vs2022_install
  }
}

Write-Host "== Micromium preflight =="
python "$RepoRoot\tools\verify.py"
if ($LASTEXITCODE -ne 0) { throw "verify.py failed -- fix problems above first." }

$SrcDir = Join-Path $CheckoutDir "src"
if (!(Test-Path -LiteralPath (Join-Path $SrcDir "BUILD.gn"))) {
  throw "No Chromium checkout at $SrcDir. Run tools\fetch_chromium.ps1 first."
}

Write-Host "== Applying $Platform patches + overlay =="
python "$RepoRoot\tools\apply_patches.py" --src $SrcDir --platform $Platform --overlay
if ($LASTEXITCODE -ne 0) { throw "patches failed -- rebase needed." }

if ([string]::IsNullOrEmpty($OutDir)) {
  $OutDir = @{ windows = "out\Micromium"; linux = "out/Micromium"; android = "out/Micromium-Android" }[$Platform]
}
# Upstream target names (verified against Chromium 153.0.8010.27):
#   windows/linux desktop browser -> chrome
#   android APK                   -> chrome_public_apk
$Target = @{ windows = "chrome"; linux = "chrome"; android = "chrome_public_apk" }[$Platform]
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
