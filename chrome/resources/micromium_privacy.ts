// Micromium Privacy settings subpage.
// Talks to MicromiumPrivacyHandler (chrome/micromium_privacy_handler.cc).
// Route: chrome://settings/micromium-privacy (registered by patch 0005).

interface MicromiumPrefs {
  adblockEnabled: boolean;
  adblockAutoUpdate: boolean;
  metricsOptIn: boolean;
}

declare const chrome: any;

function render(prefs: MicromiumPrefs): void {
  (document.getElementById('adblockToggle') as any).checked =
      prefs.adblockEnabled;
  (document.getElementById('autoUpdateToggle') as any).checked =
      prefs.adblockAutoUpdate;
  (document.getElementById('metricsToggle') as any).checked =
      prefs.metricsOptIn;
  document.getElementById('status')!.textContent =
      prefs.adblockEnabled ? 'Protection is on.' : 'Protection is off.';
}

function init(): void {
  chrome.send('getMicromiumPrefs');
  chrome.addWebUiListener('micromium-prefs-changed', (prefs: MicromiumPrefs) => {
    render(prefs);
  });
  document.getElementById('adblockToggle')!.addEventListener('change', (e) => {
    chrome.send('setAdblockEnabled', [(e.target as any).checked]);
  });
  document.getElementById('autoUpdateToggle')!.addEventListener(
      'change', (e) => {
        chrome.send('setAdblockAutoUpdate', [(e.target as any).checked]);
      });
  document.getElementById('metricsToggle')!.addEventListener('change', (e) => {
    chrome.send('setMetricsOptIn', [(e.target as any).checked]);
  });
  document.getElementById('resetButton')!.addEventListener('click', () => {
    chrome.send('resetMicromiumPrivacy');
  });
}

document.addEventListener('DOMContentLoaded', init);
