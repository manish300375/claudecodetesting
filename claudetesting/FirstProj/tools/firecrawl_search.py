"""Run a Firecrawl web search and save url/title/description results.

Usage: python tools/firecrawl_search.py "<query>" [--limit 10]
Output: .tmp/search/<slug>.json (cached: an existing file is reused, costing 0 credits).
Cost: 2 credits per 10 results.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _firecrawl import ROOT, add_credits, post  # noqa: E402


def main(query: str, limit: int) -> None:
    out = ROOT / ".tmp" / "search" / (re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:80] + ".json")
    if out.exists():
        print(f"cached: {out}")
        return
    resp = post("search", {"query": query, "limit": limit})
    results = [{"url": r.get("url"), "title": r.get("title"), "description": r.get("description")}
               for r in resp.get("data", {}).get("web", [])]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"query": query, "results": results}, indent=2))
    used = resp.get("creditsUsed", 2 * -(-limit // 10))
    print(f"{out} ({len(results)} results, {used} credits, {add_credits(used)} used this run)")


if __name__ == "__main__":
    args = sys.argv[1:]
    limit = 10
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        raise SystemExit(__doc__)
    main(args[0], limit)
