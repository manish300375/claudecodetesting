"""Validate and save one competitor's research JSON to .tmp/competitors/<slug>.json.

Usage: python tools/save_research.py <path-to-json>   (or pipe JSON on stdin with "-")
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".tmp" / "competitors"
REQUIRED = ["name", "website", "category", "positioning", "offerings", "pricing",
            "target_customer", "strengths", "weaknesses", "recent_news", "sources"]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main(src: str) -> None:
    data = json.loads(sys.stdin.read() if src == "-" else Path(src).read_text())
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        raise SystemExit(f"Missing fields: {', '.join(missing)}")
    if not data["sources"]:
        raise SystemExit("sources must list at least one URL")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{slugify(data['name'])}.json"
    path.write_text(json.dumps(data, indent=2))
    print(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
