# Windows

Windows-only Micromium layer. Applied **after** the common `patches/` series.

## Contents

- `patches/SERIES` — Windows-only patches, applied in order:
  - `0001-windows-cet-cfg-sandbox.patch` — CET shadow-stack + CFG + strict
    sandbox job/token lockdown defaults.
  - `0002-windows-branding-installer.patch` — Micromium app ID
    (`micromium.browser.stable`) + installer defaults.
- `args.gn` — Windows x64 release GN args (mirrors `build/args/windows.gn`).
- `default_flags.json` — Windows launch switches on top of the common
  `patches/micromium_default_flags.json`.

## Apply

```powershell
# common + windows
python tools\apply_patches.py --src D:\chromium-src\src --patches patches
python tools\apply_patches.py --src D:\chromium-src\src --patches windows\patches
# or in one step:
python tools\apply_patches.py --src D:\chromium-src\src --patches patches --platform windows
```
