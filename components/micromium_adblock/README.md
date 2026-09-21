# Wiring MicromiumAdblock into Chromium (DNR path)

`AdblockEngine` is the matcher. `AdblockService` owns it and emits DNR JSON.
Blocking happens in the network service via `declarativeNetRequest`.

## Files in this component

- `adblock_engine.{h,cc}` — substring + `@@` exception matcher, unit-tested
- `adblock_dnr_bridge.{h,cc}` — EasyList pattern → DNR `urlFilter` + JSON
- `adblock_service.{h,cc}` — loads lists, calls bridge, fires update callback
- `filter_lists/` — bundled lists + `sources.json` manifest

## Chrome integration (applied by `patches/0004-wire-micromium-adblock.patch`)

1. `chrome/browser/BUILD.gn` gains:
   ```
   deps += [ "//micromium/components/micromium_adblock" ]
   ```
2. New file in checkout (created by overlay, not upstream):
   `src/micromium/chrome/adblock_service_factory.cc` — creates one
   `AdblockService` per profile, binds `DnrUpdateCallback` to:
   ```cpp
   declarative_net_request::RulesMonitor::UpdateDynamicRules()
   ```
3. Default enable flag: `--enable-features=MicromiumAdblock`
   (see `patches/micromium_default_flags.json`).
4. UI stub: `chrome://settings/micromium-privacy` toggles the feature.
   Until the WebUI lands, use `chrome://flags/#micromium-adblock`.

## Android integration

Same service, bound in `chrome/android/` WebLayer wrapper. DNR works on
Android without extra JNI — JSON crosses via existing DNR mojo pipe.

## Testing without a full build

```bash
python3 tools/update_filters.py --check   # validates lists parse
```

C++ unit test target `:unit_tests` covers engine + bridge escaping.
