"""Scrape listing pages with Firecrawl into cached markdown.

Usage: python tools/scrape_listings.py <base-url> <first-page> <last-page>
Example: python tools/scrape_listings.py https://dailyremote.com/remote-jobs 1 5
Output: .tmp/pages/listing-<N>.md (cached pages are skipped, 0 credits).
Cost: 1 credit per page (failed pages still cost 1).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _firecrawl import ROOT, add_credits, post  # noqa: E402


def page_url(base: str, n: int) -> str:
    if n == 1:
        return base
    return f"{base}{'&' if '?' in base else '?'}page={n}"


def main(base: str, first: int, last: int) -> None:
    out_dir = ROOT / ".tmp" / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in range(first, last + 1):
        out = out_dir / f"listing-{n}.md"
        if out.exists():
            print(f"cached: {out}")
            continue
        url = page_url(base, n)
        try:
            data = post("scrape", {"url": url, "formats": ["markdown"], "onlyMainContent": True}).get("data", {})
        except SystemExit as e:  # one failed page must not abort the batch
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
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
