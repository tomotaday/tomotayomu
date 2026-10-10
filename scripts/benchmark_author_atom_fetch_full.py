#!/usr/bin/env python3
"""Full-size diagnostic for bounded-concurrent Narou Atom fetches.

Reads the author list and writes only a report. It does not modify production snapshots,
GitHub Pages files, index.html, or any IndexedDB data.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import time
import xml.etree.ElementTree as ET

INPUT_PATH = os.environ.get("AUTHOR_LIST_PATH", "data/author-list.json")
REPORT_PATH = os.environ.get("REPORT_PATH", "author-fetch-full-benchmark.json")
MAX_WORKERS = max(1, min(4, int(os.environ.get("MAX_WORKERS", "4"))))
ATOM_NS = "{http://www.w3.org/2005/Atom}"

def fetch_one(author, kind):
    aid = str(author["author_id"])
    endpoint = "writernovel" if kind == "novel" else "writerblog"
    url = f"https://api.syosetu.com/{endpoint}/{aid}.Atom"
    req = Request(url, headers={
        "User-Agent": "tomotayomu-author-feed-full-benchmark/1.0",
        "Accept": "application/atom+xml, application/xml, text/xml",
    })
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=25) as res:
            status, body = res.status, res.read()
        root = ET.fromstring(body)
        entries = root.findall(f"{ATOM_NS}entry")
        ids = []
        for entry in entries:
            node = entry.find(f"{ATOM_NS}id")
            ids.append((node.text or "").strip() if node is not None else "")
        return {
            "author_id": aid, "author_type": author["author_type"], "kind": kind,
            "ok": True, "http_status": status, "entry_count": len(entries),
            "entry_ids": ids, "elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": None,
        }
    except (HTTPError, URLError, TimeoutError, ET.ParseError, OSError) as exc:
        return {
            "author_id": aid, "author_type": author["author_type"], "kind": kind,
            "ok": False, "http_status": getattr(exc, "code", None), "entry_count": None,
            "entry_ids": [], "elapsed_seconds": round(time.perf_counter() - started, 3),
            "error": f"{type(exc).__name__}: {exc}",
        }

def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        raw = json.load(f)["authors"]
    authors, seen = [], set()
    for item in raw:
        aid = str(item.get("author_id", "")).strip()
        typ = item.get("author_type")
        if not aid or typ not in ("normal", "r18"):
            continue
        key = (typ, aid)
        if key not in seen:
            seen.add(key)
            authors.append({"author_id": aid, "author_type": typ})
    tasks = [(author, kind) for author in authors for kind in ("novel", "activity")]
    started = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(fetch_one, author, kind): (author, kind) for author, kind in tasks}
        for future in as_completed(future_map):
            results.append(future.result())
    elapsed = round(time.perf_counter() - started, 3)
    results.sort(key=lambda x: (x["author_type"], x["author_id"], x["kind"]))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "author_count": len(authors),
        "feed_request_count": len(tasks),
        "max_workers": MAX_WORKERS,
        "elapsed_seconds": elapsed,
        "ok_count": sum(x["ok"] for x in results),
        "failed_count": sum(not x["ok"] for x in results),
        "entry_count_total": sum(x["entry_count"] or 0 for x in results),
        "warning": "Full-size diagnostic only. Does not write production snapshots. Feed contents may change between runs.",
        "results": results,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(json.dumps({k: report[k] for k in (
        "author_count", "feed_request_count", "max_workers", "elapsed_seconds",
        "ok_count", "failed_count", "entry_count_total", "generated_at", "report_path"
    ) if k in report}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
