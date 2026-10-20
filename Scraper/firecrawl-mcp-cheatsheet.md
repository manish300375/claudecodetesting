# Firecrawl MCP Cheat Sheet

As of 2026-10-20. Source: tool descriptions from the connected Firecrawl MCP server. Credit costs per tool are not listed there; check the Firecrawl pricing page.

## Overview

Firecrawl MCP gives Claude 28 tools to search the web, read pages, map and crawl sites, extract structured data, drive a live browser, monitor changes and run research. It covers everything from a one-page lookup to a multi-site dataset.

| Capability | What it does |
| --- | --- |
| Read | Scrape one URL into markdown, HTML, JSON, screenshots, links or a targeted answer; parse local PDFs, Word and spreadsheet files |
| Find | Web, news and image search; developer, legal and academic search; a catalogue of data providers (Alexandria) |
| Cover a site | Map lists URLs without content; crawl collects many pages |
| Research | An agent that searches, navigates and returns structured JSON across several sources |
| Act | Click, type and run code in a live browser session |
| Watch | Recurring monitors that diff pages or search results and notify by email or webhook |
| Account | Check credit balance and historical usage |

**Setup in this project.** `run-firecrawl-mcp.sh` loads `FIRECRAWL_API_KEY` from a local `.env` file, then starts the server with `npx -y firecrawl-mcp`. Keep `.env` out of git.

## Tool map

All 28 tools, grouped by job. Names are prefixed `firecrawl_` in the MCP server.

| Group | Tool | What it does |
| --- | --- | --- |
| Read | scrape | One URL to markdown, HTML, JSON, screenshot, links, images, summary, branding, audio or a targeted answer |
| Read | parse | A local PDF, DOCX, DOC, ODT, RTF, XLSX, XLS or HTML file to the same outputs |
| Search | search | Web, news and image results, plus matching Alexandria data providers |
| Search | developer_search | Public repos, GitHub issues, merged PRs, READMEs and code docs |
| Search | gov_search | US federal, state and local statutes, regulations, court opinions |
| Search | research_search_papers | PubMed, bioRxiv, medRxiv and arXiv abstracts, filterable by author, category and date |
| Search | research_read_paper, research_inspect_paper, research_related_papers | Read, inspect and find papers related to a result |
| Search | find_tools | Free discovery of Alexandria providers and their contracts |
| Site | map | List URLs under a site, optionally filtered by a search term, without fetching content |
| Site | crawl | Collect content from many pages, bounded by paths, depth and page limit |
| Site | check_crawl_status | Check a crawl by ID |
| Research | agent | Autonomous multi-source research that returns structured JSON |
| Research | agent_status | Poll an agent job until it completes or fails |
| Act | interact | Live browser session: navigate, click, fill, or run Bash, Python or Node code |
| Act | interact_stop | End a live browser session |
| Watch | monitor_create, monitor_get, monitor_list, monitor_update, monitor_delete | Manage recurring scrape, crawl or search monitors |
| Watch | monitor_run, monitor_check, monitor_checks | Trigger a check, read one check, list a monitor's checks |
| Account | credit_usage | Remaining credits, plan credits, billing period and historical usage |
| Feedback | feedback, search_feedback | Optional quality feedback on scrapes and searches |

## Which tool to use

Start with the cheapest tool that answers the question: scrape for a known URL, search for an unknown one, agent only when the answer spans several sites.

| If you need | Use | Notes |
| --- | --- | --- |
| Content of one known page | scrape | Add `formats: json` with a schema for fields |
| Content of a local file | parse | Hosted MCP needs a two-call upload |
| An answer, source not known | search | Add `scrapeOptions` to fetch page content in the same call |
| All URLs on a site | map | No page content returned |
| Content from many pages | crawl | Set `limit` and `includePaths` to control cost |
| A page behind clicks, forms or logins | interact | Acts on the live site; can submit forms |
| A dataset or entity facts across sites | agent | Async: poll `agent_status`, usually 1 to 3 minutes |
| Code, library or error-message answers | developer_search | Or search with `categories: developer` |
| Statutes and regulations (US) | gov_search | Verify jurisdiction and effective date |
| Biomedical or arXiv papers | research_search_papers | Not the same as search with `categories: research` |
| Same fields across many entities | find_tools, then scrape with `alexandria` | Typed, sourced records; discovery is free |
| Know when a page or result changes | monitor_create | Email or webhook notifications |
| Remaining credits | credit_usage | Current or historical view |

## Scrape: formats and options

`scrape` takes one `url` and returns whatever formats you list; the default is markdown. The same options apply inside crawl (`scrapeOptions`) and search (`scrapeOptions`).

**Formats**

| Format | Returns |
| --- | --- |
| markdown | Clean page text (default) |
| html, rawHtml | Processed or raw HTML |
| links, images | URLs found on the page |
| summary | Short summary of the page |
| json | Structured fields; set `jsonOptions.prompt` and `jsonOptions.schema` |
| query | A targeted answer; set `queryOptions.prompt`, mode `directQuote` or `freeform` |
| screenshot | Image; `screenshotOptions`: fullPage, quality, viewport |
| branding | Brand data such as colors and fonts |
| changeTracking | Diff against the previous scrape |
| audio | Audio version of the page |

**Options**

| Option | Purpose |
| --- | --- |
| onlyMainContent | Strip navigation and footers |
| includeTags, excludeTags | Keep or drop HTML elements by tag |
| waitFor | Milliseconds to wait for JavaScript rendering |
| maxAge | Accept cached content up to this age in ms; 0 forces a live fetch |
| mobile | Render as a mobile device |
| proxy | basic, stealth, enhanced or auto for harder sites |
| location | country and languages to emulate |
| parsers, pdfOptions | pdf parsing; `maxPages` caps pages |
| actions | Pre-scrape steps: wait, click, write, press, scroll, screenshot, scrape, executeJavascript, generatePDF |
| redactPII | Redact personal data in returned content |
| removeBase64Images | Drop inline images to shrink output |
| zeroDataRetention | No retention; needs an eligible account |
| profile | Named browser profile; `saveChanges` persists session state |
| skipTlsVerification, storeInCache, lockdown | Boolean flags: ignore TLS errors, store the result in cache, lockdown mode (see Firecrawl docs) |

**Example: extract fields**

```json
{
  "url": "https://example.com/pricing",
  "formats": ["json"],
  "jsonOptions": {
    "prompt": "Extract plan names and monthly prices",
    "schema": {"type": "object", "properties": {"plans": {"type": "array"}}}
  },
  "maxAge": 0
}
```

## Search, map and crawl

**search** returns ranked web results and, when authenticated, matching Alexandria data providers in `data.tools`.

| Parameter | Purpose |
| --- | --- |
| query | Supports quoted phrases, `-term`, `site:`, `inurl:`, `intitle:`, `related:` |
| sources | web, images, news, alexandria, exchange |
| categories | research, pdf, developer, gov (gov cannot be combined) |
| limit | 1 to 100 results |
| includeDomains, excludeDomains | Hostname allow or block list; mutually exclusive |
| location, tbs | Geo targeting and time filter |
| highlights | Query-relevant excerpts in descriptions (on by default) |
| scrapeOptions | Fetch page content for each result in the same call |
| toolDetail | compact, summary or full detail for provider matches |

**map** lists URLs without fetching content.

| Parameter | Purpose |
| --- | --- |
| url | Site to enumerate (required) |
| search | Narrow the list to a topic |
| sitemap | include, skip or only |
| includeSubdomains, ignoreQueryParameters | Coverage controls |
| limit | Cap the number of URLs |

**crawl** starts a multi-page crawl, polls to completion and returns the data. Use `check_crawl_status` for a crawl ID.

| Parameter | Purpose |
| --- | --- |
| url | Starting point (required) |
| limit | Maximum pages; keep it low to control credits |
| includePaths, excludePaths | Path patterns to keep or skip |
| maxDiscoveryDepth | How deep to follow links |
| crawlEntireDomain | Follow links beyond the start path |
| allowSubdomains, allowExternalLinks | Widen scope |
| sitemap | skip, include or only |
| deduplicateSimilarURLs, ignoreQueryParameters | Reduce repeated pages |
| delay, maxConcurrency | Throttle the crawl |
| scrapeOptions | Same options as scrape |
| prompt | Natural-language crawl guidance |
| webhook, webhookHeaders | Notify an endpoint (unavailable in safe mode) |

Typical flow: map to find the URLs, then scrape the few you need. That costs less than crawling a whole site.

## Agent, interact, monitor and parse

**agent** runs multi-source research and returns JSON. It returns a job ID; read the result with `agent_status` until the job is completed or failed (typically 1 to 3 minutes).

| Parameter | Purpose |
| --- | --- |
| prompt | The fields or dataset you want (required, up to 10,000 characters) |
| schema | JSON schema for the output |
| urls, strictConstrainToURLs | Seed pages; restrict the agent to them |
| effort | low, medium or high reasoning budget |
| maxCredits | Spending cap for the run (API default 2,500) |
| mode | extract (default) or chat for short follow-up replies |
| threadId | Continue an earlier thread with a follow-up prompt |
| exchange | Alexandria settings: enabled, toolkits (up to 5), maxCalls (up to 30), onTermsRequired, requireApproval |

**interact** opens or reuses a live browser session. It acts on the real site, so a form submission can have lasting effects. Stop sessions with `interact_stop`.

| Parameter | Purpose |
| --- | --- |
| url or scrapeId | Page to open, or a prior scrape to continue from (one is required) |
| prompt or code | Natural-language instruction, or code to run |
| language | bash, python or node for code |
| timeout | 1 to 300 seconds |
| scrapeOptions | Same options as scrape |

**monitor** compares each scheduled check with the previous one.

| Tool | Purpose |
| --- | --- |
| monitor_create | Simple form: `page`/`pages` (or `queries`) plus a `goal`; optional scheduleText, timezone, email, webhookUrl, includeDiffs, searchWindow (5m to 7d), maxResults (up to 50), include and exclude domains. Advanced form: a `body` object |
| monitor_list, monitor_get | List monitors or read one |
| monitor_update, monitor_delete | Change or remove a monitor |
| monitor_run | Trigger a check now |
| monitor_checks, monitor_check | List past checks or read one |

**parse** converts a local file: .html, .htm, .pdf, .docx, .doc, .odt, .rtf, .xlsx, .xls. It accepts the same formats as scrape except screenshot, images, branding and changeTracking, plus `pdfOptions.maxPages` and `redactPII`. With the hosted server, call once with `filePath` to get upload instructions, upload, then call again with the returned `uploadRef`. Remote web URLs go to scrape instead.

## Specialty search and Alexandria

Four dedicated search tools cover code, law and science; Alexandria covers structured data about companies, people, jobs, filings, real estate, prices and more.

| Tool | Searches | Key parameters |
| --- | --- | --- |
| developer_search | Public repos, GitHub issues, merged PRs, READMEs, code docs | query, k (up to 100), `skills: only` for agent-skill files |
| gov_search | US federal, state and local primary law | query, k (up to 100); state the jurisdiction and as-of date |
| research_search_papers | PubMed, bioRxiv, medRxiv, arXiv | query, k (up to 500), authors, categories such as cs.LG, from and to dates |
| find_tools | Alexandria providers and contracts | query, urls, categories, providers, capabilities, includeCosts |

**Alexandria workflow**

1. Run search or find_tools to discover a provider and capability.
2. Read the contract: inputs, outputs, and any costs (`includeCosts`).
3. Execute with scrape using `alexandria: {provider, capability, options}`. Up to 10 capabilities per call.
4. Some providers need terms accepted by an organization admin in the Firecrawl dashboard before use.

Alexandria access needs an API key on a team with it enabled. Use it when you need the same fields across many entities, exact figures with provenance, or large record sets.

## Tips and gotchas

- **Control cost.** Set `limit` on crawl and map, `maxCredits` on agent, and check `credit_usage` before large jobs.
- **Freshness.** Results can come from cache. Use `maxAge: 0` on scrape for a live fetch.
- **Prefer JSON over markdown** when you need specific fields; it is shorter and easier to use.
- **Hard pages.** Try `waitFor`, then proxy `stealth` or `enhanced`, then interact.
- **Side effects.** interact and monitor_create change the outside world: forms get submitted and checks get scheduled. Confirm before using them.
- **Async tools.** agent and crawl are polled: use `agent_status` and `check_crawl_status`.
- **Secrets.** Keep the API key in `.env`, never in committed files or prompts.
- **Credits.** If Firecrawl reports credits ran out or a daily limit, it provides a link to continue.
