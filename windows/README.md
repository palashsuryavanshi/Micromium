# Windows

Self-contained Windows Micromium layer. No common patch directory — every
patch this platform needs lives in `windows/patches/`.

## Contents

- `patches/SERIES` — full patch stack, applied in order:
  - `0001`–`0005` — de-Google, telemetry/RLZ off, sandbox/CFI defaults,
    adblock wiring, privacy settings page (same files as the other platforms).
  - `0006-windows-cet-cfg-sandbox.patch` — CET shadow-stack + CFG + strict
    sandbox job/token lockdown defaults.
  - `0007-windows-branding-installer.patch` — Micromium app ID
    (`micromium.browser.stable`) + installer defaults.
  - `0008-windows-sdk-26100-compat.patch` — retargets the pinned
    28000 SDK / NTDDI_WIN11_BR at the public 26100 SDK so stock VS2022
    builds work (proven by a full local `chrome` build).
- `args.gn` — Windows x64 release GN args (mirrors `build/args/windows.gn`).
- `default_flags.json` — Windows launch switches.

## Apply

```powershell
python tools\apply_patches.py --src D:\chromium-src\src --patches windows\patches
# or:
python tools\apply_patches.py --src D:\chromium-src\src --platform windows
```
