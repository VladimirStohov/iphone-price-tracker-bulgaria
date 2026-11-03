# Project status — 2026-11-03

## Verified implementation

- Architecture: Python standard library → GitHub Actions → append-only JSON change observations → Cloudflare Pages Git integration (pending connection) → vanilla HTML/CSS/JS dashboard.
- Repository: https://github.com/VladimirStohov/iphone-price-tracker-bulgaria — public repository and all 23 source/data files published and read back from main; initial commit c128fe326bd36756a72887522ed10d5f0d3dedc8 verified.
- Public website: **not deployed**; do not invent a Pages URL.
- 38 accepted model/storage configurations, 12 model names, generations 15/16/17. Actual discovered coverage: 6 configurations.
- Initial live scan: 2026-11-03 18:09–18:11 UTC (20:09–20:11 Sofia), 2 retailers returned real product prices.
- Accepted data after duplicate validation: 14 unique offers, 8 explicitly confirmed new (iSTYLE), 6 condition-unconfirmed (Ardes); 0 observed price reductions, 0 claimed active promotions.
- iSTYLE initial scan partial: 2 HTTP 429 responses; subsequent GitHub run succeeded. New scanner now stops all additional requests to a host after 403/429; no bypass. Delay increased to 5 seconds for future scans.
- Ardes: 6 extracted offers; explicit NewCondition absent, so excluded from new-device recommendations.
- Local tests: 16 passed; JavaScript syntax and static build passed. Browser QA unavailable: browser tool failed twice with “failed to write kernel assets … path not found”.

## Not yet verified / blockers

- Manual workflow_dispatch verified successful: run 41694748396, 2026-11-03 18:32–18:34 UTC (20:32–20:34 Sofia). All 16 tests, scan, data commit and push succeeded. iSTYLE: 10 confirmed-new offers; Ardes: blocked by HTTP 403 on GitHub runner, prior prices retained stale. New reductions: 0. Scheduled invocation itself has not yet occurred.
- Cloudflare account is signed in according to user, but unavailable to automation due to browser-tool infrastructure failure. Official Git integration and first deployment still required.
- The connected GitHub plugin has no repository-creation or workflow_dispatch operation. User created the public repository with README. Source can be published through Git tree/commit APIs.
- Nine other shortlisted retailers/operators are **not implemented**, not falsely counted as monitored or failed live integrations. Two initial adapters are enabled; latest iSTYLE scan succeeded, Ardes is blocked from GitHub runners (403) and is not eligible for confirmed-new recommendations.
- Discovery is bounded and not exhaustive. Colour extraction is limited to explicit JSON-LD. Retailer-specific promotions beyond structured strikethrough priceSpecification need adapters. No retailer explicit promotion dates found.
- Only one observation period exists; no price trend or historical discount is asserted. No browser/runtime/public-deployment verification yet.

## Automation and maintenance

Workflow: `.github/workflows/daily_price_scan.yml`, schedule **12:07 Europe/Sofia** (non-zero minute, DST-aware; execution can be delayed), modes full/retry_failed/selected_stores. Python dependencies: none beyond Python 3.12 standard library. No paid APIs or LLM execution.

Manual request: “Jarvis, analyze iPhone prices in Bulgaria today.” Read this file first; dispatch the existing workflow if supported. Otherwise use https://github.com/VladimirStohov/iphone-price-tracker-bulgaria/actions/workflows/daily_price_scan.yml . Never claim a dispatch succeeded without a returned GitHub run.

Cloudflare setup: Pages → Git integration → this repository → main → `python build.py` → output `dist`. After deployment, record the real URL in site.json and here, trigger Actions, confirm a new data commit produces a new Pages deployment and updated timestamp.

Adding retailers: see README; inspect only the adapter, relevant fixtures and common logic when repairing a specific store. Keep history, preserve stale prices, and report partial failures.
