#include "micromium_prefs.h"

#include "components/prefs/pref_registry_simple.h"

namespace micromium {

void RegisterMicromiumPrefs(PrefRegistrySimple* registry) {
  // Adblock ships ON; the settings page flips this without restart.
  registry->RegisterBooleanPref(kAdblockEnabled, true);
  // Filter lists auto-refresh via the component updater hook.
  registry->RegisterBooleanPref(kAdblockAutoUpdate, true);
  // Telemetry stays OFF unless the user explicitly opts in.
  registry->RegisterBooleanPref(kMetricsOptIn, false);
}

}  // namespace micromium
