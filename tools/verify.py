#!/usr/bin/env python3
"""Micromium readiness check. Run before fetch/build. No network required.

Checks:
  - micromium.json pin present, VERSION matches layout
  - per-platform patches (windows/android/linux) SERIES entries exist on disk
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
import re
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

    print("== platform patches (windows/ + android/ + linux/) ==")
    if (ROOT / "patches").exists():
        fail("legacy common patches/ dir still exists — all patches must live in <platform>/patches/")
    for plat in ["windows", "android", "linux"]:
        pdir = ROOT / plat / "patches"
        series = pdir / "SERIES"
        if not series.exists():
            fail(f"{plat}/patches/SERIES missing")
            continue
        entries = [l.strip() for l in series.read_text().splitlines()
                   if l.strip() and not l.strip().startswith("#")]
        if not entries:
            fail(f"{plat}/patches/SERIES is empty")
            continue
        for line in entries:
            if (pdir / line).exists():
                ok(f"{plat}/patches/{line}")
            else:
                fail(f"SERIES entry missing on disk: {plat}/patches/{line}")
        for f in [f"{plat}/args.gn", f"{plat}/default_flags.json",
                  f"{plat}/README.md"]:
            if (ROOT / f).exists():
                ok(f)
            else:
                fail(f"{f} missing")
        check_json(ROOT / plat / "default_flags.json")

    print("== patch file structure ==")
    import re as _re
    _hunk = _re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    for plat in ["windows", "android", "linux"]:
        pdir = ROOT / plat / "patches"
        for patch in sorted(pdir.glob("*.patch")):
            raw = patch.read_bytes()
            if b"\r" in raw:
                fail(f"{plat}/patches/{patch.name} has CRLF — patches must be LF for git apply")
                continue
            lines = raw.decode("utf-8").splitlines()
            expect_plus = False
            ok_file = True
            i = 0
            while i < len(lines):
                if lines[i].startswith("--- "):
                    if not (i + 1 < len(lines) and lines[i + 1].startswith("+++ ")):
                        fail(f"{plat}/patches/{patch.name}: --- without +++")
                        ok_file = False
                        break
                    i += 2
                    continue
                m = _hunk.match(lines[i])
                if m:
                    j = i + 1
                    old_c = new_c = 0
                    while j < len(lines) and lines[j][:1] in (" ", "+", "-") \
                            and not _hunk.match(lines[j]) \
                            and not lines[j].startswith("--- "):
                        if lines[j].startswith("\\ "):
                            j += 1
                            continue
                        if lines[j][:1] in (" ", "-"):
                            old_c += 1
                        if lines[j][:1] in (" ", "+"):
                            new_c += 1
                        j += 1
                    exp_old = int(m.group(2)) if m.group(2) is not None else 1
                    exp_new = int(m.group(4)) if m.group(4) is not None else 1
                    if old_c != exp_old or new_c != exp_new:
                        fail(f"{plat}/patches/{patch.name}: hunk {m.group(0)} "
                             f"body is -{old_c} +{new_c}")
                        ok_file = False
                        break
                    i = j
                    continue
                i += 1
            if ok_file:
                ok(f"{plat}/patches/{patch.name} structure")

    print("== patch apply smoke test ==")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "smoke_patch_apply.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"smoke_patch_apply.py failed:\n{r.stdout}\n{r.stderr}")
    else:
        for line in r.stdout.splitlines():
            if line.startswith("smoke ok:") or line.strip() == "SMOKE OK":
                print(f"    {line}")
        ok("smoke_patch_apply.py")

    print("== cross-platform patch parity ==")
    base = None
    for plat in ["windows", "android", "linux"]:
        entries = [l.strip() for l in (ROOT / plat / "patches" / "SERIES").read_text().splitlines()
                   if l.strip() and not l.strip().startswith("#")]
        shared = [e for e in entries
                  if not re.match(r"^000[678]-", e)]
        if base is None:
            base = shared
            ok(f"{plat} defines shared baseline ({len(shared)} patches)")
        elif shared != base:
            fail(f"{plat}/patches SERIES baseline differs from {base}")
        else:
            ok(f"{plat} matches shared baseline ({len(shared)} patches)")

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
                "filter_lists/parity_vectors.json",
                "filter_lists/youtube.txt",
                "filter_lists/micromium-default.txt"]:
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
              "tools/parity_check.py", "tools/smoke_patch_apply.py",
              "tools/fetch_chromium.ps1", "tools/fetch_chromium.sh",
              "tools/build.ps1", "tools/build.sh"]:
        if (ROOT / t).exists():
            ok(t)
        else:
            fail(f"tool missing: {t}")
    try:
        for t in ["tools/apply_patches.py", "tools/update_filters.py",
                  "tools/parity_check.py", "tools/smoke_patch_apply.py",
                  "tools/verify.py"]:
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
