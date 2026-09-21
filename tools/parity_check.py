#!/usr/bin/env python3
"""Parity check: proves the fallback matcher behaves as documented.

Implements the exact semantics of components/micromium_adblock/
adblock_engine.cc in Python, runs filter_lists/parity_vectors.json, and
asserts every `fallback` expectation. The `rust` column is informational:
cases where rust != fallback are the syntax gap the adblock-rust backend
(rust/) is specified to close.

Usage: python tools/parity_check.py
Exit 0 = all fallback expectations hold.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "components" / "micromium_adblock" / "filter_lists" / "parity_vectors.json"


class FallbackEngine:
    """Mirror of AdblockEngine::{LoadFilterList, ShouldBlock}."""

    def __init__(self):
        self.rules = []  # (pattern, is_exception)

    def load(self, lines):
        for line in lines:
            if not line or line.startswith("!") or line.startswith("#"):
                continue
            if line.startswith("@@"):
                self.rules.append((line[2:], True))
            else:
                self.rules.append((line, False))

    def should_block(self, url):
        blocked = False
        for pattern, is_exception in self.rules:
            if pattern and pattern in url:
                if is_exception:
                    return False
                blocked = True
        return blocked


def main():
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    failures = 0
    gaps = []
    for v in data["vectors"]:
        eng = FallbackEngine()
        eng.load(v["rules"])
        got = eng.should_block(v["url"])
        want = v["fallback"]
        status = "ok" if got == want else "FAIL"
        if got != want:
            failures += 1
        if v["rust"] != v["fallback"]:
            gaps.append(v["name"])
        print(f"  {status}: {v['name']} (fallback={got}, want={want}, rust-target={v['rust']})")
    print(f"vectors={len(data['vectors'])} failures={failures}")
    if gaps:
        print(f"documented Rust-gap cases ({len(gaps)}): {', '.join(gaps)}")
    if failures:
        print("PARITY FAILED", file=sys.stderr)
        return 1
    print("PARITY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
