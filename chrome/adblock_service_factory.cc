#include "adblock_service_factory.h"

#include "base/no_destructor.h"
#include "chrome/browser/profiles/profile.h"
#include "components/keyed_service/content/browser_context_dependency_manager.h"
#include "components/prefs/pref_service.h"
#include "micromium_prefs.h"
#include "micromium/components/micromium_adblock/adblock_service.h"

namespace micromium {

AdblockService* AdblockServiceFactory::GetForProfile(
    content::BrowserContext* context) {
  return static_cast<AdblockService*>(
      GetInstance()->GetServiceForBrowserContext(context, true));
}

AdblockServiceFactory* AdblockServiceFactory::GetInstance() {
  static base::NoDestructor<AdblockServiceFactory> instance;
  return instance.get();
}

AdblockServiceFactory::AdblockServiceFactory()
    : BrowserContextKeyedServiceFactory(
          "MicromiumAdblockService",
          BrowserContextDependencyManager::GetInstance()) {}

AdblockServiceFactory::~AdblockServiceFactory() = default;

std::unique_ptr<KeyedService>
AdblockServiceFactory::BuildServiceInstanceFor(
    content::BrowserContext* context) const {
  Profile* profile = Profile::FromBrowserContext(context);
  auto service = std::make_unique<AdblockService>();
  // Respect the settings-page toggle from first run: a disabled pref means
  // we push an empty DNR rule set instead of the bundled lists.
  bool enabled =
      profile->GetPrefs()->GetBoolean(micromium::kAdblockEnabled);
  service->SetEnabled(enabled);
  return service;
}

}  // namespace micromium
