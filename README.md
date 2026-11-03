# iPhone Price Tracker Bulgaria

Automated historical price monitoring and deal tracking for iPhone 15, 16 and 17 models across reputable Bulgarian retailers.

**Deployment is not complete. Read [PROJECT_STATUS.md](PROJECT_STATUS.md) for verified state and blockers.**

## Architecture

Public GitHub source + JSON observations → ordinary Python GitHub Actions scan → commit data → Cloudflare Pages official Git integration → static HTML dashboard. No LLM calls, API subscriptions, backend or external database. Python 3.12+ standard library only; no dependency installation is necessary.

The initial scope is **iSTYLE and Ardes**, with bounded discovery of product pages. This is deliberately not all Bulgarian retailers or all colours/storage variants. Other shortlisted retailers and operators are not implemented. Model parsing supports 38 manufacturer model/storage combinations across the requested 12 models; this is not a claim that all combinations were discovered in stores. The official name “iPhone Air” is used; “iPhone 17 Air” is accepted as an input alias.

## Start and maintain

```sh
python -m unittest discover -s tests -v
python -m tracker.scan --mode full
python -m tracker.scan --mode retry_failed
python -m tracker.scan --mode selected_stores --stores istyle
python build.py
python -m http.server 8000 --directory dist
```

The deployed website needs no local computer. Local commands are for maintainers, not daily users.

Files: `tracker/core.py` normalization/history/validation; `tracker/http.py` polite allowlisted HTTP client; `tracker/adapters/` one adapter per retailer; `tracker/scan.py` independent store failures and atomic JSON writes; `data/` public observations and scan report; `index.html`, `app.js`, `style.css` static English dashboard; `build.py` Cloudflare packaging.

## Daily and on-demand scans

`.github/workflows/daily_price_scan.yml` supports `workflow_dispatch` with `full`, `retry_failed`, and `selected_stores`. The schedule is **12:07 Europe/Sofia**, using GitHub's native IANA-timezone scheduling with DST. Seven minutes after noon implements the requested non-zero minute; it is not exactly 12:00. GitHub schedules can be late and are not an uptime guarantee. Public repository schedules can be disabled after inactivity; check Actions if runs stop. Actual start/end timestamps are recorded.

“Jarvis, analyze iPhone prices in Bulgaria today” means dispatch the existing workflow, wait for completion, read `data/run_status.json`, and report the verified website URL. Do not recreate the project or ask an AI to scrape each product. If the connected tools cannot dispatch, link to the Actions workflow. A manually requested scan is not started until GitHub accepts dispatch.

## Cloudflare Pages setup

Use **official Git integration**, not Direct Upload: Workers & Pages → Create application → Pages → Connect to Git → choose this repository. Production branch: `main`; framework: None; build command: `python build.py`; build output: `dist`; root directory: repository root. Authorize Cloudflare only for this repository. No paid plan or custom domain is required. No API token is needed for Git integration.

After the first deployment, put the actual deployed URL in `site.json`, confirm a data commit triggers another Pages deployment, and update PROJECT_STATUS. The repository URL alone is not a working website. The existing data remains available even when a scanner fails. `_headers` disables persistent JSON caching, and browser reads use `cache: no-store`.

## Data integrity and discounts

* Store only explicit EUR prices. Missing currency or BGN-only prices are rejected, not guessed or converted.
* Match exact model + storage. Preserve separate product URLs/colours and actual seller evidence. The same product represented by ProductGroup and Product JSON-LD is one offer, not two.
* Confirm “new” only from explicit `NewCondition` source evidence. Ardes currently omits that field; those prices are labelled **condition unconfirmed** and excluded from new-device recommendations.
* Seller may come from the Offer or the same-domain Organization on the product page; its evidence is recorded. Marketplace and operator adapters are not enabled.
* Advertised strikethrough `priceSpecification` is a reference price, never a verified prior selling price. Other retailer-specific old-price markup is not yet extracted. `priceValidUntil` is preserved separately and **not misrepresented as a promotion end date**. Missing promotion dates remain unspecified.
* Price history is append-only after validation. Append price/offer changes; unchanged checks update current `verified_at` and run status, not fake daily history. No generated historical prices. Initial pre-publication validation collapsed identical duplicate JSON-LD presentations; no price change was discarded.
* New drop = lower than the preceding successful observation of the same offer. Historical-low eligibility requires ≥2 prior samples spanning ≥1 day. 30-day average requires ≥3 samples spanning ≥7 days, and is observation-weighted, not a daily/time-weighted average. Low/high values describe recorded observations only; coverage gaps remain gaps.
* Advertised promotions and historical-low flags are separate from the price-change classification. Promotion metadata and disappearances are stored in change observations; missing or blocked pages do not imply a promotion ended.
* A price change over 40% is quarantined; keep the prior accepted price stale until a maintainer verifies it. This protects against parsing failures without silently accepting a suspicious change.
* A failed/partial product check does not delete old data or refresh its timestamp. Unseen old offers become stale; a bounded catalog scan cannot prove an offer disappeared. The UI also marks prices older than 36 hours stale and excludes them from recommendations.

## Crawling limits

Read robots.txt before product requests. Same-domain HTTPS only; no login, CAPTCHA bypass, proxy rotation, hidden APIs or browser scraping. Cache pages within a run, set timeouts and size limits, honour crawl delay. HTTP 403/429 stops further requests to that retailer for the run. Shopify collection pagination/full inventory discovery is not implemented. Automatic retries are intentionally disabled after rate limits. Inspect retailer terms before expanding collection. A public page and permissive robots.txt do not constitute legal permission; no legal-compliance claim is made.

## Adding a retailer

First verify its business identity, public new-iPhone listing, actual seller, product condition, EUR pricing, robots and terms. Add a small adapter in `tracker/adapters/`, explicit domain/listings in stores.json, and register it in ADAPTERS. Add sanitized fixtures and tests. Test a small real scan before advertising coverage. Treat operators/subscription offers and marketplace partners as separate channels, never ordinary retail recommendations.

## Primary references

* [Apple model identification and capacities](https://support.apple.com/en-us/108044)
* [iPhone 15 specs](https://support.apple.com/en-us/111831), [15 Pro Max](https://support.apple.com/en-us/111828)
* [iPhone 16 specs](https://support.apple.com/en-us/121029), [16 Pro](https://support.apple.com/en-us/121031)
* [iPhone 17 specs](https://support.apple.com/en-us/125089), [iPhone Air](https://www.apple.com/iphone-air/specs/)
* [GitHub schedule semantics/timezones](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
* [Cloudflare Pages official Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/)

No LICENSE file is included: no licence was selected or approved. No credentials, cookies, access tokens, local browser profiles or private account data belong in this repository.
