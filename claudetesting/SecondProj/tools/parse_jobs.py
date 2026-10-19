"""Parse cached DailyRemote listing pages into jobs.csv / jobs.json.

Usage: python tools/parse_jobs.py [first-page] [last-page]   (default 1 5)
Reads .tmp/pages/listing-<N>.md. Writes .tmp/jobs.csv and .tmp/jobs.json.
Blanks stay blank (nothing is guessed). Duplicates are dropped by job URL.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ["title", "company", "job_type", "posted", "location", "salary", "experience", "category",
          "role", "skills_tags", "description", "job_url", "apply_url", "source_page", "scraped_on"]

TITLE = re.compile(r"^## \[(.+)\]\((https://dailyremote\.com/remote-job/[^)]+)\)\s*$")
LINK = re.compile(r"\[([^\]]+)\]\((https://dailyremote\.com/[^)]+)\)")
SALARY = re.compile(r"(?:[$£€][\d.,]+[KkMm]?(?:\s*[–-]\s*[$£€]?[\d.,]+[KkMm]?)?|\d+[KkMm]\s*[–-]\s*\d+[KkMm]|\d[\d.,]*[KkMm]?(?:\s*[–-]\s*\d[\d.,]*[KkMm]?)?(?=\s*(?:per|/)\s*[a-z]))(?:\s*(?:per|/)\s*[a-z]+)?")
EXPERIENCE = re.compile(r"\d+(?:\s*[-–]\s*\d+)?\+?\s*yrs?\s*exp")
LOGO = re.compile(r"^!\[[^\]]*\]\((https://[^)]+)\)")


def parse_card(lines: list, page: int, today: str) -> dict:
    m = TITLE.match(lines[0])
    title = re.sub(r"\\(.)", r"\1", m.group(1))
    url = m.group(2)
    rows = [l.strip() for l in lines[1:] if l.strip()]
    job = dict.fromkeys(FIELDS, "")
    job.update(title=title, job_url=url, source_page=page, scraped_on=today)

    if len(rows) > 1 and rows[1].startswith("·"):  # hidden-company cards put "Company hidden" on its own line
        rows = [rows[0] + rows[1]] + rows[2:]
    if rows and rows[0].count("·") >= 2:  # "Company·Type·Posted"
        company, job_type, posted = [p.strip() for p in rows[0].split("·", 2)]
        job.update(company=company, job_type=job_type, posted=posted)
        rows = rows[1:]

    # Metadata line: "<location><salary><experience> [Category](..) [Role](..)" with no separators.
    if rows and not rows[0].startswith("[APPLY]"):
        meta = rows[0]
        links = LINK.findall(meta)
        rest = LINK.sub("", meta).strip()
        sal = SALARY.search(rest)
        if sal:
            job["salary"] = sal.group(0).strip()
            rest = rest.replace(sal.group(0), "", 1)
        exp = EXPERIENCE.search(rest)
        if exp:
            job["experience"] = exp.group(0)
            rest = rest.replace(exp.group(0), "", 1)
        job["location"] = rest.strip()
        if links:
            job["category"] = links[0][0]
            job["role"] = "; ".join(t for t, _ in links[1:])
        rows = rows[1:]

    desc, tags = [], []
    for r in rows:
        if r.startswith("[APPLY]"):
            a = LINK.search(r)
            job["apply_url"] = a.group(2) if a else ""
        elif r.startswith("[") and LINK.sub("", r).strip() == "":  # a line made only of tag links
            tags += [t for t, _ in LINK.findall(r)]
        else:
            desc.append(r)
    job["skills_tags"] = "; ".join(tags)
    job["description"] = re.sub(r"\s*Premium$", "", " ".join(desc))
    return job


def parse_page(path: Path, page: int, today: str) -> list:
    lines = path.read_text().splitlines()
    starts = [i for i, l in enumerate(lines) if TITLE.match(l)]
    jobs = []
    for k, s in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        block = lines[s:end]
        for j, l in enumerate(block):  # stop at the next logo / section heading
            if j > 0 and (LOGO.match(l.strip()) or l.startswith("### ") or l.startswith("## ")):
                block = block[:j]
                break
        job = parse_card(block, page, today)
        jobs.append(job)
    return jobs


def main(first: int, last: int) -> None:
    today = date.today().isoformat()
    seen, jobs = set(), []
    for n in range(first, last + 1):
        p = ROOT / ".tmp" / "pages" / f"listing-{n}.md"
        if not p.exists():
            print(f"MISSING page {n}")
            continue
        page_jobs = parse_page(p, n, today)
        new = [j for j in page_jobs if j["job_url"] not in seen]
        seen.update(j["job_url"] for j in new)
        jobs += new
        print(f"page {n}: {len(page_jobs)} parsed, {len(new)} new")
    out = ROOT / ".tmp"
    (out / "jobs.json").write_text(json.dumps(jobs, indent=2, ensure_ascii=False))
    with open(out / "jobs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(jobs)
    print(f"{len(jobs)} jobs -> {out/'jobs.csv'}")
    for f_ in FIELDS:
        print(f"  {f_:12} blank in {sum(1 for j in jobs if not j[f_])}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]) if a else 1, int(a[1]) if len(a) > 1 else 5)
