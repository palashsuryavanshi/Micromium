#!/bin/bash
# Fetches upstream Chromium at the Micromium-pinned stable tag (Linux host,
# also used for Android builds).
# Usage:
#   ./tools/fetch_chromium.sh --checkout-dir ~/chromium-src
#   ./tools/fetch_chromium.sh --checkout-dir ~/chromium-src --setup-only
set -euo pipefail

CHECKOUT_DIR="$HOME/chromium-src"
TAG="153.0.8010.27"
SETUP_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --checkout-dir) CHECKOUT_DIR="$2"; shift 2 ;;
    --tag) TAG="$2"; shift 2 ;;
    --setup-only) SETUP_ONLY=1; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

DEPOT_TOOLS_DIR="$CHECKOUT_DIR/depot_tools"

if [[ ! -d "$DEPOT_TOOLS_DIR" ]]; then
  echo "Cloning depot_tools ..."
  mkdir -p "$CHECKOUT_DIR"
  git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$DEPOT_TOOLS_DIR"
else
  echo "Updating depot_tools ..."
  git -C "$DEPOT_TOOLS_DIR" pull --ff-only
fi

export PATH="$DEPOT_TOOLS_DIR:$PATH"
echo "depot_tools ready. Add to PATH permanently: export PATH=\"$DEPOT_TOOLS_DIR:\$PATH\""

if [[ "$SETUP_ONLY" -eq 1 ]]; then
  echo "SetupOnly: skipping gclient sync."
  exit 0
fi

# build deps for Linux/Android (needs sudo once)
if command -v apt-get >/dev/null 2>&1; then
  echo "Installing Chromium build deps (may prompt for sudo) ..."
  "$DEPOT_TOOLS_DIR/ninja" --version >/dev/null 2>&1 || true
fi

if [[ ! -d "$CHECKOUT_DIR/src" ]]; then
  echo "First sync — fetching Chromium $TAG ..."
  mkdir -p "$CHECKOUT_DIR/src"
  cat > "$CHECKOUT_DIR/.gclient" <<EOF
solutions = [
  {
    'name': 'src',
    'url': 'https://chromium.googlesource.com/chromium/src.git',
    'managed': False,
    'custom_deps': {},
    'custom_vars': {},
  },
]
EOF
  (cd "$CHECKOUT_DIR" && gclient sync --revision "src@$TAG" --with_branch_heads --with_tags -j8)
else
  echo "Existing checkout found, syncing to $TAG ..."
  (cd "$CHECKOUT_DIR" && gclient sync --revision "src@$TAG" -D -j8)
fi

echo ""
echo "Done. Next:"
echo "  python3 tools/apply_patches.py --src $CHECKOUT_DIR/src --patches patches"
echo "  python3 tools/apply_patches.py --src $CHECKOUT_DIR/src --overlay"
