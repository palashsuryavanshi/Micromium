#include "micromium_privacy_handler.h"

#include "base/values.h"
#include "components/prefs/pref_service.h"
#include "content/public/browser/web_ui.h"
#include "micromium_prefs.h"
#include "micromium/components/micromium_adblock/adblock_service.h"

namespace micromium {

MicromiumPrivacyHandler::MicromiumPrivacyHandler(PrefService* prefs,
                                                 AdblockService* adblock)
    : prefs_(prefs), adblock_(adblock) {}
MicromiumPrivacyHandler::~MicromiumPrivacyHandler() = default;

void MicromiumPrivacyHandler::RegisterMessages() {
  web_ui()->RegisterMessageCallback(
      "getMicromiumPrefs",
      base::BindRepeating(&MicromiumPrivacyHandler::HandleGetPrefs,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "setAdblockEnabled",
      base::BindRepeating(&MicromiumPrivacyHandler::HandleSetAdblockEnabled,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "setAdblockAutoUpdate",
      base::BindRepeating(
          &MicromiumPrivacyHandler::HandleSetAdblockAutoUpdate,
          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "setMetricsOptIn",
      base::BindRepeating(&MicromiumPrivacyHandler::HandleSetMetricsOptIn,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "resetMicromiumPrivacy",
      base::BindRepeating(&MicromiumPrivacyHandler::HandleReset,
                          base::Unretained(this)));
}

void MicromiumPrivacyHandler::HandleGetPrefs(const base::Value::List& args) {
  AllowJavascript();
  NotifyPrefsChanged();
}

void MicromiumPrivacyHandler::HandleSetAdblockEnabled(
    const base::Value::List& args) {
  if (args.empty() || !args[0].is_bool()) {
    return;
  }
  bool enabled = args[0].GetBool();
  prefs_->SetBoolean(kAdblockEnabled, enabled);
  if (adblock_) {
    adblock_->SetEnabled(enabled);
  }
  NotifyPrefsChanged();
}

void MicromiumPrivacyHandler::HandleSetAdblockAutoUpdate(
    const base::Value::List& args) {
  if (args.empty() || !args[0].is_bool()) {
    return;
  }
  prefs_->SetBoolean(kAdblockAutoUpdate, args[0].GetBool());
  NotifyPrefsChanged();
}

void MicromiumPrivacyHandler::HandleSetMetricsOptIn(
    const base::Value::List& args) {
  if (args.empty() || !args[0].is_bool()) {
    return;
  }
  prefs_->SetBoolean(kMetricsOptIn, args[0].GetBool());
  NotifyPrefsChanged();
}

void MicromiumPrivacyHandler::HandleReset(const base::Value::List& args) {
  prefs_->SetBoolean(kAdblockEnabled, true);
  prefs_->SetBoolean(kAdblockAutoUpdate, true);
  prefs_->SetBoolean(kMetricsOptIn, false);
  if (adblock_) {
    adblock_->SetEnabled(true);
  }
  NotifyPrefsChanged();
}

void MicromiumPrivacyHandler::NotifyPrefsChanged() {
  base::Value::Dict prefs;
  prefs.Set("adblockEnabled", prefs_->GetBoolean(kAdblockEnabled));
  prefs.Set("adblockAutoUpdate", prefs_->GetBoolean(kAdblockAutoUpdate));
  prefs.Set("metricsOptIn", prefs_->GetBoolean(kMetricsOptIn));
  FireWebUIListener("micromium-prefs-changed", prefs);
}

}  // namespace micromium
