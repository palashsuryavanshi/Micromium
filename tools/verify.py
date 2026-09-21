#!/usr/bin/env python3
"""Micromium readiness check. Run before fetch/build. No network required.

Checks:
  - micromium.json pin present, VERSION matches layout
  - patches/SERIES entries exist on disk
  - JSON files parse
  - filter lists validate (same logic as update_filters --check)
  - build/args/*.gn present with required keys
  - C++ overlay sources present, BUILD.gn lists them
  - tools compile (py_compile of sibling scripts)

Usage: python tools/verify.py
Exit 0 = ready, 1 = problems found.
"""
import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fails: list[str] = []


def ok(msg: str):
    print(f"  ok: {msg}")


def fail(msg: str):
    print(f"FAIL: {msg}")
    fails.append(msg)


def check_json(path: Path):
    try:
        json.loads(path.read_text(encoding="utf-8"))
        ok(str(path.relative_to(ROOT)))
    except Exception as e:
        fail(f"{path.name} unparsable: {e}")


def main() -> int:
    print("== micromium.json / VERSION ==")
    try:
        cfg = json.loads((ROOT / "micromium.json").read_text())
        tag = cfg["chromium"]["tag"]
        ok(f"pinned to {tag}")
        if not tag[0].isdigit():
            fail(f"suspicious tag {tag!r}")
    except Exception as e:
        fail(f"micromium.json: {e}")
    if (ROOT / "VERSION").exists():
        ok(f"VERSION={(ROOT / 'VERSION').read_text().strip()}")
    else:
        fail("VERSION missing")
    if not (ROOT / "LICENSE").exists():
        fail("LICENSE missing")
    else:
        ok("LICENSE")

    print("== patches ==")
    series = ROOT / "patches" / "SERIES"
    if not series.exists():
        fail("patches/SERIES missing")
    else:
        for line in series.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = ROOT / "patches" / line
            if p.exists():
                ok(line)
            else:
                fail(f"SERIES entry missing on disk: {line}")
    check_json(ROOT / "patches" / "micromium_default_flags.json")

    print("== json ==")
    for f in ["micromium.json", "branding/BRANDING.json",
              "components/micromium_adblock/filter_lists/sources.json",
              "components/micromium_adblock/filter_lists/parity_vectors.json"]:
        check_json(ROOT / f)

    print("== filters ==")
    flist = ROOT / "components/micromium_adblock/filter_lists/micromium-default.txt"
    if not flist.exists():
        fail("micromium-default.txt missing")
    else:
        rules = [l.strip() for l in flist.read_text().splitlines()
                 if l.strip() and not l.startswith("!")]
        if rules:
            ok(f"{len(rules)} bundled rules")
        else:
            fail("bundled filter list is empty")

    print("== build args ==")
    for plat in ["windows", "linux", "android"]:
        f = ROOT / "build" / "args" / f"{plat}.gn"
        if not f.exists():
            fail(f"build/args/{plat}.gn missing")
            continue
        text = f.read_text()
        for key in ["is_official_build", "micromium_google_apis_enabled",
                    "micromium_hardened"]:
            if key not in text:
                fail(f"{plat}.gn missing {key}")
        else:
            ok(f"{plat}.gn")

    print("== adblock overlay ==")
    comp = ROOT / "components" / "micromium_adblock"
    for src in ["adblock_engine.h", "adblock_engine.cc",
                "adblock_dnr_bridge.h", "adblock_dnr_bridge.cc",
                "adblock_service.h", "adblock_service.cc",
                "rust_matcher.h", "rust_matcher.cc",
                "RUST_BACKEND.md", "BUILD.gn",
                "rust/Cargo.toml", "rust/src/lib.rs",
                "filter_lists/parity_vectors.json"]:
        if (comp / src).exists():
            ok(src)
        else:
            fail(f"component file missing: {src}")
    build_gn = (comp / "BUILD.gn").read_text()
    for src in ["adblock_dnr_bridge.cc", "adblock_service.cc",
                "rust_matcher.cc", "micromium_use_adblock_rust"]:
        if src not in build_gn:
            fail(f"BUILD.gn missing {src}")

    print("== chrome overlay (settings page) ==")
    chrome = ROOT / "chrome"
    for src in ["BUILD.gn", "README.md",
                "micromium_prefs.h", "micromium_prefs.cc",
                "adblock_service_factory.h", "adblock_service_factory.cc",
                "micromium_privacy_handler.h",
                "micromium_privacy_handler.cc",
                "resources/micromium_privacy.html",
                "resources/micromium_privacy.ts"]:
        if (chrome / src).exists():
            ok(src)
        else:
            fail(f"chrome overlay file missing: {src}")

    print("== parity vectors ==")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "parity_check.py")],
                       capture_output=True, text=True)
    print("".join(f"    {l}\n" for l in r.stdout.splitlines()))
    if r.returncode != 0:
        fail(f"parity_check.py failed:\n{r.stderr}")
    else:
        ok("parity_check.py")

    print("== tools ==")
    for t in ["tools/apply_patches.py", "tools/update_filters.py",
              "tools/parity_check.py",
              "tools/fetch_chromium.ps1", "tools/fetch_chromium.sh",
              "tools/build.ps1", "tools/build.sh"]:
        if (ROOT / t).exists():
            ok(t)
        else:
            fail(f"tool missing: {t}")
    try:
        for t in ["tools/apply_patches.py", "tools/update_filters.py",
                  "tools/parity_check.py", "tools/verify.py"]:
            py_compile.compile(str(ROOT / t), doraise=True)
        ok("python tools compile")
    except Exception as e:
        fail(f"py_compile: {e}")

    print()
    if fails:
        print(f"NOT READY: {len(fails)} problem(s)")
        return 1
    print("READY: all checks passed. Next: .\\tools\\fetch_chromium.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
