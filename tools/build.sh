#!/bin/bash
# One-command Micromium configure + build for linux / android.
# Usage: ./tools/build.sh --platform linux --checkout-dir ~/chromium-src
set -euo pipefail

PLATFORM="linux"
CHECKOUT_DIR="$HOME/chromium-src"
OUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --checkout-dir) CHECKOUT_DIR="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "== Micromium preflight =="
python3 "$REPO_ROOT/tools/verify.py"

SRC_DIR="$CHECKOUT_DIR/src"
if [[ ! -f "$SRC_DIR/BUILD.gn" ]]; then
  echo "No Chromium checkout at $SRC_DIR. Run tools/fetch_chromium.sh first." >&2
  exit 2
fi

echo "== Applying overlay =="
python3 "$REPO_ROOT/tools/apply_patches.py" --src "$SRC_DIR" --patches "$REPO_ROOT/patches"
python3 "$REPO_ROOT/tools/apply_patches.py" --src "$SRC_DIR" --overlay

if [[ -z "$OUT_DIR" ]]; then
  case "$PLATFORM" in
    windows) OUT_DIR="out/Micromium" ;;
    android) OUT_DIR="out/Micromium-Android" ;;
    *) OUT_DIR="out/Micromium" ;;
  esac
fi
case "$PLATFORM" in
  android) TARGET="micromium_apk" ;;
  *) TARGET="micromium" ;;
esac

cd "$SRC_DIR"
echo "== gn gen $OUT_DIR =="
gn gen "$OUT_DIR" --args="import(\"//micromium/build/args/$PLATFORM.gn\")"
echo "== autoninja $TARGET =="
autoninja -C "$OUT_DIR" "$TARGET"
echo "BUILD OK: $SRC_DIR/$OUT_DIR"
