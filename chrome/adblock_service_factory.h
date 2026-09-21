// Per-profile AdblockService. KeyedService so each profile gets its own
// engine instance; honors the micromium.adblock.enabled pref.

#ifndef MICROMIUM_CHROME_ADBLOCK_SERVICE_FACTORY_H_
#define MICROMIUM_CHROME_ADBLOCK_SERVICE_FACTORY_H_

#include "components/keyed_service/content/browser_context_keyed_service_factory.h"

namespace micromium {

class AdblockService;

class AdblockServiceFactory : public BrowserContextKeyedServiceFactory {
 public:
  static AdblockService* GetForProfile(content::BrowserContext* context);
  static AdblockServiceFactory* GetInstance();

 private:
  AdblockServiceFactory();
  ~AdblockServiceFactory() override;

  std::unique_ptr<KeyedService> BuildServiceInstanceFor(
      content::BrowserContext* context) const override;
};

}  // namespace micromium

#endif  // MICROMIUM_CHROME_ADBLOCK_SERVICE_FACTORY_H_
