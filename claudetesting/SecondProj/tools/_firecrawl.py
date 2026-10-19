"""Shared Firecrawl helpers: API key, POST with retry, and a credit ledger in .tmp/credits.json."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / ".tmp" / "credits.json"
API = "https://api.firecrawl.dev/v2"


def post(endpoint: str, body: dict, retries: int = 2) -> dict:
    load_dotenv(ROOT / ".env")
    key = os.getenv("FIRECRAWL_API_KEY")
    if not key:
        raise SystemExit("FIRECRAWL_API_KEY is not set in .env")
    for attempt in range(retries + 1):
        r = requests.post(f"{API}/{endpoint}", json=body, headers={"Authorization": f"Bearer {key}"}, timeout=120)
        if r.status_code == 429 and attempt < retries:  # rate limited: back off, don't fail
            time.sleep(10 * (attempt + 1))
            continue
        if not r.ok:
            raise SystemExit(f"Firecrawl {endpoint} failed: {r.status_code} {r.text[:300]}")
        return r.json()
    raise SystemExit("Firecrawl rate limit persisted")


def add_credits(n: int) -> int:
    total = (json.loads(LEDGER.read_text())["used"] if LEDGER.exists() else 0) + n
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps({"used": total}))
    return total
