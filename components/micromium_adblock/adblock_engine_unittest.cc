// Minimal unit test — run with `gn` target :unit_tests or standalone gtest.
#include "adblock_engine.h"

#include <cassert>
#include <iostream>

int main() {
  micromium::AdblockEngine engine;
  engine.LoadFilterList(
      "! micromium test list\n"
      "ads.example.com\n"
      "@@allow.ads.example.com/safe\n");
  assert(engine.rule_count() == 2);
  assert(engine.ShouldBlock("https://ads.example.com/banner.js"));
  assert(!engine.ShouldBlock("https://allow.ads.example.com/safe/logo.png"));
  assert(!engine.ShouldBlock("https://example.com/"));
  std::cout << "micromium adblock tests passed\n";
  return 0;
}
