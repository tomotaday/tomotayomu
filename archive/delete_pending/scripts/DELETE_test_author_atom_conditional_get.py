#!/usr/bin/env python3
"""Read-only benchmark: compare normal Atom GETs with conditional GETs on a small sample."""
import json, os, re, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = "https://api.syosetu.com"
NS = "{http://www.w3.org/2005/Atom}"
COUNT = int(os.environ.get("MAX_AUTHORS", "25"))
WORKERS = 3
TIMEOUT = 20

def fetch(author, kind, endpoint, validators=None):
    url = f"{BASE}/{endpoint}/{author['author_id']}.Atom"
    headers = {"User-Agent": "tomotayomu-conditional-get-benchmark/1.0",
               "Accept": "application/atom+xml, application/xml, */*"}
    validators = validators or {}
    if validators.get("etag"): headers["If-None-Match"] = validators["etag"]
    if validators.get("last_modified"): headers["If-Modified-Since"] = validators["last_modified"]
    started = time.perf_counter()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            body = res.read()
            status = res.status
            response_headers = res.headers
    except urllib.error.HTTPError as exc:
        if exc.code != 304:
            return {"key": f"{author['author_type']}:{author['author_id']}:{kind}", "status": exc.code,
                    "seconds": round(time.perf_counter()-started, 3), "bytes": 0, "entries": None,
                    "etag": None, "last_modified": None, "error": f"HTTP {exc.code}"}
        body, status, response_headers = b"", 304, exc.headers
    except Exception as exc:
        return {"key": f"{author['author_type']}:{author['author_id']}:{kind}", "status": None,
                "seconds": round(time.perf_counter()-started, 3), "bytes": 0, "entries": None,
                "etag": None, "last_modified": None, "error": f"{type(exc).__name__}: {exc}"}
    entries = None
    if status == 200:
        try:
            root = ET.fromstring(body)
            entries = []
            for node in root.findall(f"{NS}entry"):
                ident = node.find(f"{NS}id")
                entries.append((ident.text or "").strip() if ident is not None else "")
        except Exception as exc:
            return {"key": f"{author['author_type']}:{author['author_id']}:{kind}", "status": status,
                    "seconds": round(time.perf_counter()-started, 3), "bytes": len(body), "entries": None,
                    "etag": response_headers.get("ETag"), "last_modified": response_headers.get("Last-Modified"),
                    "error": f"XML parse: {exc}"}
    return {"key": f"{author['author_type']}:{author['author_id']}:{kind}", "status": status,
            "seconds": round(time.perf_counter()-started, 3), "bytes": len(body), "entries": entries,
            "etag": response_headers.get("ETag"), "last_modified": response_headers.get("Last-Modified"),
            "error": None}

def run_batch(tasks, validator_map=None):
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {}
        for author, kind, endpoint in tasks:
            key = f"{author['author_type']}:{author['author_id']}:{kind}"
            futures[pool.submit(fetch, author, kind, endpoint, (validator_map or {}).get(key))] = key
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results

def main():
    source = json.loads(Path("data/author-list.json").read_text(encoding="utf-8"))
    all_authors = source.get("authors", [])
    # Stratify the sample so R18 is included even when normal authors come first.
    normal = [a for a in all_authors if a.get("author_type") == "normal"]
    r18 = [a for a in all_authors if a.get("author_type") == "r18"]
    normal_count = (COUNT + 1) // 2
    r18_count = COUNT // 2
    authors = normal[:normal_count] + r18[:r18_count]
    if len(authors) < COUNT:
        used = {(a.get("author_type"), a.get("author_id")) for a in authors}
        authors.extend(a for a in all_authors
                       if (a.get("author_type"), a.get("author_id")) not in used
                       and len(authors) < COUNT)
    tasks = [(a, kind, endpoint) for a in authors
             for kind, endpoint in (("novel", "writernovel"), ("activity", "writerblog"))]
    print(f"Read-only conditional GET benchmark: {len(authors)} authors / {len(tasks)} feeds")
    started = time.perf_counter()
    first = run_batch(tasks)
    first_seconds = round(time.perf_counter()-started, 3)
    validators = {key: {"etag": val.get("etag"), "last_modified": val.get("last_modified")}
                  for key, val in first.items() if val.get("etag") or val.get("last_modified")}
    started = time.perf_counter()
    second = run_batch(tasks, validators)
    second_seconds = round(time.perf_counter()-started, 3)
    both_ok = sum(1 for x in first.values() if x["status"] == 200 and x["error"] is None)
    conditional_304 = sum(1 for x in second.values() if x["status"] == 304)
    conditional_200 = sum(1 for x in second.values() if x["status"] == 200)
    no_validator = sum(1 for x in first.values() if not x.get("etag") and not x.get("last_modified"))
    errors = sum(1 for x in list(first.values()) + list(second.values()) if x["error"])
    entry_mismatches = []
    for key, result in second.items():
        if result["status"] == 200 and first.get(key, {}).get("entries") != result.get("entries"):
            entry_mismatches.append(key)
        if result["status"] == 304 and first.get(key, {}).get("entries") is None:
            entry_mismatches.append(key + " (304 without prior parsed body)")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only; no repository data is changed",
        "authors_tested": len(authors), "feeds_tested": len(tasks),
        "first_pass_seconds": first_seconds, "second_pass_seconds": second_seconds,
        "first_pass_200_success": both_ok, "validators_available": len(validators),
        "no_validator_feeds": no_validator, "second_pass_304": conditional_304,
        "second_pass_200": conditional_200, "errors_across_both_passes": errors,
        "entry_mismatches": entry_mismatches,
        "first_pass_bytes": sum(x["bytes"] for x in first.values()),
        "second_pass_bytes": sum(x["bytes"] for x in second.values()),
        "results": [{"key": key, "first": first[key], "second": second[key]} for key in sorted(first)]
    }
    Path("conditional-get-benchmark-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "results"}, ensure_ascii=False, indent=2))
    if errors or entry_mismatches:
        raise SystemExit("Benchmark found errors or entry mismatches; inspect artifact.")

if __name__ == "__main__":
    main()
