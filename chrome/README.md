# Micromium chrome/ layer: settings page + service factory

Route: `chrome://settings/micromium-privacy`.

## How it plugs into upstream settings

Upstream `chrome://settings` is a single WebUI (`SettingsUI`) with JS-side
subpage routes. Micromium adds:

1. **Prefs** (`micromium_prefs.*`) — registered at startup by patch 0005
   in `chrome/browser/prefs/browser_prefs.cc`:
   - `micromium.adblock.enabled` (default `true`)
   - `micromium.adblock.auto_update` (default `true`)
   - `micromium.privacy.metrics_opt_in` (default `false`)
2. **Handler** (`micromium_privacy_handler.*`) — a
   `WebUIMessageHandler` owned by `SettingsUI` (patch 0005 adds it in
   `chrome/browser/ui/webui/settings/settings_ui.cc`). It reads/writes the
   prefs above and calls `AdblockService::SetEnabled()` so the toggle
   applies without restart (DNR rules are cleared/pushed immediately).
3. **Frontend** (`resources/micromium_privacy.{html,ts}`) — a
   `settings-subpage` element. The TS is compiled by the existing settings
   `BUILD.gn` ts_library once patch 0005 lists the new `.ts` file; until
   then it is plain readable source. The settings router entry
   (`MICROMIUM_PRIVACY` route) is added by the same patch in
   `chrome/browser/resources/settings/route.ts`.

## Files

- `BUILD.gn` — `micromium_chrome` source_set
- `micromium_prefs.{h,cc}`
- `adblock_service_factory.{h,cc}` — per-profile service, honors the pref
- `micromium_privacy_handler.{h,cc}`
- `resources/micromium_privacy.html` / `.ts`
