// MicromiumAdblockService: owns AdblockEngine + pushes DNR dynamic rules.
//
// Threading: constructed on browser UI thread, matching is thread-safe
// for read (ShouldBlock) after LoadFilterLists completes.

#ifndef MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_
#define MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_

#include <functional>
#include <memory>
#include <string>

#include "adblock_dnr_bridge.h"
#include "adblock_engine.h"
#include "rust_matcher.h"

namespace micromium {

// Callback receiving serialized DNR JSON. The chrome/ embedder binds this
// to declarativeNetRequest::RulesMonitor::UpdateDynamicRules().
using DnrUpdateCallback =
    std::function<void(const std::string& dnr_json)>;

class AdblockService {
 public:
  // |prefer_rust_engine| selects the adblock-rust backend when it was
  // compiled in (micromium_use_adblock_rust=true). Defaults to the
  // always-available substring fallback.
  explicit AdblockService(bool prefer_rust_engine = false);
  ~AdblockService();

  // Loads all bundled lists + user lists, rebuilds DNR rules, fires |cb|.
  // When disabled via SetEnabled(false), pushes an empty rule set so the
  // settings-page toggle takes effect without a restart.
  void LoadAndPushRules(const std::string& filter_text,
                        DnrUpdateCallback cb);

  // Toggles blocking. Persists via the micromium.adblock.enabled pref on
  // the chrome/ side; the service itself just gates matching + DNR output.
  void SetEnabled(bool enabled);
  bool enabled() const { return enabled_; }

  bool ShouldBlock(const std::string& url) const;
  size_t rule_count() const { return engine_->rule_count(); }

 private:
  std::unique_ptr<AdblockEngine> engine_;
  bool enabled_ = true;
};

}  // namespace micromium

#endif  // MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_
