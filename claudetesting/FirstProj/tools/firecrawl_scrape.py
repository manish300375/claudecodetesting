"""Scrape pages with Firecrawl into cached markdown.

Usage: python tools/firecrawl_scrape.py <competitor-slug> <url> [<url> ...]
Output: .tmp/pages/<competitor-slug>/<page>.md (main content only; cached URLs are skipped, 0 credits).
Cost: 1 credit per page (failed pages such as 403/404 still cost 1).
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _firecrawl import ROOT, add_credits, post  # noqa: E402


def page_name(url: str) -> str:
    u = urlparse(url)
    return re.sub(r"[^a-z0-9]+", "-", (u.netloc + u.path).lower()).strip("-")[:100]


def main(slug: str, urls: list) -> None:
    out_dir = ROOT / ".tmp" / "pages" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for url in urls:
        out = out_dir / f"{page_name(url)}.md"
        if out.exists():
            print(f"cached: {out}")
            continue
        try:
            data = post("scrape", {"url": url, "formats": ["markdown"], "onlyMainContent": True}).get("data", {})
        except SystemExit as e:  # one unsupported/blocked site must not abort the batch
            print(f"FAILED: {url}: {e}")
            continue
        total = add_credits(1)
        status = data.get("metadata", {}).get("statusCode")
        md = data.get("markdown") or ""
        if len(md) < 500 or (status and status >= 400):  # tiny pages are usually bot-check screens
            print(f"FAILED or blocked ({status}, {len(md)} chars): {url}  [{total} credits used]")
            continue
        out.write_text(f"<!-- source: {url} -->\n{md}")
        print(f"{out} ({len(md)} chars, {total} credits used this run)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
