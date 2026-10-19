# Competitor Analysis & Branded Report (one-time)

## Objective
Given the user's business profile and brand assets, analyze **3 competitors**, find what's working for them and where the user can improve, and deliver a branded PDF (logo, colors, typography). One-time report; no monitoring or scheduling.

## Required inputs
- `inputs/business_profile.md` (fill every field; ask the user for any that are blank)
- `brand/logo.(png|jpg|svg)`, optional `logo_light` (white/reversed logo, used on the dark cover; a dark logo disappears on the primary-color cover), `brand/fonts/*.ttf` (optionally `body_bold_file`, else bold text isn't bold), `brand/brand.json` (colors, font files)
- `.env`: `FIRECRAWL_API_KEY`; optional `DRIVE_FOLDER_ID` + `credentials.json` for Drive upload

## Setup (once)
- `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- PDFs use ReportLab (pure Python, no system libs). WeasyPrint was tried first but needs Pango, and Homebrew has no bottles for macOS 14 (it would compile ~10 packages from source).

## Credit budget (Firecrawl)
Search = 2 credits per 10 results. Scrape = 1 credit per page (failed 403/404 pages still cost 1). Expected total for 3 competitors: ~30 (lean) to ~140 (heavy) credits; the free tier gives 1,000/month. `.tmp/credits.json` tracks credits used this run. Tools cache results, so re-running never re-spends credits. Do not use paid extras (enhanced mode, JSON extraction) without asking the user.

## Steps
1. **Brand check:** `.venv/bin/python tools/load_brand.py`. Fix anything it reports first.
2. **Discover:** from the profile, write ~8-15 queries ("alternatives to X", category + customer + geography, "X vs Y", review sites). Run each: `.venv/bin/python tools/firecrawl_search.py "<query>"`. Read `.tmp/search/*.json`. Pick exactly **3 competitors** (mix of direct / indirect / emerging, or the 3 closest if the user named them). **Show the user the 3 and the credit estimate; wait for a go-ahead before scraping.**
3. **Collect:** for each competitor run `.venv/bin/python tools/firecrawl_scrape.py <slug> <url> ...` with ~5-7 URLs (home, pricing, product/features, about, blog, 1-2 review/news pages). Output goes to `.tmp/pages/<slug>/*.md`. Pages that fail are reported; note the gap, don't guess.
4. **Analyze:** read the cached pages through `.venv/bin/python tools/clean_page.py <page.md>` (strips images/links; raw pages are mostly noise). For each competitor write a JSON file and save it with `.venv/bin/python tools/save_research.py <file>` (fields: name, website, category, positioning, offerings, pricing, target_customer, strengths, weaknesses, recent_news, sources). Then write `.tmp/analysis.json`: title, subtitle, date, executive_summary, market_overview, competitors[], comparison{columns, rows[{label, values}]}, whats_working[{competitor, insight, evidence}], opportunities[{title, detail}], recommendations[{title, detail, impact, effort}], what_to_watch[], sources[]. Every claim traces to a source URL; label unverified items and estimates.
5. **Render:** `.venv/bin/python tools/build_report_pdf.py .tmp/analysis.json output/competitor_analysis_<YYYY-MM-DD>.pdf`. Check every page: `pymupdf` can rasterize pages to PNG for viewing. Look at logo, colors, fonts, tables, page breaks.
6. **Deliver:** give the user the local path. If Drive is set up, `.venv/bin/python tools/upload_to_drive.py <pdf>` and share the link.

## Edge cases
- Pricing hidden behind a sales form: record "not public"; use review or third-party figures labeled as estimates.
- Page blocked or login-walled: use an alternate page or source; note the gap in the report.
- Fonts missing (no TTF in brand/fonts): falls back to Helvetica; tell the user.
- API 429: `tools/_firecrawl.py` retries with backoff; if it persists, wait and re-run (cache keeps finished work).

## Lessons learned
- Firecrawl returns 403 "site not supported" for some sites (Serious Eats). Bon Appetit and My Subscription Addiction worked. The scrape tool skips failed URLs and continues, and costs 1 credit even on failure.
- Some pages return a bot-check screen instead of content (lowkeycoffeesnobs.com). The scrape tool refuses pages under 500 chars so they aren't cached as real content.
- Homepages rarely show pricing. Get prices from the site's plan/subscribe page, or from review roundups labeled as unverified third-party figures.
- Raw scraped markdown is ~80% images/nav. Use `tools/clean_page.py` before reading.
- PDF: long cover titles wrap; keep the Sources list short or it can strand a few lines on a nearly empty last page. Always rasterize all pages with pymupdf and look at them.
- Test run (BrightBean dummy profile, 3 competitors): 12 search credits (6 queries) + ~7 scrape credits.
