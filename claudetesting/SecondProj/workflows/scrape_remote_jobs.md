# Scrape Remote Job Listings to Google Sheet (one-time)

## Objective
Scrape the first N pages of https://dailyremote.com/remote-jobs and deliver every
listing field as a Google Sheet. One-time; no scheduling.

## Required inputs
- Base URL and page range (default: 1-5)
- `.env`: FIRECRAWL_API_KEY
- Google Drive connector available in the Claude session

## Credit budget (Firecrawl)
1 credit per page scraped (failures also cost 1). 5 pages = 5 credits. Cached in
.tmp/pages/, so re-runs cost 0. Show the estimate and wait for a go-ahead.
Do not use JSON-extraction mode (+4 credits/page) without asking.

## Steps
1. Scrape page 1 (1 credit) and check the card structure and field list.
2. Scrape the remaining pages:
   `.venv/bin/python tools/scrape_listings.py <base-url> <first> <last>`
3. Parse: `.venv/bin/python tools/parse_jobs.py <first> <last>`
   -> .tmp/jobs.csv. Check rows per page (30 expected), blank counts, no duplicate URLs,
   and spot-check 5 rows against the live site.
4. Copy the CSV to output/dailyremote_jobs_<date>.csv.
5. Create the Sheet: Drive connector `create_file`, contentMimeType text/csv
   (converts to a Google Sheet). Read it back and confirm the range is A1:O<rows+1>.
   Formatting (header style, widths, frozen row, filter) needs an .xlsx upload, see Lessons learned.
6. Give the user the Sheet link and the local path.

## Output columns
title, company, job_type, posted, location, salary, experience, category, role,
skills_tags, description, job_url, apply_url, source_page, scraped_on

## Edge cases
- Bot-check or blocked page: the scraper skips pages under 500 chars; note the gap.
- Salary has no currency symbol or an unusual format: extend the SALARY regex in
  parse_jobs.py and re-parse (free).
- Fewer than 30 jobs on a page: check for a parse miss before trusting the count.

## Lessons learned
- Pagination is ?page=N; pages 1-5 each had 30 distinct jobs.
- Only ~10 of 150 jobs show a company; the rest are "Company hidden" (premium paywall),
  and have no logo.
- Location, salary and experience are concatenated on one line with no separators
  (e.g. "Philippines50000 - 60000 per month2-5 yrs exp"), so the parser splits by regex.
- Markdown escapes (\#) and a trailing "Premium" tag appear in titles and descriptions;
  the parser strips them.
- Passing a ~95 KB CSV through create_file works, but costs ~35k tokens of context.
- A CSV upload gives an unformatted Sheet (sheet tab named "Untitled", no header styling).
  The Drive connector cannot format cells. Formatting in place needs the Google Sheets editing
  connector (get_spreadsheet / update_spreadsheet); it was not available in the first run, so the
  Sheet was left unformatted. Check for it before step 5 and, if present, create a blank Sheet,
  write values with update_values, then format with sheets_helper.py.
- First run (2026-10-15): 150 jobs, 5 credits, Sheet delivered unformatted.
