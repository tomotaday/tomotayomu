#!/usr/bin/env python3
"""Read-only persistence simulation for Atom conditional GET across two runs.

Run A fetches and parses a small mixed sample, then writes a temporary state file.
Run B loads that state and sends validators. 304 reuses cached parsed entries;
200 parses the fresh body and replaces the cache. Nothing is committed.
"""
import json, os, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = "https://api.syosetu.com"
NS = "{http://www.w3.org/2005/Atom}"
COUNT = int(os.environ.get("MAX_AUTHORS", "25"))
WORKERS = 3
TIMEOUT = 20
STATE_PATH = Path("conditional-get-state-test.json")
REPORT_PATH = Path("conditional-get-persistence-report.json")

def request(url, validators=None):
    headers = {"User-Agent": "tomotayomu-conditional-persistence-test/1.0",
               "Accept": "application/atom+xml, application/xml, */*"}
    validators = validators or {}
    if validators.get("etag"): headers["If-None-Match"] = validators["etag"]
    if validators.get("last_modified"): headers["If-Modified-Since"] = validators["last_modified"]
    started = time.perf_counter()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            body, status, response_headers = res.read(), res.status, res.headers
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            body, status, response_headers = b"", 304, exc.headers
        else:
            return {"status": exc.code, "seconds": round(time.perf_counter()-started, 3),
                    "body_bytes": 0, "etag": None, "last_modified": None,
                    "entries": None, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"status": None, "seconds": round(time.perf_counter()-started, 3),
                "body_bytes": 0, "etag": None, "last_modified": None,
                "entries": None, "error": f"{type(exc).__name__}: {exc}"}
    entries = None
    if status == 200:
        try:
            root = ET.fromstring(body)
            entries = []
            for entry in root.findall(f"{NS}entry"):
                def value(name):
                    node = entry.find(f"{NS}{name}")
                    return (node.text or "").strip() if node is not None else ""
                links = entry.findall(f"{NS}link")
                link = next((n.attrib.get("href", "") for n in links
                             if n.attrib.get("rel", "alternate") == "alternate"),
                            links[0].attrib.get("href", "") if links else "")
                entries.append({"id": value("id"), "title": value("title"),
                                "updated": value("updated"), "published": value("published"),
                                "url": link})
        except Exception as exc:
            return {"status": status, "seconds": round(time.perf_counter()-started, 3),
                    "body_bytes": len(body), "etag": response_headers.get("ETag"),
                    "last_modified": response_headers.get("Last-Modified"),
                    "entries": None, "error": f"XML parse: {exc}"}
    return {"status": status, "seconds": round(time.perf_counter()-started, 3),
            "body_bytes": len(body), "etag": response_headers.get("ETag"),
            "last_modified": response_headers.get("Last-Modified"),
            "entries": entries, "error": None}

def key_for(author, kind):
    return f"{author['author_type']}:{author['author_id']}:{kind}"

def url_for(author, kind):
    endpoint = "writernovel" if kind == "novel" else "writerblog"
    return f"{BASE}/{endpoint}/{author['author_id']}.Atom"

def run_fetch(tasks, state=None):
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        future_map = {}
        for author, kind in tasks:
            key = key_for(author, kind)
            previous = (state or {}).get("feeds", {}).get(key, {})
            validators = {"etag": previous.get("etag"),
                          "last_modified": previous.get("last_modified")}
            future_map[pool.submit(request, url_for(author, kind), validators)] = (key, previous)
        for future in as_completed(future_map):
            key, previous = future_map[future]
            response = future.result()
            if response["status"] == 304:
                if not previous.get("entries"):
                    response.update({"reused_cache": False, "error": "304 but cached entries missing"})
                else:
                    response.update({"entries": previous["entries"], "reused_cache": True})
                    response["entry_count"] = len(previous["entries"])
            elif response["status"] == 200 and response["error"] is None:
                response.update({"reused_cache": False, "entry_count": len(response["entries"])})
            else:
                # Preserve the last known parsed entries and validators on errors.
                response.update({"reused_cache": bool(previous.get("entries")),
                                 "entries": previous.get("entries"),
                                 "entry_count": len(previous.get("entries", [])) if previous.get("entries") is not None else None})
            results[key] = response
    return results

def main():
    source = json.loads(Path("data/author-list.json").read_text(encoding="utf-8"))
    all_authors = source.get("authors", [])
    normal = [a for a in all_authors if a.get("author_type") == "normal"]
    r18 = [a for a in all_authors if a.get("author_type") == "r18"]
    authors = normal[:(COUNT + 1)//2] + r18[:COUNT//2]
    if len(authors) < COUNT:
        used = {(a.get("author_type"), a.get("author_id")) for a in authors}
        authors.extend(a for a in all_authors if (a.get("author_type"), a.get("author_id")) not in used and len(authors) < COUNT)
    tasks = [(a, kind) for a in authors for kind in ("novel", "activity")]

    start = time.perf_counter()
    first = run_fetch(tasks)
    first_seconds = round(time.perf_counter()-start, 3)
    first_state = {"schema_version": 1, "saved_at": datetime.now(timezone.utc).isoformat(), "feeds": {}}
    for key, result in first.items():
        if result["status"] == 200 and result["error"] is None:
            first_state["feeds"][key] = {"etag": result.get("etag"),
                "last_modified": result.get("last_modified"), "entries": result["entries"]}
    STATE_PATH.write_text(json.dumps(first_state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # Reload the exact serialized state, just as a later run would.
    saved_state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    start = time.perf_counter()
    second = run_fetch(tasks, saved_state)
    second_seconds = round(time.perf_counter()-start, 3)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only simulation; state is temporary and not committed",
        "authors_tested": len(authors), "feeds_tested": len(tasks),
        "first_run_seconds": first_seconds, "second_run_seconds": second_seconds,
        "first_run_success_200": sum(1 for x in first.values() if x["status"] == 200 and not x["error"]),
        "second_run_304": sum(1 for x in second.values() if x["status"] == 304),
        "second_run_200": sum(1 for x in second.values() if x["status"] == 200 and not x["error"]),
        "second_run_errors": sum(1 for x in second.values() if x["error"]),
        "second_run_reused_cache": sum(1 for x in second.values() if x.get("reused_cache")),
        "missing_cached_entries": sum(1 for x in second.values() if x.get("error") == "304 but cached entries missing"),
        "second_run_body_bytes": sum(x["body_bytes"] for x in second.values()),
        "second_run_entries": sum(x.get("entry_count") or 0 for x in second.values()),
        "details": [{"key": k, "first_status": first[k]["status"], "first_count": first[k].get("entry_count"),
                     "first_etag": bool(first[k].get("etag")), "second_status": second[k]["status"],
                     "second_count": second[k].get("entry_count"), "reused_cache": second[k].get("reused_cache"),
                     "error": second[k].get("error")} for k in sorted(first)]
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "details"}, ensure_ascii=False, indent=2))
    if report["second_run_errors"] or report["missing_cached_entries"]:
        raise SystemExit("Persistence simulation had errors; inspect artifact.")

if __name__ == "__main__":
    main()
