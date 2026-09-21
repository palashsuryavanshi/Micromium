// Micromium profile prefs. Registered once at startup (see patch 0005).

#ifndef MICROMIUM_CHROME_MICROMIUM_PREFS_H_
#define MICROMIUM_CHROME_MICROMIUM_PREFS_H_

class PrefRegistrySimple;

namespace micromium {

// Preference names (profile-scoped, synced as local state only).
inline constexpr char kAdblockEnabled[] = "micromium.adblock.enabled";
inline constexpr char kAdblockAutoUpdate[] = "micromium.adblock.auto_update";
inline constexpr char kMetricsOptIn[] = "micromium.privacy.metrics_opt_in";

void RegisterMicromiumPrefs(PrefRegistrySimple* registry);

}  // namespace micromium

#endif  // MICROMIUM_CHROME_MICROMIUM_PREFS_H_
