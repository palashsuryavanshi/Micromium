# Android

Android-only Micromium layer. Applied **after** the common `patches/` series.
Build on a Linux host.

## Contents

- `patches/SERIES` — Android-only patches, applied in order:
  - `0001-android-pac-bti-hardening.patch` — PAC/BTI guards + enforced CFI
    on arm64.
  - `0002-android-apk-branding.patch` — package `org.micromium.browser` +
    WebLayer DNR adblock wiring.
- `args.gn` — Android arm64 release GN args (mirrors `build/args/android.gn`).
- `default_flags.json` — Android launch switches on top of the common
  `patches/micromium_default_flags.json`, plus the package name.

## Apply

```bash
# common + android
python3 tools/apply_patches.py --src ~/chromium-src/src --patches patches
python3 tools/apply_patches.py --src ~/chromium-src/src --patches android/patches
# or in one step:
python3 tools/apply_patches.py --src ~/chromium-src/src --patches patches --platform android
```
