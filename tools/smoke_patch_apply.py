#!/usr/bin/env python3
"""Smoke test: proves every platform patch stack applies with `git apply`.

Builds a fake Chromium `src/` tree containing the exact anchor lines each
patch's context hunks expect, then runs the real
`tools/apply_patches.py --platform <p> --overlay` path for windows, android
and linux. Asserts platform markers land in the patched files.

Usage: python tools/smoke_patch_apply.py
Exit 0 = all three platforms apply cleanly. No network, no checkout needed.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import apply_patches  # noqa: E402

COMMON_ANCHORS = {
    "BUILD.gn": "{\n}\n",
    "google_apis/build.gn": (
        "# Upstream google_apis build config.\n"
        "# Micromium: default to no baked-in keys.\n"
        'source_set("google_apis") {\n'
        "  sources = [\n"
        '    "google_api_keys.cc",\n'
        "  ]\n"
        "}\n"
    ),
    "chrome/common/chrome_switches.cc": (
        '#include "chrome/common/chrome_switches.h"\n'
        "namespace switches {\n"
        "}  // namespace switches\n"
    ),
    "chrome/browser/policy/policy_helpers.cc": (
        "// Micromium patch marker: disable Sync / Sign-in by default.\n"
    ),
    "components/metrics/metrics_service.cc": (
        '#include "components/metrics/metrics_service.h"\n'
        "namespace metrics {\n"
        "// Start() early-outs when Micromium privacy mode is on.\n"
        "}  // namespace metrics\n"
    ),
    "rlz/build.gn": (
        'source_set("rlz_lib") {\n'
        "  sources = [\n"
        '    "rlz.cc",\n'
        "  ]\n"
        "}\n"
    ),
    "chrome/browser/metrics/chrome_metrics_service_accessor.cc": (
        '#include "chrome/browser/metrics/chrome_metrics_service_accessor.h"\n'
    ),
    "sandbox/policy/features.cc": (
        '#include "sandbox/policy/features.h"\n'
        "namespace sandbox::policy::features {\n"
        "}  // namespace sandbox::policy::features\n"
    ),
    "build/config/compiler/compiler.gn": (
        "# Toolchain files key off micromium_hardened to add:\n"
        "#   win: /guard:cf, /CETCOMPAT ; clang: -fsanitize=cfi,-mbranch-protection=standard\n"
    ),
    "chrome/browser/BUILD.gn": (
        'source_set("browser") {\n'
        "  deps = [\n"
        '    "//chrome/common",\n'
        "  ]\n"
        "}\n"
    ),
    "chrome/browser/about_flags.cc": (
        '#include "chrome/browser/about_flags.h"\n'
        "namespace about_flags {\n"
        "}  // namespace about_flags\n"
    ),
    "chrome/browser/prefs/browser_prefs.cc": (
        '#include "chrome/browser/prefs/browser_prefs.h"\n'
        "namespace chrome {\n"
        "}  // namespace chrome\n"
    ),
    "chrome/browser/ui/webui/settings/settings_ui.cc": (
        '#include "chrome/browser/ui/webui/settings/settings_ui.h"\n'
        "namespace settings {\n"
        "}  // namespace settings\n"
    ),
    "chrome/browser/resources/settings/route.ts": (
        "// Upstream settings routes live here; rebase the route table on update.\n"
    ),
}

PLATFORM_ANCHORS = {
    "windows": {
        "sandbox/policy/win/sandbox_win.cc": (
            '#include "sandbox/policy/win/sandbox_win.h"\n'
            "namespace sandbox::policy {\n"
            "}  // namespace sandbox::policy\n"
        ),
        "build/config/win/visual_studio_version.gni": (
            "# Toolchain keys off these to add /guard:cf + /CETCOMPAT.\n"
        ),
        "chrome/app/theme/chromium/BRANDING": (
            "# Upstream Chromium branding file; rebase on milestone update.\n"
        ),
        "chrome/installer/setup/install.cc": (
            '#include "chrome/installer/setup/install.h"\n'
            "namespace installer {\n"
            "}  // namespace installer\n"
        ),
    },
    "android": {
        "build/config/android/config.gni": (
            "# Toolchain keys off these to add -mbranch-protection=standard + -fsanitize=cfi.\n"
        ),
        "base/android/build_info.cc": (
            '#include "base/android/build_info.h"\n'
            "namespace base::android {\n"
            "}  // namespace base::android\n"
        ),
        "chrome/android/java/AndroidManifest.xml": "<manifest>\n</manifest>\n",
        "chrome/android/weblayer/wrapper.cc": (
            '#include "chrome/android/weblayer/wrapper.h"\n'
            "namespace weblayer {\n"
            "}  // namespace weblayer\n"
        ),
    },
    "linux": {
        "sandbox/policy/linux/sandbox_linux.cc": (
            '#include "sandbox/policy/linux/sandbox_linux.h"\n'
            "namespace sandbox::policy {\n"
            "}  // namespace sandbox::policy\n"
        ),
        "media/gpu/vaapi/vaapi_wrapper.cc": (
            '#include "media/gpu/vaapi/vaapi_wrapper.h"\n'
            "namespace media {\n"
            "}  // namespace media\n"
        ),
        "chrome/app/theme/chromium/BRANDING": (
            "# Upstream Chromium branding file; rebase on milestone update.\n"
        ),
        "chrome/browser/shell_integration_linux.cc": (
            '#include "chrome/browser/shell_integration_linux.h"\n'
            "namespace shell_integration {\n"
            "}  // namespace shell_integration\n"
        ),
    },
}

# file -> marker that must exist after the platform stack applies
MARKERS = {
    "windows": {
        "google_apis/build.gn": "MICROMIUM_NO_GOOGLE_APIS",
        "sandbox/policy/win/sandbox_win.cc": "kMicromiumWinSandboxLockdownByDefault",
        "chrome/app/theme/chromium/BRANDING": "micromium.browser.stable",
        "chrome/browser/BUILD.gn": '"//micromium/chrome"',
    },
    "android": {
        "google_apis/build.gn": "MICROMIUM_NO_GOOGLE_APIS",
        "build/config/android/config.gni": "micromium_android_branch_protection",
        "chrome/android/java/AndroidManifest.xml": "org.micromium.browser",
        "chrome/browser/BUILD.gn": '"//micromium/chrome"',
    },
    "linux": {
        "google_apis/build.gn": "MICROMIUM_NO_GOOGLE_APIS",
        "sandbox/policy/linux/sandbox_linux.cc": "kMicromiumLinuxSandboxStrictByDefault",
        "chrome/browser/shell_integration_linux.cc": "micromium-browser.desktop",
        "chrome/browser/BUILD.gn": '"//micromium/chrome"',
    },
}


def write_anchors(src: Path, platform: str) -> None:
    files = dict(COMMON_ANCHORS)
    files.update(PLATFORM_ANCHORS[platform])
    for rel, text in files.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)


def test_platform(platform: str) -> bool:
    tmp = Path(tempfile.mkdtemp(prefix=f"micromium-smoke-{platform}-"))
    try:
        write_anchors(tmp, platform)
        patches_dir = ROOT / platform / "patches"
        print(f"--- smoke: {platform} ({patches_dir}) ---")
        if not apply_patches.apply_patches(tmp, patches_dir):
            print(f"SMOKE FAIL: {platform} patches did not apply")
            return False
        apply_patches.copy_overlay(tmp, platform)
        for rel, marker in MARKERS[platform].items():
            text = (tmp / rel).read_text(encoding="utf-8")
            if marker not in text:
                print(f"SMOKE FAIL: {platform}/{rel} missing {marker!r}")
                return False
        flags = tmp / "micromium" / "micromium_default_flags.json"
        if not flags.exists():
            print(f"SMOKE FAIL: {platform} overlay flags missing")
            return False
        print(f"smoke ok: {platform}")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    if shutil.which("git") is None:
        print("SKIP: git not found")
        return 0
    ok = all(test_platform(p) for p in ["windows", "android", "linux"])
    print("SMOKE OK" if ok else "SMOKE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
