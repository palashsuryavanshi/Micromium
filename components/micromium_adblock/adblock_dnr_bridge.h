// Micromium adblock <-> declarativeNetRequest bridge.
//
// Purpose: translate Micromium AdblockEngine rules into DNR-compatible
// dynamic rules so blocking happens in the network service (fast, before
// network), while AdblockEngine stays as the single source of truth for
// matching + unit tests.
//
// Chromium integration point (see README.md in this dir):
//   chrome/browser/micromium/adblock_service.cc  (created by overlay)
//   calls micromium::AdblockDnrBridge::ToDnrRules() on startup / list update
//   then feeds them to declarativeNetRequest::RulesMonitor.

#ifndef MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_DNR_BRIDGE_H_
#define MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_DNR_BRIDGE_H_

#include <string>
#include <vector>

#include "adblock_engine.h"

namespace micromium {

// Subset of DNR RuleActionType we emit. Mirrors
// components/declarative_net_request/common/constants.h to avoid pulling
// full extension headers into unit tests.
enum class DnrAction { kBlock = 0, kAllow = 1 };

struct DnrRule {
  int id = 0;                 // 1-based, stable per session
  int priority = 1;           // exceptions get higher priority
  DnrAction action = DnrAction::kBlock;
  std::string url_filter;     // DNR urlFilter syntax
  std::string domains;        // optional initiator domain condition (CSV)
};

class AdblockDnrBridge {
 public:
  // Converts engine rules to DNR rules. Drops rules that have no DNR
  // equivalent (e.g. cosmetic filters starting with '##').
  static std::vector<DnrRule> ToDnrRules(const AdblockEngine& engine);

  // Serializes to the JSON format accepted by DNR dynamic rules
  // (chrome.declarativeNetRequest.updateDynamicRules). Used by the
  // EasyList updater + tests to diff lists without a full Chromium build.
  static std::string ToDnrJson(const std::vector<DnrRule>& rules);

  // Converts a single EasyList-style pattern to DNR urlFilter.
  //   "||ads.example.com^" -> "||ads.example.com^"
  //   "|https://tracker/x" -> "|https://tracker/x"
  //   "ads.example.com/banner" -> "ads.example.com/banner"
  // Returns empty string if not convertible (cosmetic / scriptlet).
  static std::string PatternToUrlFilter(const std::string& pattern);
};

}  // namespace micromium

#endif  // MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_DNR_BRIDGE_H_
