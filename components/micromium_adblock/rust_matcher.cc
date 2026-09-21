// See rust_matcher.h. Toggle implementations:
//   MICROMIUM_USE_ADBLOCK_RUST undefined -> factory returns fallback only.

#include "rust_matcher.h"

namespace micromium {

#ifdef MICROMIUM_USE_ADBLOCK_RUST

// C ABI implemented in rust/src/lib.rs (built by :adblock_rust_bridge).
extern "C" {
void* micromium_adblock_rust_create();
void micromium_adblock_rust_destroy(void* handle);
void micromium_adblock_rust_add_rules(void* handle,
                                      const char* rules_data,
                                      size_t rules_len);
int micromium_adblock_rust_should_block(void* handle,
                                        const char* url_data,
                                        size_t url_len);
size_t micromium_adblock_rust_rule_count(const void* handle);
}  // extern "C"

struct RustAdblockEngine::RustHandle {
  void* inner;
};

RustAdblockEngine::RustAdblockEngine()
    : handle_(new RustHandle{micromium_adblock_rust_create()}) {}

RustAdblockEngine::~RustAdblockEngine() {
  micromium_adblock_rust_destroy(handle_->inner);
  delete handle_;
}

void RustAdblockEngine::LoadFilterList(const std::string& text) {
  micromium_adblock_rust_add_rules(handle_->inner, text.data(), text.size());
}

bool RustAdblockEngine::ShouldBlock(const std::string& url) const {
  return micromium_adblock_rust_should_block(handle_->inner, url.data(),
                                             url.size()) != 0;
}

size_t RustAdblockEngine::rule_count() const {
  return micromium_adblock_rust_rule_count(handle_->inner);
}

std::unique_ptr<AdblockEngine> CreateAdblockEngine(bool prefer_rust) {
  if (prefer_rust) {
    return std::make_unique<RustAdblockEngine>();
  }
  return std::make_unique<AdblockEngine>();
}

#else  // !MICROMIUM_USE_ADBLOCK_RUST

std::unique_ptr<AdblockEngine> CreateAdblockEngine(bool /*prefer_rust*/) {
  return std::make_unique<AdblockEngine>();
}

#endif  // MICROMIUM_USE_ADBLOCK_RUST

}  // namespace micromium
