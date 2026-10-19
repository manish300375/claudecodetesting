# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Inherits the WAT framework and shared guidelines from `../CLAUDE.md`.

## Project: SecondProj

One-time job: scrape job listings from https://dailyremote.com/remote-jobs (first 5 pages) with Firecrawl and deliver them as a Google Sheet. No scheduling.

**Status: complete (2026-10-15).** 150 jobs delivered to [DailyRemote Jobs - Pages 1-5 (2026-10-15)](https://docs.google.com/spreadsheets/d/1WDW2r2csjehvn6erVBtciCU37NX75HR9cT6TS_WQRVM/edit). The Sheet is unformatted by choice (no header style, frozen row or filter; the Google Sheets editing connector was not available). Follow `workflows/scrape_remote_jobs.md` to repeat the run. Only reopen this project if the user asks for more pages, detail-page scraping, or formatting.

## Commands

Setup (once): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`; put `FIRECRAWL_API_KEY` in `.env` (never read or print it).

```
.venv/bin/python tools/scrape_listings.py https://dailyremote.com/remote-jobs 1 5   # 1 credit/page, cached in .tmp/pages/
.venv/bin/python tools/parse_jobs.py 1 5                                            # -> .tmp/jobs.csv + jobs.json (free)
```

`tools/_firecrawl.py` is copied from FirstProj (retry on 429, credit ledger in `.tmp/credits.json`).

## Decisions already made

- Firecrawl markdown scrape + deterministic parser (no JSON-extraction mode, which costs +4 credits/page).
- Listing pages only (no detail pages). Sheet is created through the Google Drive connector by uploading the CSV (`create_file`, `text/csv` converts to a Google Sheet); no OAuth setup.
- Pagination is `?page=N` (verified: pages 1-5 each return 30 distinct jobs).

## Site quirks (DailyRemote listing markdown)

- Each card: `## [Title](job-url)`, then `Company·Type·Posted`, then one concatenated line `<location><salary><experience> [Category](..) [Role](..)`, description, tag links, APPLY link. Fields have no separators, so `parse_jobs.py` splits them with regexes; check new salary/experience formats when re-running.
- Only about 10 of 150 jobs show a company name; the rest are "Company hidden" (premium paywall). The company logo is also missing for those.
- Salary appears with `$`, `€`, or no currency symbol (e.g. `650K per year`), and as ranges or `per hour/month`. Kept as raw text, not normalized.
- Some cards are near-duplicates (same title, different job id); dedupe is by job URL only.

## Cost / rate-limit rules

Firecrawl: 1 credit per page scraped (failures too). Show a credit estimate and wait for a go-ahead before scraping. The 5-page run used 5 credits; re-runs are free thanks to the cache.

## Inputs and outputs

- Env var: `FIRECRAWL_API_KEY` (see `.env.example`).
- Local copy: `output/dailyremote_jobs_<date>.csv`. Deliverable: the Google Sheet "DailyRemote Jobs - Pages 1-5 (2026-10-15)".
