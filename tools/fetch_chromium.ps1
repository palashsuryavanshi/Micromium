<#
.SYNOPSIS
  Fetches upstream Chromium at the Micromium-pinned stable tag.
.DESCRIPTION
  Installs depot_tools (if missing) and runs gclient sync. Does NOT use
  `git clone https://github.com/chromium/chromium` — that mirror cannot build.
.EXAMPLE
  .\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src
  .\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src -SetupOnly
#>
param(
  [string]$CheckoutDir = "D:\chromium-src",
  [switch]$SetupOnly,
  [string]$Tag = "153.0.8010.27"
)

$ErrorActionPreference = "Stop"
$DepotToolsDir = Join-Path $CheckoutDir "depot_tools"

function Ensure-DepotTools {
  if (!(Test-Path -LiteralPath $DepotToolsDir)) {
    Write-Host "Cloning depot_tools to $DepotToolsDir ..."
    New-Item -ItemType Directory -Force -Path $CheckoutDir | Out-Null
    & git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git $DepotToolsDir
  } else {
    Write-Host "depot_tools already present, updating ..."
    & git -C $DepotToolsDir pull --ff-only
  }
  $env:PATH = "$DepotToolsDir;$env:PATH"
  $env:DEPOT_TOOLS_WIN_TOOLCHAIN = "0"
}

Ensure-DepotTools
Write-Host "depot_tools ready. Ensure it stays in PATH for gn/ninja/gclient."

if ($SetupOnly) {
  Write-Host "SetupOnly: skipping gclient sync. Restart shell, then re-run without -SetupOnly."
  exit 0
}

$SrcDir = Join-Path $CheckoutDir "src"
if (!(Test-Path -LiteralPath $SrcDir)) {
  Write-Host "First sync — fetching Chromium $Tag (30-80GB, be patient) ..."
  New-Item -ItemType Directory -Force -Path $SrcDir | Out-Null
  Push-Location $CheckoutDir
  try {
    # Minimal .gclient pointing at upstream src + tag revision
    @"
solutions = [
  {
    'name': 'src',
    'url': 'https://chromium.googlesource.com/chromium/src.git',
    'managed': False,
    'custom_deps': {},
    'custom_vars': {},
  },
]
"@ | Set-Content -NoNewline -Path (Join-Path $CheckoutDir ".gclient")
    & gclient sync --revision "src@$Tag" --with_branch_heads --with_tags -j8
  } finally {
    Pop-Location
  }
} else {
  Write-Host "Existing checkout found, syncing to $Tag ..."
  Push-Location $CheckoutDir
  try {
    & gclient sync --revision "src@$Tag" -D -j8
  } finally {
    Pop-Location
  }
}

Write-Host ""
Write-Host "Done. Next:"
Write-Host "  python tools\apply_patches.py --src $SrcDir --patches patches"
Write-Host "  python tools\apply_patches.py --src $SrcDir --overlay"
