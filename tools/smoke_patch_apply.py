#!/usr/bin/env python3
"""Smoke test: proves every platform patch stack applies with `git apply`.

Builds a fake Chromium `src/` tree containing the exact anchor lines each
patch's context hunks expect (mirroring the real 153.0.8010.27 file heads),
then runs the real `tools/apply_patches.py --platform <p> --overlay` path
for windows, android and linux. Asserts platform markers land in the
patched files.

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
        "  # Set these to bake the specified API keys and OAuth client\n"
        "  # IDs/secrets into your build.\n"
        "  #\n"
    ),
    "chrome/common/chrome_switches.cc": (
        '#include "chrome/common/chrome_switches.h"\n'
        "\n"
        '#include "build/branding_buildflags.h"\n'
    ),
    "chrome/browser/signin/chrome_signin_client.cc": (
        '#include "chrome/browser/signin/chrome_signin_client.h"\n'
        "\n"
        "#include <stddef.h>\n"
    ),
    "components/metrics/metrics_service.cc": (
        "// Copyright 2014 The Chromium Authors\n"
        "// Use of this source code is governed by a BSD-style license that can be\n"
        "// found in the LICENSE file.\n"
        "\n"
        "//" + "-" * 78 + "\n"
    ),
    "rlz/build.gn": (
        'import("//rlz/buildflags/buildflags.gni")\n'
        'import("//testing/test.gni")\n'
    ),
    "chrome/browser/metrics/chrome_metrics_service_accessor.cc": (
        '#include "chrome/browser/metrics/chrome_metrics_service_accessor.h"\n'
        "\n"
        "#include <string_view>\n"
    ),
    "sandbox/policy/features.cc": (
        "namespace sandbox::policy::features {\n"
        "\n"
        "#if !BUILDFLAG(IS_MAC) && !BUILDFLAG(IS_FUCHSIA)\n"
    ),
    "build/config/compiler/compiler.gni": (
        'import("//build/toolchain/toolchain.gni")\n'
        'import("//build_overrides/build.gni")\n'
    ),
    "chrome/browser/BUILD.gn": (
        'source_set("browser_process") {\n'
        "  sources = [\n"
        '    "browser_process.cc",\n'
        '    "browser_process.h",\n'
        "  ]\n"
        "  deps = [\n"
        '    "//base",\n'
        '    "//chrome/browser/status_icons",\n'
        "  ]\n"
    ),
    "chrome/browser/about_flags.cc": (
        '#include "chrome/browser/about_flags.h"\n'
        "\n"
        "#include <iterator>\n"
    ),
    "chrome/browser/prefs/browser_prefs.cc": (
        '#include "chrome/browser/prefs/browser_prefs.h"\n'
        "\n"
        "#include <array>\n"
    ),
    "chrome/browser/ui/webui/settings/settings_ui.cc": (
        '#include "chrome/browser/ui/webui/settings/settings_ui.h"\n'
        "\n"
        "#include <stddef.h>\n"
    ),
    "chrome/browser/resources/settings/route.ts": (
        "// Copyright 2016 The Chromium Authors\n"
        "// Use of this source code is governed by a BSD-style license that can be\n"
        "// found in the LICENSE file.\n"
        "\n"
        "import {assert} from 'chrome://resources/js/assert.js';\n"
    ),
}

PLATFORM_ANCHORS = {
    "windows": {
        "sandbox/policy/win/sandbox_win.cc": (
            '#include "sandbox/policy/win/sandbox_win.h"\n'
            "\n"
            "#include <windows.h>\n"
        ),
        "build/config/win/visual_studio_version.gni": (
            "declare_args() {\n"
            "  # Path to Visual Studio. If empty, the default is used which is to use the\n"
            "  # automatic toolchain in depot_tools. If set, you must also set the\n"
        ),
        "chrome/app/theme/chromium/BRANDING": (
            "MAC_BUNDLE_ID=org.chromium.Chromium\n"
            "MAC_CREATOR_CODE=Cr24\n"
            "MAC_TEAM_ID=\n"
        ),
        "chrome/installer/setup/install.cc": (
            '#include "chrome/installer/setup/install.h"\n'
            "\n"
            "#include <windows.h>\n"
        ),
    },
    "android": {
        "build/config/android/config.gni": (
            "declare_args() {\n"
            "  # Build incremental targets whenever possible.\n"
            "  # See //build/android/incremental_install/README.md for more details.\n"
            "  incremental_install = false\n"
            "}\n"
        ),
        "chrome/android/java/AndroidManifest.xml": (
            'by a child template that "extends" this file.\n'
            "-->\n"
            "\n"
            '<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n'
        ),
        "chrome/android/BUILD.gn": (
            'import("//build/config/android/config.gni")\n'
            'import("//build/config/cronet/config.gni")\n'
        ),
    },
    "linux": {
        "sandbox/policy/linux/sandbox_linux.cc": (
            '#include "sandbox/policy/linux/sandbox_linux.h"\n'
            "\n"
            "#include <dirent.h>\n"
        ),
        "media/gpu/vaapi/vaapi_wrapper.cc": (
            '#include "media/gpu/vaapi/vaapi_wrapper.h"\n'
            "\n"
            "#include <dlfcn.h>\n"
        ),
        "chrome/app/theme/chromium/BRANDING": (
            "MAC_BUNDLE_ID=org.chromium.Chromium\n"
            "MAC_CREATOR_CODE=Cr24\n"
            "MAC_TEAM_ID=\n"
        ),
        "chrome/browser/shell_integration_linux.cc": (
            '#include "chrome/browser/shell_integration_linux.h"\n'
            "\n"
            "#include <fcntl.h>\n"
        ),
    },
}

# file -> marker that must exist after the platform stack applies
MARKERS = {
    "windows": {
        "google_apis/build.gn": "micromium_google_apis_enabled",
        "sandbox/policy/win/sandbox_win.cc": "kMicromiumWinSandboxLockdownByDefault",
        "chrome/app/theme/chromium/BRANDING": "micromium.browser.stable",
        "chrome/browser/BUILD.gn": '"//micromium/chrome:micromium_chrome"',
    },
    "android": {
        "google_apis/build.gn": "micromium_google_apis_enabled",
        "build/config/android/config.gni": "micromium_android_branch_protection",
        "chrome/android/java/AndroidManifest.xml": "org.micromium.browser",
        "chrome/browser/BUILD.gn": '"//micromium/chrome:micromium_chrome"',
    },
    "linux": {
        "google_apis/build.gn": "micromium_google_apis_enabled",
        "sandbox/policy/linux/sandbox_linux.cc": "kMicromiumLinuxSandboxStrictByDefault",
        "chrome/browser/shell_integration_linux.cc": "micromium-browser.desktop",
        "chrome/browser/BUILD.gn": '"//micromium/chrome:micromium_chrome"',
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
