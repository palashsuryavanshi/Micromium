# Micromium — Better Chromium Base

Overlay-based custom browser base built on top of upstream Chromium.
We do **NOT** vendor full Chromium source here (it's ~40GB+ with history).
Instead this repo pins a stable Chromium tag and applies Micromium patches,
branding, and build configs on top — like Brave / Ungoogled-Chromium do.

> Base pin: `153.0.8010.27` (Stable, Sep 2026, branch 1681091)
> Upstream: https://github.com/chromium/chromium
> Targets: Windows (x64), Linux (x64), Android (arm64)

## Why better than vanilla Chromium?

1. **Privacy / de-Google** — disables telemetry, RLZ, field-trial pingbacks,
   Google service keys by default. See `<platform>/patches/0001-0002`.
2. **Built-in adblock** — native `MicromiumAdblock` component using
   Brave-style adblock-rust compatible filter lists + `declarativeNetRequest`.
   See `components/micromium_adblock/`.
3. **Performance** — PGO ThinLTO, `is_official_build=true`, partition-alloc
   tweaks, aggressive discards. See `build/args/`.
4. **Security hardening** — CET/CFG on Windows, PAC/BTI on ARM64 Android,
   `use_cfi=true`, hardened mojo/sandbox flags. See `build/args/`.

## Layout

```
VERSION                     # overlay version (0.3.0)
micromium.json              # version pin + feature toggles (single source of truth)
tools/verify.py             # readiness check — run this first
tools/fetch_chromium.ps1    # Windows: installs depot_tools, gclient syncs Chromium
tools/fetch_chromium.sh     # Linux: same for Linux/Android builds
tools/apply_patches.py      # applies <platform>/patches SERIES onto src/ (+ --overlay)
tools/update_filters.py     # merges EasyList/EasyPrivacy -> bundled list + DNR JSON
tools/parity_check.py       # proves fallback matcher meets parity_vectors.json
tools/build.ps1 / build.sh  # one-command verify + patch + gn gen + autoninja
windows/                    # full Windows stack: patches/0001-0007 + args.gn + flags
android/                    # full Android stack: patches/0001-0007 + args.gn + flags
linux/                      # full Linux stack: patches/0001-0007 + args.gn + flags
components/micromium_adblock/ # engine + DNR bridge + service + rust/ backend + filter_lists/
chrome/                     # prefs + adblock factory + privacy WebUI handler + resources/
build/args/                 # windows.gn, linux.gn, android.gn
branding/                   # product name, icons placeholder
docs/BUILDING.md            # full build instructions
```

## Ready to use

```powershell
# 0. Sanity check (no network needed)
python tools\verify.py

# 1. Fetch upstream Chromium at pinned tag (~30-100GB, takes a while)
.\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src

# 2. One-command build (re-runs verify, applies patches+overlay, builds)
.\tools\build.ps1 -Platform windows -CheckoutDir D:\chromium-src
# .\tools\build.ps1 -Platform android -CheckoutDir D:\chromium-src
```

See `docs/BUILDING.md` for Linux / Android and troubleshooting.

## Quick start (manual steps — or just use tools/build.ps1)

```powershell
# 1. Fetch upstream Chromium at pinned tag (~30-100GB, takes a while)
.\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src

# 2. Apply Micromium patches (pick your platform — no common dir)
python tools\apply_patches.py --src D:\chromium-src\src --platform windows --overlay

# 3. Configure + build (example: Windows release)
cd D:\chromium-src\src
gn gen out\Micromium --args="import(\"//micromium/build/args/windows.gn\")"
autoninja -C out\Micromium micromium
```

See `docs/BUILDING.md` for Linux / Android.

## Updating the base

1. Bump `micromium.json` -> `chromium.tag`
2. Run `tools/fetch_chromium.*` again
3. Rebase `<platform>/patches/` if any fail, update that platform's `SERIES`
   (keep the 0001-0005 baseline identical across windows/android/linux)
4. Tag `micromium-vX.Y` in this repo

## License

BSD-3-Clause (same as Chromium). Patches retain upstream headers.
