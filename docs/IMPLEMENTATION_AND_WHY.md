# Micromium: How to Implement It and Why to Use It With Chromium

## Part 1 — Why use Micromium with Chromium (instead of vanilla Chromium)

### 1. Vanilla Chromium is a raw engine, not a finished browser base
Upstream Chromium gives you Blink + V8 + content shell, but the defaults are
tuned for Google's products: baked-in Google API keys, metrics/UMA upload,
crash-report pingbacks, RLZ tracking, Translate/OptimizationHints calling
home, and field-trial fetches on first run. Every downstream browser
(Brave, Edge, Ungoogled-Chromium) strips or replaces these. Micromium does
that work for you in `patches/0001` + `0002`, with the kill-switch list in
`patches/micromium_default_flags.json`:
`--disable-background-networking --disable-metrics-reporting
--no-report-upload --disable-rlz --disable-domain-reliability
--disable-breakpad`.

### 2. Overlay model: you never fork 40GB of code
A full Chromium checkout is 30–80GB with ~1.8M commits. Forking it means
you own every rebase conflict forever. Micromium keeps **zero** upstream
files in this repo. It pins one stable tag (`micromium.json`,
`153.0.8010.27`) and keeps only:
- `patches/` — small diffs rebased per milestone,
- `components/micromium_adblock/` — your own code,
- `build/args/` — your GN configs,
- `branding/` — your identity.
Updating to a new Chromium milestone = bump the tag, re-run the sync,
fix only the patches that reject. Ungoogled-Chromium and Brave work the
same way, and it is the only sustainable model.

### 3. Built-in adblock where it belongs: the network service
Extensions can be disabled, fingerprinted, or MV3-limited. Micromium's
`AdblockService` (`components/micromium_adblock/adblock_service.{h,cc}`)
loads EasyList/EasyPrivacy and emits `declarativeNetRequest` dynamic rules
via `adblock_dnr_bridge.{h,cc}`, so blocking happens **before** the network
request leaves the browser process. No extension install, works on
Windows/Linux/Android identically, and `tools/update_filters.py` refreshes
lists from `filter_lists/sources.json` with a 30k-rule DNR cap guard.

### 4. Performance + hardening presets, not tribal knowledge
`build/args/windows.gn`, `linux.gn`, `android.gn` encode what experienced
Chromium embedders learn the hard way: `is_official_build=true`,
ThinLTO, PartitionAlloc, `use_cfi=true`, CET/CFG on Windows, PAC/BTI on
ARM64 Android, RLZ/Google APIs compiled out. One import line replaces pages
of wiki-reading, and `patches/0003` flips the sandbox defaults so even a
plain `gn gen` stays hardened.

### 5. Reproducible pipeline: verify → fetch → patch → build
`tools/verify.py` (no network) proves the overlay is sane.
`tools/fetch_chromium.*` syncs the exact pinned tag via `depot_tools`.
`tools/apply_patches.py` applies + copies the overlay to `src/micromium/`.
`tools/build.ps1` / `build.sh` chain all of it. Any machine that runs
`verify.py` green will produce the same browser.

## Part 2 — Detailed implementation instructions

### Prerequisites
- Windows 10/11 64-bit (VS2022 + SDK 10.0.22621) **or** Ubuntu 22.04+.
- 32GB RAM recommended, **150GB free** (Chromium needs it; this repo is KBs).
- Git, Python 3.8+, Node 18+. Android builds additionally need JDK 17 +
  SDK/NDK r26+ (`src/build/android/envsetup.sh` installs them post-sync).
- Never `git clone https://github.com/chromium/chromium` — the GitHub
  mirror lacks DEPS submodules (V8, Skia) and cannot build.

### Step 0 — Clone this repo and verify
```powershell
git clone https://github.com/<you>/Micromium.git
cd Micromium
python tools\verify.py   # expect: READY: all checks passed
```

### Step 1 — Fetch upstream Chromium at the pinned tag
```powershell
.\tools\fetch_chromium.ps1 -CheckoutDir D:\chromium-src
```
What happens: clones `depot_tools`, writes a minimal `.gclient` pointing at
`chromium.googlesource.com/chromium/src`, then
`gclient sync --revision src@153.0.8010.27`. Takes 30min–3h, 30–80GB.
Linux/Android hosts: `./tools/fetch_chromium.sh --checkout-dir ~/chromium-src`.

### Step 2 — Apply Micromium patches + overlay
```powershell
python tools\apply_patches.py --src D:\chromium-src\src --patches patches --overlay
```
What happens: `git apply` for each entry in `patches/SERIES` in order
(0001 de-Google, 0002 telemetry/RLZ, 0003 sandbox/CFI, 0004 adblock wiring),
then copies `components/micromium_adblock` → `src/micromium/components/`,
`build/args` → `src/micromium/build/args/`, `branding/` and flags JSON.
If a patch FAILs after you bump the Chromium tag, open the `.rej`, fix the
hunk in the checkout, regenerate with `git diff > patches/000x-....patch`.

### Step 3 — Refresh filter lists (optional but recommended)
```powershell
python tools\update_filters.py --fetch --check
git diff --stat   # review what EasyList changed before committing
```
Merges EasyList + EasyPrivacy per `filter_lists/sources.json` into
`micromium-default.txt` plus a reviewable `dnr_snapshot.json`.

### Step 4 — Build (one command)
```powershell
.\tools\build.ps1 -Platform windows -CheckoutDir D:\chromium-src
# linux:   ./tools/build.sh --platform linux --checkout-dir ~/chromium-src
# android: ./tools/build.sh --platform android --checkout-dir ~/chromium-src
#   (android must run on a Linux host)
```
What happens: re-runs `verify.py`, re-applies overlay (idempotent),
`gn gen out/Micromium --args='import("//micromium/build/args/windows.gn")'`,
`autoninja -C out/Micromium micromium` (or `micromium_apk` on Android).

### Step 5 — Run and iterate
- Windows/Linux: `D:\chromium-src\src\out\Micromium\micromium.exe --enable-features=MicromiumAdblock`
- Android: `autoninja -C out/Micromium-Android install_micromium_apk` then launch `org.micromium.browser`.
- Toggle work-in-progress UI at `chrome://flags/#micromium-adblock`
  (full `chrome://settings/micromium-privacy` WebUI is the next milestone).
- Local adblock loop without building: edit `micromium-default.txt`,
  run `update_filters.py --check`, unit-test `:unit_tests`.

### Step 6 — Updating the Chromium base (every 2–4 weeks)
1. Check https://chromereleases.googleblog.com for the new Stable tag.
2. Bump `micromium.json` → `chromium.tag` (+ `VERSION` if behavior changed).
3. Re-run fetch + apply; fix rejected patches; run `verify.py`.
4. Commit overlay changes, tag `micromium-vX.Y`, push.

### Troubleshooting
| Symptom | Fix |
|---|---|
| `gn: command not found` | `depot_tools` not in PATH — reopen shell |
| Patch FAILs | Rebase that one file, regenerate the `.patch` |
| Link OOM (16GB RAM) | `symbol_level=0`, `autoninja -j4`, close browsers/AV |
| Android SDK missing | Run `src/build/android/envsetup.sh` once |
| CRLF corrupt patches | `git config core.autocrlf false`, `.gitattributes` already forces LF |
