// MicromiumAdblockService: owns AdblockEngine + pushes DNR dynamic rules.
//
// Threading: constructed on browser UI thread, matching is thread-safe
// for read (ShouldBlock) after LoadFilterLists completes.

#ifndef MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_
#define MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_

#include <functional>
#include <string>

#include "adblock_dnr_bridge.h"
#include "adblock_engine.h"

namespace micromium {

// Callback receiving serialized DNR JSON. The chrome/ embedder binds this
// to declarativeNetRequest::RulesMonitor::UpdateDynamicRules().
using DnrUpdateCallback =
    std::function<void(const std::string& dnr_json)>;

class AdblockService {
 public:
  AdblockService();
  ~AdblockService();

  // Loads all bundled lists + user lists, rebuilds DNR rules, fires |cb|.
  void LoadAndPushRules(const std::string& filter_text,
                        DnrUpdateCallback cb);

  bool ShouldBlock(const std::string& url) const;
  size_t rule_count() const { return engine_.rule_count(); }

 private:
  AdblockEngine engine_;
};

}  // namespace micromium

#endif  // MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_SERVICE_H_
