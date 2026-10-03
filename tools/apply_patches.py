#!/usr/bin/env python3
"""Applies Micromium patches + overlay onto a Chromium checkout.

Each platform is self-contained: windows/patches, android/patches,
linux/patches each hold that platform's FULL patch stack (SERIES order).

Usage:
  python tools/apply_patches.py --src D:\\chromium-src\\src --platform windows --overlay
  python tools/apply_patches.py --src D:\\chromium-src\\src --patches windows/patches --overlay

--platform: one of windows, android, linux. Applies <platform>/patches/SERIES.
--patches: explicit patch dir (e.g. windows/patches). Overrides --platform.
--overlay: copy components/micromium_adblock, chrome/, build/args, branding
           plus the platform's default_flags.json into <src>/micromium/...
           (--platform selects which flags file; defaults to windows).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("windows", "android", "linux")


def run(cmd, cwd):
    print(f"+ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
    return r


def apply_patches(src: Path, patches_dir: Path) -> bool:
    series = patches_dir / "SERIES"
    if not series.exists():
        print(f"SERIES not found: {series}", file=sys.stderr)
        return False
    ok = True
    for line in series.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patch = patches_dir / line
        if not patch.exists():
            print(f"Missing patch: {patch}", file=sys.stderr)
            ok = False
            continue
        r = run(["git", "apply", "--whitespace=fix", str(patch)], cwd=src)
        if r.returncode != 0:
            print(f"FAILED: {line} — rebase needed (see git apply output above)")
            ok = False
        else:
            print(f"Applied: {line}")
    return ok


def copy_overlay(src: Path, platform: str | None):
    dest_root = src / "micromium"
    mappings = [
        (REPO_ROOT / "components" / "micromium_adblock",
         dest_root / "components" / "micromium_adblock"),
        (REPO_ROOT / "chrome",
         dest_root / "chrome"),
        (REPO_ROOT / "build" / "args",
         dest_root / "build" / "args"),
        (REPO_ROOT / "branding",
         dest_root / "branding"),
    ]
    if platform in PLATFORMS:
        mappings.append(
            (REPO_ROOT / platform / "default_flags.json",
             dest_root / "micromium_default_flags.json"),
        )
    for src_path, dst_path in mappings:
        if not src_path.exists():
            print(f"Skip missing overlay source: {src_path}")
            continue
        if src_path.is_file():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"Copied file {src_path.name} -> {dst_path}")
        else:
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            print(f"Copied dir {src_path} -> {dst_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to Chromium src/ dir")
    ap.add_argument("--patches",
                    help="Explicit patch dir (e.g. windows/patches). Overrides --platform.")
    ap.add_argument("--platform", choices=list(PLATFORMS),
                    help="Apply <platform>/patches/SERIES (full per-platform stack)")
    ap.add_argument("--overlay", action="store_true", help="Copy overlay files")
    args = ap.parse_args()

    src = Path(args.src)
    if not (src / "BUILD.gn").exists():
        print(f"Does not look like Chromium src/: {src}", file=sys.stderr)
        sys.exit(2)

    patches_dir: Path | None = None
    if args.patches:
        patches_dir = Path(args.patches)
        if not patches_dir.is_absolute():
            patches_dir = (Path.cwd() / patches_dir).resolve()
    elif args.platform:
        patches_dir = REPO_ROOT / args.platform / "patches"

    failed = False
    if patches_dir is not None:
        if not apply_patches(src, patches_dir):
            failed = True
    elif args.overlay:
        pass  # overlay-only run
    else:
        print("Nothing to do: pass --platform <windows|android|linux> or --patches <dir>.",
              file=sys.stderr)
        sys.exit(2)
    if args.overlay:
        copy_overlay(src, args.platform)

    if failed:
        print("Some patches FAILED — fix them manually, then re-run.", file=sys.stderr)
        sys.exit(1)
    print("Micromium overlay applied OK.")


if __name__ == "__main__":
    main()
