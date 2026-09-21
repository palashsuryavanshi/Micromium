# Building Micromium

Full Chromium builds are heavy. Minimum recommended:

- Windows 10/11 64-bit, VS2022 17.x, 10.0.22621 SDK, 32GB RAM, 150GB free on D:
- Ubuntu 22.04+ for Linux/Android builds, 32GB RAM, 150GB free
- depot_tools in PATH, Python 3.8+, Node 18+ (for some tools)
- Android: JDK 17, Android SDK + NDK r26+ (installed via `build/android`)

Do NOT `git clone https://github.com/chromium/chromium`. That mirror lacks
DEPS history and submodules (v8, skia, etc). Use gclient.

## 1. Install depot_tools

Windows (PowerShell, run from this repo):

```powershell
.\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src -SetupOnly
# then restart shell so PATH includes depot_tools
```

Linux:

```bash
./tools/fetch_chromium.sh --checkout-dir ~/chromium-src --setup-only
```

## 2. Sync Chromium at pinned tag

Pin comes from `micromium.json` (`153.0.8010.27`).

```powershell
.\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src
```

This creates `D:\chromium-src\src` via `gclient sync --revision src@<tag>`.
Expect 30-80GB and 30min-3h depending on network/disk.

## 3. Apply Micromium patches + overlay

```powershell
python tools\apply_patches.py --src D:\chromium-src\src --patches patches
python tools\apply_patches.py --src D:\chromium-src\src --overlay
```

This:
- applies every patch in `patches/SERIES` with `git apply`
- copies `components/micromium_adblock` -> `src/micromium/components/...`
- copies `branding/*` -> `src/micromium/branding/`
- copies `build/args/*.gn` -> `src/micromium/build/args/`

## 4. Build

Windows x64:

```powershell
cd D:\chromium-src\src
gn gen out\Micromium --args='import("//micromium/build/args/windows.gn")'
autoninja -C out\Micromium micromium
```

Linux x64:

```bash
gn gen out/Micromium --args='import("//micromium/build/args/linux.gn")'
autoninja -C out/Micromium micromium
```

Android arm64 (from Linux host):

```bash
gn gen out/Micromium-Android --args='import("//micromium/build/args/android.gn")'
autoninja -C out/Micromium-Android micromium_apk
```

Artifacts land in `out/.../`. Install/run per-platform as normal Chromium.

## Troubleshooting

- `gn: command not found` -> depot_tools not in PATH, reopen shell.
- Patch fails after version bump -> `git apply --reject` output tells you the
  hunk; rebase manually, regenerate patch with `git diff > patches/xxxx.patch`.
- Link OOM on 16GB machines -> set `jumbo_build=false`, `symbol_level=0`,
  close browsers/AV, use `autoninja -j4`.
- Android SDK missing -> run `build/android/envsetup.sh` once.
