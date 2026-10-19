# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Inherits the WAT framework and shared guidelines from `../CLAUDE.md`.

**Current state:** one workflow exists, `workflows/competitor_analysis.md`, with its tools in `tools/` (see "Project" below). Create new `tools/` scripts only when nothing suitable exists, and ask before creating or overwriting any workflow (unless explicitly told to).

## Project: One-Time Competitor Analysis Report

Takes the user's business profile and brand assets, researches **exactly 3 competitors**, and produces a branded PDF (logo, colors, typography). It is one-time: no scheduling or recurring monitoring. Follow `workflows/competitor_analysis.md` and read its "Lessons learned" before running.

**Tools** (all run with `.venv/bin/python tools/<name>.py`):
- `load_brand.py`: validates `brand/` (logo, optional `logo_light` for the dark cover, fonts, colors)
- `firecrawl_search.py`, `firecrawl_scrape.py`: Firecrawl search and scrape; results cached in `.tmp/`, so retries are free (`_firecrawl.py` is the shared helper)
- `clean_page.py`: strips images/links from scraped markdown before reading
- `save_research.py`: validates and saves per-competitor JSON
- `build_report_pdf.py`: renders the PDF with ReportLab
- `upload_to_drive.py`: optional Google Drive upload (untested; needs `credentials.json` and `DRIVE_FOLDER_ID`)

**Decisions already made (don't re-litigate):**
- Firecrawl for search and scraping (not built-in WebSearch/WebFetch).
- ReportLab for PDFs. WeasyPrint was rejected: it needs Pango, and Homebrew has no bottles for macOS 14.
- Exactly 3 competitors; no monitoring/scheduling.

**Cost rules (Firecrawl):** search = 2 credits per 10 results, scrape = 1 credit per page (failures still cost 1). Free tier is 1,000 credits/month; a typical run uses ~30-140. Before scraping, show the user the 3 chosen competitors and the credit estimate and wait for a go-ahead. Never use enhanced or JSON extraction modes (+4 credits/page) without asking.

**Before delivering:** rasterize every page of the PDF with `pymupdf` and look at each one. Mark third-party or unverified figures (especially prices) as such in the report.

**Test data:** `brand/`, `inputs/business_profile.md` currently hold a dummy company (BrightBean Coffee). Replace them with the user's real assets for a real run.

**Setup:** `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`; put `FIRECRAWL_API_KEY` in `.env` (see `.env.example`). Never read or print `.env`.

## File Structure

- **Deliverables:** the final PDF is saved to `output/` (gitignored) and, when Drive is configured, uploaded to Google Drive for the user. Share the local path and the Drive link.
- **Intermediates:** temporary, regenerable processing files

```
.tmp/           # Temporary files (search results, scraped pages, analysis JSON, credit ledger). Disposable.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
brand/          # logo.png, logo_light.png, fonts/*.ttf, brand.json, brand_guidelines.md
inputs/         # business_profile.md
output/         # Final PDFs (gitignored)
requirements.txt, .venv/
.env            # API keys and environment variables (NEVER store secrets anywhere else); .env.example lists the names
credentials.json, token.json  # Google OAuth (gitignored)
```
