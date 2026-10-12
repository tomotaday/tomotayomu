#!/usr/bin/env python3
"""Publish Narou author Atom snapshots, using conditional GET when validators exist.

Input: data/author-list.json.
Output: data/atom/author-feeds.json.
Previous successful entries and HTTP validators are retained across workflow runs.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, os, re, sys
import xml.etree.ElementTree as ET

INPUT_PATH = os.environ.get("AUTHOR_LIST_PATH", "data/author-list.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "data/atom/author-feeds.json")
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ID_RE = re.compile(r"^(?:[0-9]+|X[0-9A-Z]+)$", re.I)
BASE = "https://api.syosetu.com"


def parse_entries(body):
    root = ET.fromstring(body)
    entries = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        def val(name):
            node = entry.find(f"{ATOM_NS}{name}")
            return (node.text or "").strip() if node is not None else ""
        links = entry.findall(f"{ATOM_NS}link")
        link = next((n.attrib.get("href", "") for n in links
                     if n.attrib.get("rel", "alternate") == "alternate"),
                    links[0].attrib.get("href", "") if links else "")
        entries.append({"title": val("title"), "id": val("id"),
                        "updated": val("updated"), "published": val("published"),
                        "url": link})
    return entries


def fetch_feed(author_id, kind, url, old_feed=None):
    old_feed = old_feed or {}
    old_entries = old_feed.get("entries")
    has_cache = isinstance(old_entries, list)
    headers = {
        "User-Agent": "tomotayomu-author-feed-collector/1.1",
        "Accept": "application/atom+xml, application/xml, text/xml",
    }
    if has_cache and old_feed.get("etag"):
        headers["If-None-Match"] = old_feed["etag"]
    if has_cache and old_feed.get("last_modified"):
        headers["If-Modified-Since"] = old_feed["last_modified"]

    def send(request_headers):
        req = Request(url, headers=request_headers)
        try:
            with urlopen(req, timeout=25) as res:
                return res.status, res.read(), res.headers
        except HTTPError as exc:
            if exc.code == 304:
                return 304, b"", exc.headers
            raise

    try:
        try:
            status, body, response_headers = send(headers)
        except HTTPError as exc:
            return {"kind": kind, "ok": False, "http_status": exc.code,
                    "entry_count": None, "entries": [], "error": f"HTTP {exc.code}",
                    "etag": old_feed.get("etag"), "last_modified": old_feed.get("last_modified")}

        if status == 304:
            if has_cache:
                return {"kind": kind, "ok": True, "http_status": 304,
                        "entry_count": len(old_entries), "entries": old_entries,
                        "etag": response_headers.get("ETag") or old_feed.get("etag"),
                        "last_modified": response_headers.get("Last-Modified") or old_feed.get("last_modified"),
                        "error": None, "not_modified": True}
            # A 304 without a local body is unusable: retry once without validators.
            status, body, response_headers = send({
                "User-Agent": "tomotayomu-author-feed-collector/1.1",
                "Accept": "application/atom+xml, application/xml, text/xml",
            })

        entries = parse_entries(body)
        return {"kind": kind, "ok": True, "http_status": status,
                "entry_count": len(entries), "entries": entries,
                "etag": response_headers.get("ETag"),
                "last_modified": response_headers.get("Last-Modified"),
                "error": None, "not_modified": False}
    except HTTPError as exc:
        return {"kind": kind, "ok": False, "http_status": exc.code,
                "entry_count": None, "entries": [], "error": f"HTTP {exc.code}",
                "etag": old_feed.get("etag"), "last_modified": old_feed.get("last_modified")}
    except (URLError, TimeoutError, ET.ParseError, OSError) as exc:
        return {"kind": kind, "ok": False, "http_status": None,
                "entry_count": None, "entries": [],
                "error": f"{type(exc).__name__}: {exc}",
                "etag": old_feed.get("etag"), "last_modified": old_feed.get("last_modified")}


def main():
    try:
        with open(INPUT_PATH, encoding="utf-8") as f:
            source = json.load(f)
        raw_authors = source["authors"]
    except Exception as exc:
        print(f"Cannot read author list: {exc}", file=sys.stderr)
        return 2

    previous = {}
    if os.path.isfile(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                old_snapshot = json.load(f)
            for old_author in old_snapshot.get("authors", []):
                old_key = (old_author.get("author_type"), str(old_author.get("author_id", "")))
                previous[old_key] = {feed.get("kind"): feed for feed in old_author.get("feeds", [])}
        except Exception as exc:
            print(f"Previous snapshot could not be read; starting fresh: {exc}", file=sys.stderr)

    valid_authors, seen = [], set()
    for item in raw_authors:
        aid = str(item.get("author_id", "")).strip()
        typ = item.get("author_type")
        if not ID_RE.fullmatch(aid) or typ not in ("normal", "r18"):
            print(f"Skipping invalid author record: {aid!r}/{typ!r}", file=sys.stderr)
            continue
        key = (typ, aid.upper() if aid[:1].upper() == "X" else aid)
        if key in seen:
            continue
        seen.add(key)
        valid_authors.append({"author_id": aid, "author_type": typ})

    feed_results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_map = {}
        for author in valid_authors:
            aid, typ = author["author_id"], author["author_type"]
            old_feeds = previous.get((typ, aid), {})
            for kind, endpoint in (("novel", "writernovel"), ("activity", "writerblog")):
                old_feed = old_feeds.get(kind)
                future = pool.submit(fetch_feed, aid, kind, f"{BASE}/{endpoint}/{aid}.Atom", old_feed)
                future_map[future] = (typ, aid, kind)
        for future in as_completed(future_map):
            typ, aid, kind = future_map[future]
            feed_results[(typ, aid, kind)] = future.result()

    authors = []
    for author in valid_authors:
        aid, typ = author["author_id"], author["author_type"]
        old_feeds = previous.get((typ, aid), {})
        feeds = [feed_results[(typ, aid, kind)] for kind in ("novel", "activity")]
        for feed in feeds:
            old = old_feeds.get(feed["kind"], {})
            if not feed["ok"] and old:
                feed["entries"] = old.get("entries", [])
                feed["entry_count"] = len(feed["entries"])
                feed["etag"] = old.get("etag")
                feed["last_modified"] = old.get("last_modified")
                feed["previous_data_retained"] = True
            else:
                feed["previous_data_retained"] = False
        authors.append({"author_id": aid, "author_type": typ,
                        "ok": all(x["ok"] for x in feeds), "feeds": feeds})
        print(f"{aid} ({typ}): " + ", ".join(
            f"{x['kind']}={x['http_status']}/{x['entry_count']}"
            f"{'/304-cache' if x.get('not_modified') else ''}" for x in feeds))

    result = {"schema_version": 1, "purpose": "tomotayomu-author-atom-feeds",
              "fetched_at": datetime.now(timezone.utc).isoformat(),
              "source_author_count": len(raw_authors), "author_count": len(authors),
              "failed_feed_count": sum(not f["ok"] for a in authors for f in a["feeds"]),
              "not_modified_feed_count": sum(bool(f.get("not_modified")) for a in authors for f in a["feeds"]),
              "previous_data_retained_count": sum(bool(f.get("previous_data_retained")) for a in authors for f in a["feeds"]),
              "authors": authors}
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")

    total_entries = sum(feed.get("entry_count") or 0 for author in authors for feed in author["feeds"])
    print("SUMMARY " + f"authors={len(authors)} feeds={len(authors)*2} "
          f"not_modified={result['not_modified_feed_count']} "
          f"failed_feeds={result['failed_feed_count']} "
          f"previous_data_retained={result['previous_data_retained_count']} entries={total_entries}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
