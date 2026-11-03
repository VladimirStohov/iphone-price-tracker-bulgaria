# Project status — 2026-11-03

- Live site: https://iphone-price-tracker-bulgaria.pages.dev (Cloudflare Pages; HTTP 200 and scan report confirmed before this update).
- Source: https://github.com/VladimirStohov/iphone-price-tracker-bulgaria
- Manual GitHub Actions run 41695365183 succeeded; 10 iSTYLE offers verified, Ardes returned 403, no observed drops. Data commit verified.
- Enlarged dashboard typography, layout and controls. Six configured retailers: iSTYLE, Ardes, eMAG Bulgaria, Ozone, Technomarket, Plesio. Four new adapters passed extraction against real public product HTML; GitHub runner access may differ.
- eMAG: direct eMAG offers only. Ozone: direct Ozone offers only. Plesio: visible EUR price, not legacy currency metadata. Plesio and Technomarket offers without explicit new-condition evidence are shown as unconfirmed, outside recommendations.
- ZORA returned 403; Technopolis disallows this crawler in robots.txt. Not enabled. Mobile operators remain outside normal retail comparisons.
- Automation: 12:07 Europe/Sofia; manual dispatch supported; changes to retailer code/catalog configuration also trigger a scan. Data commits do not trigger another scan. No dependencies or paid APIs.
- First scan for all six retailers should be checked under GitHub Actions after publishing these changes. Use the deployed data/run_status.json to confirm Pages picked up the data commit.
- See README for adapter maintenance and Cloudflare build settings.
