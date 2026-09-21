#include "adblock_service.h"

namespace micromium {

AdblockService::AdblockService() = default;
AdblockService::~AdblockService() = default;

void AdblockService::LoadAndPushRules(const std::string& filter_text,
                                      DnrUpdateCallback cb) {
  engine_.LoadFilterList(filter_text);
  // Convert: split text into convertible DNR rules here so the embedder
  // gets a ready-to-apply JSON blob. Cosmetic rules stay engine-only.
  std::vector<DnrRule> dnr;
  int id = 1;
  size_t pos = 0;
  while (pos < filter_text.size()) {
    size_t end = filter_text.find('\n', pos);
    std::string line = filter_text.substr(
        pos, end == std::string::npos ? std::string::npos : end - pos);
    // Trim CR.
    if (!line.empty() && line.back() == '\r') {
      line.pop_back();
    }
    bool is_exception = false;
    if (line.rfind("@@", 0) == 0) {
      is_exception = true;
      line = line.substr(2);
    }
    if (!line.empty() && line[0] != '!' && line[0] != '#') {
      std::string url_filter = AdblockDnrBridge::PatternToUrlFilter(line);
      if (!url_filter.empty()) {
        DnrRule rule;
        rule.id = id++;
        rule.priority = is_exception ? 100 : 1;
        rule.action =
            is_exception ? DnrAction::kAllow : DnrAction::kBlock;
        rule.url_filter = url_filter;
        dnr.push_back(rule);
      }
    }
    if (end == std::string::npos) {
      break;
    }
    pos = end + 1;
  }
  if (cb) {
    cb(AdblockDnrBridge::ToDnrJson(dnr));
  }
}

bool AdblockService::ShouldBlock(const std::string& url) const {
  return engine_.ShouldBlock(url);
}

}  // namespace micromium
