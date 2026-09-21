// Micromium adblock unit tests (standalone main, no gtest needed).
// Covers: fallback engine, @@ exceptions, cosmetic no-ops, DNR bridge
// conversion + JSON escaping, AdblockService enable toggle, backend factory.
// The adblock-rust backend must satisfy filter_lists/parity_vectors.json;
// the `rust` column there is checked in CI once the crate is vendored.

#include <cassert>
#include <iostream>

#include "adblock_dnr_bridge.h"
#include "adblock_engine.h"
#include "adblock_service.h"
#include "rust_matcher.h"

static void TestFallbackBasics() {
  micromium::AdblockEngine engine;
  engine.LoadFilterList(
      "! comment\n"
      "\n"
      "ads.example.com\n"
      "@@allow.ads.example.com/safe\n");
  assert(engine.rule_count() == 2);
  assert(engine.ShouldBlock("https://ads.example.com/banner.js"));
  assert(!engine.ShouldBlock("https://allow.ads.example.com/safe/logo.png"));
  assert(!engine.ShouldBlock("https://example.com/"));
}

static void TestCosmeticNeverBlocksNetwork() {
  micromium::AdblockEngine engine;
  engine.LoadFilterList("example.com##.ad-box\n");
  assert(!engine.ShouldBlock("https://example.com/"));
}

static void TestBridgeConversion() {
  // Cosmetic input has no DNR equivalent.
  assert(micromium::AdblockDnrBridge::PatternToUrlFilter(
             "example.com##.ad") == "");
  // Network patterns pass through (options stripped).
  assert(micromium::AdblockDnrBridge::PatternToUrlFilter(
             "||ads.example.com^") == "||ads.example.com^");
  assert(micromium::AdblockDnrBridge::PatternToUrlFilter(
             "banner_$third-party") == "banner_");
  // JSON escaping keeps quotes/backslashes intact.
  std::vector<micromium::DnrRule> rules;
  micromium::DnrRule r;
  r.id = 1;
  r.priority = 1;
  r.action = micromium::DnrAction::kBlock;
  r.url_filter = "a\"b\\c";
  rules.push_back(r);
  std::string json = micromium::AdblockDnrBridge::ToDnrJson(rules);
  assert(json.find("a\\\"b\\\\c") != std::string::npos);
}

static void TestServiceToggle() {
  micromium::AdblockService service;
  bool pushed_empty = false;
  service.SetEnabled(false);
  service.LoadAndPushRules(
      "ads.example.com\n",
      [&](const std::string& dnr_json) { pushed_empty = (dnr_json == "[]"); });
  assert(pushed_empty);
  assert(!service.ShouldBlock("https://ads.example.com/x.js"));
  service.SetEnabled(true);
  service.LoadAndPushRules(
      "ads.example.com\n", [&](const std::string& dnr_json) {
        assert(dnr_json.find("ads.example.com") != std::string::npos);
      });
  assert(service.ShouldBlock("https://ads.example.com/x.js"));
}

static void TestFactory() {
  // Without MICROMIUM_USE_ADBLOCK_RUST this is always the fallback.
  auto engine = micromium::CreateAdblockEngine(false);
  assert(engine);
  engine->LoadFilterList("ads.example.com\n");
  assert(engine->ShouldBlock("https://ads.example.com/x.js"));
}

int main() {
  TestFallbackBasics();
  TestCosmeticNeverBlocksNetwork();
  TestBridgeConversion();
  TestServiceToggle();
  TestFactory();
  std::cout << "micromium adblock tests passed\n";
  return 0;
}
