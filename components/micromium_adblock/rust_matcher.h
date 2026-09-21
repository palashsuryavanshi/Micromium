// Rust-backed matcher for full EasyList syntax.
//
// When MICROMIUM_USE_ADBLOCK_RUST is defined (GN arg
// micromium_use_adblock_rust=true, see BUILD.gn + RUST_BACKEND.md),
// RustAdblockEngine delegates matching to the vendored adblock-rust crate
// through the C ABI in rust/src/lib.rs. Otherwise the factory returns the
// built-in substring fallback (adblock_engine.h) and this header
// contributes only the factory declaration, so the base builds with no
// Rust toolchain installed.

#ifndef MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_RUST_MATCHER_H_
#define MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_RUST_MATCHER_H_

#include <memory>

#include "adblock_engine.h"

namespace micromium {

#ifdef MICROMIUM_USE_ADBLOCK_RUST

// Full-syntax engine. Same interface as the fallback, so AdblockService
// and the DNR bridge work unchanged. Handles anchors (||domain^),
// options ($third-party, $domain=...), exception semantics, and cosmetic
// filtering (cosmetic rules are skipped for network matching).
class RustAdblockEngine : public AdblockEngine {
 public:
  RustAdblockEngine();
  ~RustAdblockEngine() override;

  void LoadFilterList(const std::string& text) override;
  bool ShouldBlock(const std::string& url) const override;
  size_t rule_count() const override;

 private:
  // Opaque handle owned by the Rust side (Box<Engine>). Null until load.
  struct RustHandle;
  RustHandle* handle_ = nullptr;
};

#endif  // MICROMIUM_USE_ADBLOCK_RUST

// Factory: prefers the Rust backend when it was compiled in, otherwise
// always returns the fallback. |prefer_rust| lets the embedder force the
// fallback (e.g. low-memory devices or unit tests).
std::unique_ptr<AdblockEngine> CreateAdblockEngine(bool prefer_rust = true);

}  // namespace micromium

#endif  // MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_RUST_MATCHER_H_
