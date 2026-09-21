// See adblock_engine.h for docs.

#include "adblock_engine.h"

#include <sstream>

namespace micromium {

AdblockEngine::AdblockEngine() = default;
AdblockEngine::~AdblockEngine() = default;

void AdblockEngine::LoadFilterList(const std::string& text) {
  std::istringstream stream(text);
  std::string line;
  while (std::getline(stream, line)) {
    if (line.empty() || line[0] == '!' || line[0] == '#') {
      continue;
    }
    AdblockRule rule;
    if (line.rfind("@@", 0) == 0) {
      rule.is_exception = true;
      rule.pattern = line.substr(2);
    } else {
      rule.pattern = line;
    }
    if (!rule.pattern.empty()) {
      rules_.push_back(rule);
    }
  }
}

bool AdblockEngine::ShouldBlock(const std::string& url) const {
  bool blocked = false;
  for (const auto& rule : rules_) {
    if (url.find(rule.pattern) != std::string::npos) {
      if (rule.is_exception) {
        return false;  // exception overrides any prior block
      }
      blocked = true;
    }
  }
  return blocked;
}

}  // namespace micromium
