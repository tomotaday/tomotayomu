#!/usr/bin/env python3
"""Non-writing benchmark: fetch selected authors' feeds, then measure local ID diff."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, os, re, time, xml.etree.ElementTree as ET

AUTHOR_PATH = "data/author-list.json"
SNAPSHOT_PATH = "data/atom/author-feeds.json"
REPORT_PATH = "benchmark-report.json"
NS = "{http://www.w3.org/2005/Atom}"
ID_RE = re.compile(r"^(?:[0-9]+|X[0-9A-Z]+)$", re.I)

def fetch(author, kind, endpoint):
    url = f"https://api.syosetu.com/{endpoint}/{author['author_id']}.Atom"
    req = Request(url, headers={"User-Agent": "tomotayomu-author-feed-benchmark/1.0",
                                "Accept": "application/atom+xml, application/xml, text/xml"})
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=25) as res:
            status, body = res.status, res.read()
        root = ET.fromstring(body)
        entries = []
        for e in root.findall(f"{NS}entry"):
            n = e.find(f"{NS}id")
            entries.append((n.text or "").strip() if n is not None else "")
        return {"author_id": author["author_id"], "author_type": author["author_type"],
                "kind": kind, "ok": True, "status": status, "count": len(entries),
                "ids": [x for x in entries if x], "seconds": round(time.perf_counter()-start, 3),
                "error": None}
    except (HTTPError, URLError, TimeoutError, OSError, ET.ParseError) as e:
        return {"author_id": author["author_id"], "author_type": author["author_type"],
                "kind": kind, "ok": False, "status": getattr(e, "code", None), "count": 0,
                "ids": [], "seconds": round(time.perf_counter()-start, 3),
                "error": f"{type(e).__name__}: {e}"}

def main():
    max_authors = int(os.environ.get("MAX_AUTHORS", "50"))
    with open(AUTHOR_PATH, encoding="utf-8") as f:
        source = json.load(f)
    authors, seen = [], set()
    for item in source.get("authors", []):
        aid, typ = str(item.get("author_id", "")).strip(), item.get("author_type")
        if not ID_RE.fullmatch(aid) or typ not in ("normal", "r18"):
            continue
        key = (typ, aid.upper() if aid[:1].upper() == "X" else aid)
        if key not in seen:
            seen.add(key)
            authors.append({"author_id": aid, "author_type": typ})
        if len(authors) >= max_authors:
            break

    old = {}
    try:
        with open(SNAPSHOT_PATH, encoding="utf-8") as f:
            snap = json.load(f)
        for a in snap.get("authors", []):
            for feed in a.get("feeds", []):
                old[(a.get("author_type"), str(a.get("author_id")), feed.get("kind"))] = {
                    str(e.get("id", "")) for e in feed.get("entries", []) if e.get("id")
                }
    except (OSError, ValueError):
        pass

    jobs = []
    start_all = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        for a in authors:
            for kind, endpoint in (("novel", "writernovel"), ("activity", "writerblog")):
                futures[pool.submit(fetch, a, kind, endpoint)] = (a, kind)
        for future in as_completed(futures):
            jobs.append(future.result())
    fetch_seconds = time.perf_counter() - start_all

    diff_start = time.perf_counter()
    new_ids = 0
    compared = 0
    for result in jobs:
        key = (result["author_type"], result["author_id"], result["kind"])
        old_ids = old.get(key, set())
        compared += len(result["ids"])
        new_ids += sum(1 for item_id in result["ids"] if item_id not in old_ids)
    diff_seconds = time.perf_counter() - diff_start

    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only benchmark; no files committed or changed",
        "authors_requested": max_authors,
        "authors_tested": len(authors),
        "feeds_requested": len(jobs),
        "successful_feeds": sum(x["ok"] for x in jobs),
        "failed_feeds": sum(not x["ok"] for x in jobs),
        "entries_returned": sum(x["count"] for x in jobs),
        "entry_ids_compared": compared,
        "new_ids_vs_saved_snapshot": new_ids,
        "fetch_and_parse_seconds": round(fetch_seconds, 3),
        "local_diff_seconds": round(diff_seconds, 6),
        "total_seconds": round(fetch_seconds + diff_seconds, 3),
        "max_feed_seconds": max((x["seconds"] for x in jobs), default=0),
        "slowest_feeds": sorted(
            [{"author_id": x["author_id"], "author_type": x["author_type"],
              "kind": x["kind"], "seconds": x["seconds"], "ok": x["ok"],
              "error": x["error"]} for x in jobs],
            key=lambda x: x["seconds"], reverse=True)[:20],
        "note": "Diff is measured after the same feed requests. This benchmark measures local comparison cost; it does not claim that comparison reduces network requests."
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for k, v in report.items():
        if k != "slowest_feeds":
            print(f"{k}: {v}")
    print("Slowest feeds:")
    for item in report["slowest_feeds"]:
        print(item)

if __name__ == "__main__":
    main()
