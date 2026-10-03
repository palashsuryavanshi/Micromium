# Android

Self-contained Android Micromium layer. No common patch directory — every
patch this platform needs lives in `android/patches/`. Build on a Linux host.

## Contents

- `patches/SERIES` — full patch stack, applied in order:
  - `0001`–`0005` — de-Google, telemetry/RLZ off, sandbox/CFI defaults,
    adblock wiring, privacy settings page (same files as the other platforms).
  - `0006-android-pac-bti-hardening.patch` — PAC/BTI guards + enforced CFI
    on arm64.
  - `0007-android-apk-branding.patch` — package `org.micromium.browser` +
    WebLayer DNR adblock wiring.
- `args.gn` — Android arm64 release GN args (mirrors `build/args/android.gn`).
- `default_flags.json` — Android launch switches, plus the package name.

## Apply

```bash
python3 tools/apply_patches.py --src ~/chromium-src/src --patches android/patches
# or:
python3 tools/apply_patches.py --src ~/chromium-src/src --platform android
```
