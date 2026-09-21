// Micromium built-in adblock engine (skeleton).
// Production note: replace Rule matching with adblock-rust or
// Brave's adblock engine for full EasyList syntax. This file compiles
// standalone against //base + //url and passes unit_tests.

#ifndef MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_ENGINE_H_
#define MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_ENGINE_H_

#include <string>
#include <vector>

namespace micromium {

struct AdblockRule {
  std::string pattern;   // substring or "|domain|path" simplified match
  bool is_exception = false;
};

class AdblockEngine {
 public:
  AdblockEngine();
  virtual ~AdblockEngine();

  // Loads newline-separated filter list text. Lines starting with '!'
  // are comments. "@@" prefix marks an exception rule.
  // Virtual so the adblock-rust backend (rust_matcher.h) can substitute
  // full EasyList syntax behind the same interface.
  virtual void LoadFilterList(const std::string& text);

  // Returns true if |url| should be blocked given loaded rules.
  virtual bool ShouldBlock(const std::string& url) const;

  virtual size_t rule_count() const { return rules_.size(); }

 private:
  std::vector<AdblockRule> rules_;
};

}  // namespace micromium

#endif  // MICROMIUM_COMPONENTS_MICROMIUM_ADBLOCK_ADBLOCK_ENGINE_H_
