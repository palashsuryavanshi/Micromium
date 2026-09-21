// See adblock_dnr_bridge.h for docs.

#include "adblock_dnr_bridge.h"

#include <sstream>

namespace micromium {

namespace {

// EasyList options after '$' that have no DNR equivalent in the static
// fast path — we still emit the URL part and let exceptions handle the rest.
// Full option handling (third-party, domain=) is TODO for adblock-rust swap.
std::string StripOptions(const std::string& pattern) {
  size_t dollar = pattern.find('$');
  if (dollar == std::string::npos) {
    return pattern;
  }
  return pattern.substr(0, dollar);
}

bool IsCosmetic(const std::string& pattern) {
  return pattern.find("##") != std::string::npos ||
         pattern.find("#@#") != std::string::npos ||
         pattern.find("#?#") != std::string::npos;
}

}  // namespace

std::string AdblockDnrBridge::PatternToUrlFilter(const std::string& pattern) {
  if (pattern.empty() || IsCosmetic(pattern)) {
    return "";
  }
  std::string base = StripOptions(pattern);
  // Trim whitespace.
  size_t start = base.find_first_not_of(" \t\r\n");
  size_t end = base.find_last_not_of(" \t\r\n");
  if (start == std::string::npos) {
    return "";
  }
  return base.substr(start, end - start + 1);
}

std::vector<DnrRule> AdblockDnrBridge::ToDnrRules(
    const AdblockEngine& engine_rules) {
  // NOTE: AdblockEngine exposes rules only via matching today. For the
  // bridge we re-derive from the same filter text in production
  // (AdblockService keeps the raw text). This overload exists so unit tests
  // can round-trip without friends. Production path: use ToDnrRulesFromText.
  std::vector<DnrRule> out;
  (void)engine_rules;
  return out;
}

std::string AdblockDnrBridge::ToDnrJson(const std::vector<DnrRule>& rules) {
  std::ostringstream json;
  json << "[";
  for (size_t i = 0; i < rules.size(); ++i) {
    const auto& r = rules[i];
    if (i > 0) {
      json << ",";
    }
    json << "{\"id\":" << r.id << ",\"priority\":" << r.priority
         << ",\"action\":{\"type\":\""
         << (r.action == DnrAction::kAllow ? "allow" : "block") << "\"}"
         << ",\"condition\":{\"urlFilter\":\"";
    // Minimal JSON escaping for quotes/backslashes.
    for (char c : r.url_filter) {
      if (c == '"' || c == '\\') {
        json << '\\';
      }
      json << c;
    }
    json << "\",\"resourceTypes\":[\"main_frame\",\"sub_frame\",\"script\","
            "\"xmlhttprequest\",\"image\",\"media\"]}}";
  }
  json << "]";
  return json.str();
}

}  // namespace micromium
