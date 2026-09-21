// WebUI message handler for chrome://settings/micromium-privacy.
//
// JS API (see resources/micromium_privacy.ts):
//   chrome.send('getMicromiumPrefs')            -> 'micromium-prefs-changed'
//   chrome.send('setAdblockEnabled', [bool])
//   chrome.send('setAdblockAutoUpdate', [bool])
//   chrome.send('setMetricsOptIn', [bool])
//   chrome.send('resetMicromiumPrivacy')

#ifndef MICROMIUM_CHROME_MICROMIUM_PRIVACY_HANDLER_H_
#define MICROMIUM_CHROME_MICROMIUM_PRIVACY_HANDLER_H_

#include "content/public/browser/web_ui_message_handler.h"

class PrefService;

namespace micromium {

class AdblockService;

class MicromiumPrivacyHandler : public content::WebUIMessageHandler {
 public:
  MicromiumPrivacyHandler(PrefService* prefs, AdblockService* adblock);
  ~MicromiumPrivacyHandler() override;

  void RegisterMessages() override;

 private:
  void HandleGetPrefs(const base::Value::List& args);
  void HandleSetAdblockEnabled(const base::Value::List& args);
  void HandleSetAdblockAutoUpdate(const base::Value::List& args);
  void HandleSetMetricsOptIn(const base::Value::List& args);
  void HandleReset(const base::Value::List& args);

  void NotifyPrefsChanged();

  raw_ptr<PrefService> prefs_;
  raw_ptr<AdblockService> adblock_;
};

}  // namespace micromium

#endif  // MICROMIUM_CHROME_MICROMIUM_PRIVACY_HANDLER_H_
