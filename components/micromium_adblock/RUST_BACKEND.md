# adblock-rust backend: swap guide

The built-in substring matcher (`adblock_engine.cc`) intentionally covers
~80% of network rules with zero dependencies. This backend swaps in full
EasyList syntax (anchors `||domain^`, options `$third-party,$domain=`,
correct exception precedence) via the `adblock` Rust crate, behind the
same C++ interface.

## Architecture

```
AdblockService -> unique_ptr<AdblockEngine> (factory: CreateAdblockEngine)
    fallback: AdblockEngine            (adblock_engine.cc, always built)
    rust:     RustAdblockEngine        (rust_matcher.cc, needs
              MICROMIUM_USE_ADBLOCK_RUST + :adblock_rust_bridge)
RustAdblockEngine <-> C ABI <-> rust/src/lib.rs <-> adblock crate
```

- `AdblockEngine` methods are `virtual`; `RustAdblockEngine` overrides them.
- The C ABI (`micromium_adblock_rust_{create,destroy,add_rules,
  should_block,rule_count}`) keeps the C++ side independent of Rust
  toolchain details. Production follow-up: replace with a `cxx` bridge.
- `LoadFilterList` rebuilds the Rust `Engine` from a `FilterSet`; loads
  happen rarely (startup + updater tick), so rebuild cost is irrelevant.
- DNR output is unchanged: `AdblockService` converts the same filter text,
  so both backends emit identical `declarativeNetRequest` rules.

## Status in this repo

- C++ side: done, compiles in the default config (factory returns fallback
  when `MICROMIUM_USE_ADBLOCK_RUST` is unset).
- Rust side: source-complete skeleton (`rust/Cargo.toml`,
  `rust/src/lib.rs`), **not yet vendored or compiled** — there is no Rust
  toolchain in this environment and Chromium vendors crates through
  `//third_party/rust/chromium_crates_io`, which requires a full checkout.
- Behavior contract: `filter_lists/parity_vectors.json`. `fallback` column
  is enforced now (`tools/parity_check.py`); `rust` column is the target
  the Rust backend must satisfy once built.

## Vendoring steps (run inside the Chromium checkout)

1. Copy `rust/Cargo.toml` requirements into
   `src/third_party/rust/chromium_crates_io/Cargo.toml`
   (`adblock = "0.8"`), run the vendor script to produce `Cargo.lock` +
   `vendor/`, and add the crate's `BUILD.gn` shim per
   `src/third_party/rust/chromium_crates_io/README.md`.
2. In your `gn gen` args (or `build/args/*.gn`):
   `micromium_use_adblock_rust = true`.
3. Rebuild `:micromium_adblock`. `rust_matcher.cc` now compiles the
   `RustAdblockEngine` path and links `:adblock_rust_bridge`.
4. Run parity: C++ `unit_tests` + `tools/parity_check.py` must both pass,
   and every vector's `rust` expectation must hold against the real crate.
5. Flip the default: `AdblockServiceFactory` passes `prefer_rust=true`
   (currently default-constructs the fallback).

## Rollback

Set `micromium_use_adblock_rust = false` (the default). The Rust target is
not even defined, the factory returns the fallback, and nothing else
changes — the toggle is one GN line.
