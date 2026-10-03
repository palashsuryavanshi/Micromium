# Linux

Self-contained Linux Micromium layer. No common patch directory — every
patch this platform needs lives in `linux/patches/`.

## Contents

- `patches/SERIES` — full patch stack, applied in order:
  - `0001`–`0005` — de-Google, telemetry/RLZ off, sandbox/CFI defaults,
    adblock wiring, privacy settings page (same files as the other platforms).
  - `0006-linux-seccomp-vaapi.patch` — strict seccomp-bpf + VAAPI decode.
  - `0007-linux-branding-desktop.patch` — `micromium-browser.desktop`
    + Micromium branding.
- `args.gn` — Linux x64 release GN args (mirrors `build/args/linux.gn`).
- `default_flags.json` — Linux launch switches.

## Apply

```bash
python3 tools/apply_patches.py --src ~/chromium-src/src --patches linux/patches
# or:
python3 tools/apply_patches.py --src ~/chromium-src/src --platform linux
```
