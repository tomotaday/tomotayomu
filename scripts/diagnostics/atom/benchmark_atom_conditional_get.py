#!/usr/bin/env python3
"""Read-only 50-author benchmark for conditional Atom GETs."""
import concurrent.futures
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.syosetu.com"
WORKERS = 3
PER_TYPE = 25
TIMEOUT = 20
HEADER_NAMES = ("ETag", "Last-Modified", "Date", "Content-Length")


def request_feed(target, conditional_headers=None):
    headers = {
        "User-Agent": "tomotayomu-conditional-benchmark/1.0",
        "Accept": "application/atom+xml, application/xml, */*",
    }
    headers.update(conditional_headers or {})
    started = time.perf_counter()
    try:
        req = urllib.request.Request(target["url"], headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read()
            return {
                "status": response.status,
                "seconds": round(time.perf_counter() - started, 3),
                "bytes": len(body),
                "headers": {name: response.headers[name] for name in HEADER_NAMES if response.headers.get(name)},
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "status": exc.code,
            "seconds": round(time.perf_counter() - started, 3),
            "bytes": len(body),
            "headers": {name: exc.headers[name] for name in HEADER_NAMES if exc.headers.get(name)},
            "error": None if exc.code == 304 else f"HTTP {exc.code}",
        }
    except Exception as exc:
        return {
            "status": None,
            "seconds": round(time.perf_counter() - started, 3),
            "bytes": 0,
            "headers": {},
            "error": f"{type(exc).__name__}: {exc}",
        }


def parallel_requests(targets, headers_by_key=None):
    def run(target):
        extra = (headers_by_key or {}).get(target["key"], {})
        return target["key"], request_feed(target, extra)
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run, target) for target in targets]
        for future in concurrent.futures.as_completed(futures):
            key, result = future.result()
            results[key] = result
    return results


def main():
    source = json.loads(Path("data/author-list.json").read_text(encoding="utf-8"))
    authors = source["authors"]
    selected = []
    for kind in ("normal", "r18"):
        matches = [author for author in authors if author.get("author_type") == kind][:PER_TYPE]
        selected.extend(matches)

    targets = []
    for author in selected:
        author_id = str(author["author_id"])
        kind = author["author_type"]
        for feed_kind, endpoint in (("novel", "writernovel"), ("activity", "writerblog")):
            key = f"{kind}:{author_id}:{feed_kind}"
            targets.append({
                "key": key,
                "author_type": kind,
                "author_id": author_id,
                "feed_kind": feed_kind,
                "url": f"{BASE}/{endpoint}/{author_id}.Atom",
            })

    started = time.perf_counter()
    first_started = time.perf_counter()
    first = parallel_requests(targets)
    first_seconds = round(time.perf_counter() - first_started, 3)

    conditional_headers = {}
    for target in targets:
        result = first[target["key"]]
        headers = result["headers"]
        validators = {}
        if headers.get("ETag"):
            validators["If-None-Match"] = headers["ETag"]
        elif headers.get("Last-Modified"):
            validators["If-Modified-Since"] = headers["Last-Modified"]
        if validators and result["status"] == 200:
            conditional_headers[target["key"]] = validators

    second_started = time.perf_counter()
    second = parallel_requests(targets, conditional_headers)
    second_seconds = round(time.perf_counter() - second_started, 3)

    details = []
    for target in targets:
        key = target["key"]
        a, b = first[key], second[key]
        details.append({
            "author_type": target["author_type"],
            "author_id": target["author_id"],
            "feed_kind": target["feed_kind"],
            "initial_status": a["status"],
            "initial_seconds": a["seconds"],
            "initial_bytes": a["bytes"],
            "etag": a["headers"].get("ETag"),
            "last_modified": a["headers"].get("Last-Modified"),
            "conditional_headers_sent": list(conditional_headers.get(key, {}).keys()),
            "conditional_status": b["status"] if key in conditional_headers else None,
            "conditional_seconds": b["seconds"] if key in conditional_headers else None,
            "conditional_bytes": b["bytes"] if key in conditional_headers else None,
            "initial_error": a["error"],
            "conditional_error": b["error"] if key in conditional_headers else None,
        })

    eligible = len(conditional_headers)
    not_modified = sum(1 for item in details if item["conditional_status"] == 304)
    conditional_200 = sum(1 for item in details if item["conditional_status"] == 200)
    failed_initial = sum(1 for item in details if item["initial_status"] != 200)
    failed_conditional = sum(1 for item in details if item["conditional_error"])
    initial_bytes = sum(item["initial_bytes"] for item in details)
    conditional_bytes = sum(item["conditional_bytes"] or 0 for item in details)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Read-only benchmark: initial GET vs immediate conditional GET",
        "authors_selected": len(selected),
        "feeds_tested": len(targets),
        "workers": WORKERS,
        "initial_phase_seconds": first_seconds,
        "conditional_phase_seconds": second_seconds,
        "total_seconds": round(time.perf_counter() - started, 3),
        "initial_successful_feeds": sum(1 for item in details if item["initial_status"] == 200),
        "initial_failed_feeds": failed_initial,
        "conditional_eligible_feeds": eligible,
        "conditional_304": not_modified,
        "conditional_200": conditional_200,
        "conditional_failed": failed_conditional,
        "feeds_without_validator": len(targets) - eligible,
        "initial_body_bytes": initial_bytes,
        "conditional_body_bytes": conditional_bytes,
        "body_bytes_saved_in_this_test": max(0, initial_bytes - conditional_bytes),
        "details": details,
        "caveat": "Immediate repeat requests are a controlled benchmark, not proof of real-world update rates. This test does not modify production snapshots.",
    }
    Path("atom-conditional-benchmark-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, ensure_ascii=False, indent=2))
    print("DETAILS: atom-conditional-benchmark-report.json")


if __name__ == "__main__":
    main()
