"""Strip images, link URLs and duplicate lines from a scraped markdown page so it's cheap to read.

Usage: python tools/clean_page.py <page.md> [max_chars=6000]
"""
import re
import sys

text = open(sys.argv[1]).read()
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
seen, out = set(), []
for line in text.split("\n"):
    line = line.strip(" -\\")
    if len(line) >= 3 and line not in seen:
        seen.add(line)
        out.append(line)
print("\n".join(out)[:limit])
