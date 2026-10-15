"""Descarga issues 'Duplicate Report' y extrae de sus comentarios el número del original."""
import json
import re
from pathlib import Path

from ingest.fetch_issues import API, REPO, get

PATTERN = re.compile(r"(?:duplicate of|dupe of|dup of|xref|same as|closing in favor of)\s*#(\d+)", re.I)
OUTPUT = Path("data/raw/duplicates.jsonl")


def fetch_duplicates(limit=300):
    url = f"{API}/repos/{REPO}/issues"
    params = {"state": "closed", "labels": "Duplicate Report", "per_page": 100}
    items = []
    while url and len(items) < limit:
        r = get(url, params)
        items += [i for i in r.json() if "pull_request" not in i]
        url, params = r.links.get("next", {}).get("url"), None
    return items[:limit]


def find_original(number):
    for c in get(f"{API}/repos/{REPO}/issues/{number}/comments").json():
        m = PATTERN.search(c["body"] or "")
        if m and int(m.group(1)) != number:
            return int(m.group(1))
    return None


def main():
    rows = []
    for it in fetch_duplicates():
        original = find_original(it["number"])
        if original:
            rows.append({"number": it["number"], "title": it["title"],
                        "body": it["body"] or "", "original": original})
    with OUTPUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} pares duplicado -> original")


if __name__ == "__main__":
    main()