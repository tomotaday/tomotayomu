#!/usr/bin/env python3
"""Benchmark sequential vs bounded-concurrent Narou Atom fetches on a small sample.

This is a diagnostic only: it never writes production snapshots and never touches index.html or IndexedDB.
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
REPORT_PATH = os.environ.get("REPORT_PATH", "author-fetch-benchmark.json")
SAMPLE_SIZE = max(1, min(50, int(os.environ.get("SAMPLE_SIZE", "12"))))
MAX_WORKERS = max(1, min(4, int(os.environ.get("MAX_WORKERS", "3"))))
ATOM_NS = "{http://www.w3.org/2005/Atom}"

def fetch_one(author, kind):
    aid = str(author["author_id"])
    path = "writernovel" if kind == "novel" else "writerblog"
    url = f"https://api.syosetu.com/{path}/{aid}.Atom"
    req = Request(url, headers={
        "User-Agent": "tomotayomu-author-feed-benchmark/1.0",
        "Accept": "application/atom+xml, application/xml, text/xml",
    })
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=20) as res:
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
    sample, seen = [], set()
    for author in raw:
        aid = str(author.get("author_id", "")).strip()
        typ = author.get("author_type")
        key = (typ, aid)
        if aid and typ in ("normal", "r18") and key not in seen:
            sample.append({"author_id": aid, "author_type": typ})
            seen.add(key)
            if len(sample) >= SAMPLE_SIZE:
                break
    tasks = [(a, kind) for a in sample for kind in ("novel", "activity")]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_author_count": len(sample),
        "feed_request_count_per_mode": len(tasks),
        "max_workers": MAX_WORKERS,
        "warning": "Small diagnostic sample only; Atom feeds may change between requests. No production files are modified.",
    }

    start = time.perf_counter()
    sequential = []
    for author, kind in tasks:
        sequential.append(fetch_one(author, kind))
        time.sleep(0.25)
    report["sequential"] = {
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "ok_count": sum(x["ok"] for x in sequential),
        "failed_count": sum(not x["ok"] for x in sequential),
        "results": sequential,
    }

    start = time.perf_counter()
    concurrent = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(fetch_one, author, kind) for author, kind in tasks]
        for future in as_completed(futures):
            concurrent.append(future.result())
    report["bounded_concurrent"] = {
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "ok_count": sum(x["ok"] for x in concurrent),
        "failed_count": sum(not x["ok"] for x in concurrent),
        "results": sorted(concurrent, key=lambda x: (x["author_type"], x["author_id"], x["kind"])),
    }
    seq_map = {(x["author_type"], x["author_id"], x["kind"]): x for x in sequential}
    con_map = {(x["author_type"], x["author_id"], x["kind"]): x for x in concurrent}
    comparable = []
    for key in sorted(set(seq_map) & set(con_map)):
        a, b = seq_map[key], con_map[key]
        comparable.append({
            "author_type": key[0], "author_id": key[1], "kind": key[2],
            "both_ok": a["ok"] and b["ok"],
            "entry_count_equal": a["entry_count"] == b["entry_count"],
            "entry_ids_equal": a["entry_ids"] == b["entry_ids"] if a["ok"] and b["ok"] else None,
        })
    report["comparison"] = {
        "same_feed_count": len(comparable),
        "entry_counts_equal_count": sum(x["entry_count_equal"] for x in comparable),
        "entry_ids_equal_count": sum(x["entry_ids_equal"] is True for x in comparable),
        "results": comparable,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({
        "sample_author_count": report["sample_author_count"],
        "feed_request_count_per_mode": report["feed_request_count_per_mode"],
        "sequential_seconds": report["sequential"]["elapsed_seconds"],
        "concurrent_seconds": report["bounded_concurrent"]["elapsed_seconds"],
        "sequential_failures": report["sequential"]["failed_count"],
        "concurrent_failures": report["bounded_concurrent"]["failed_count"],
        "entry_ids_equal_count": report["comparison"]["entry_ids_equal_count"],
        "comparison_count": report["comparison"]["same_feed_count"],
        "report": REPORT_PATH,
    }, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
