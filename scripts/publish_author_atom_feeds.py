#!/usr/bin/env python3
"""Publish a compact snapshot of Narou author Atom feeds.

Input: data/author-list.json, containing authors with author_id and author_type.
Output: data/atom/author-feeds.json. No app database or reading positions are accessed.
"""
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, os, re, sys, time
import xml.etree.ElementTree as ET

INPUT_PATH = os.environ.get("AUTHOR_LIST_PATH", "data/author-list.json")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "data/atom/author-feeds.json")
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ID_RE = re.compile(r"^(?:[0-9]+|X[0-9A-Z]+)$", re.I)

def fetch_feed(author_id, kind, url):
    req = Request(url, headers={
        "User-Agent": "tomotayomu-author-feed-collector/1.0",
        "Accept": "application/atom+xml, application/xml, text/xml",
    })
    try:
        with urlopen(req, timeout=25) as res:
            status, body = res.status, res.read()
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
        return {"kind": kind, "ok": True, "http_status": status,
                "entry_count": len(entries), "entries": entries, "error": None}
    except HTTPError as e:
        return {"kind": kind, "ok": False, "http_status": e.code,
                "entry_count": None, "entries": [], "error": f"HTTP {e.code}"}
    except (URLError, TimeoutError, ET.ParseError, OSError) as e:
        return {"kind": kind, "ok": False, "http_status": None,
                "entry_count": None, "entries": [],
                "error": f"{type(e).__name__}: {e}"}

def main():
    try:
        with open(INPUT_PATH, encoding="utf-8") as f:
            source = json.load(f)
        raw_authors = source["authors"]
    except Exception as e:
        print(f"Cannot read author list: {e}", file=sys.stderr)
        return 2
    authors, seen = [], set()
    for item in raw_authors:
        aid = str(item.get("author_id", "")).strip()
        typ = item.get("author_type")
        if not ID_RE.fullmatch(aid) or typ not in ("normal", "r18"):
            print(f"Skipping invalid author record: {aid!r}/{typ!r}", file=sys.stderr)
            continue
        key = (typ, aid.upper() if aid[:1].upper() == "X" else aid)
        if key in seen: continue
        seen.add(key)
        base = "https://api.syosetu.com"
        feeds = [
            fetch_feed(aid, "novel", f"{base}/writernovel/{aid}.Atom"),
            fetch_feed(aid, "activity", f"{base}/writerblog/{aid}.Atom"),
        ]
        authors.append({"author_id": aid, "author_type": typ,
                        "ok": all(x["ok"] for x in feeds), "feeds": feeds})
        print(f"{aid} ({typ}): " + ", ".join(
            f"{x['kind']}={x['http_status']}/{x['entry_count']}" for x in feeds))
        time.sleep(0.25)
    result = {"schema_version": 1, "purpose": "tomotayomu-author-atom-feeds",
              "fetched_at": datetime.now(timezone.utc).isoformat(),
              "source_author_count": len(raw_authors), "author_count": len(authors),
              "failed_feed_count": sum(not f["ok"] for a in authors for f in a["feeds"]),
              "authors": authors}
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(authors)} authors")
    return 0

if __name__ == "__main__":
    sys.exit(main())
