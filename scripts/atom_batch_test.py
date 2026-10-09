#!/usr/bin/env python3
"""Fetch Narou Atom feeds for multiple author IDs and combine them into JSON.

This is an isolated pipeline test. It does not touch the app or its IndexedDB.
"""
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import sys
import xml.etree.ElementTree as ET

AUTHOR_IDS = list(dict.fromkeys(
    value.strip() for value in os.environ.get("AUTHOR_IDS", "1826746").split(",")
    if value.strip()
))
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "atom-test-result/authors.json")
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def fetch_feed(author_id: str, kind: str, url: str) -> dict:
    request = Request(url, headers={
        "User-Agent": "tomotayomu-github-actions-atom-batch-test/1.0",
        "Accept": "application/atom+xml, application/xml, text/xml",
    })
    try:
        with urlopen(request, timeout=25) as response:
            status, body = response.status, response.read()
        root = ET.fromstring(body)
        entries = []
        for entry in root.findall(f"{ATOM_NS}entry"):
            def child_text(name: str) -> str:
                node = entry.find(f"{ATOM_NS}{name}")
                return (node.text or "").strip() if node is not None else ""
            links = entry.findall(f"{ATOM_NS}link")
            alternate = next(
                (node.attrib.get("href", "") for node in links
                 if node.attrib.get("rel", "alternate") == "alternate"),
                links[0].attrib.get("href", "") if links else "",
            )
            entries.append({
                "title": child_text("title"),
                "id": child_text("id"),
                "updated": child_text("updated"),
                "published": child_text("published"),
                "url": alternate,
            })
        return {"author_id": author_id, "kind": kind, "url": url,
                "ok": True, "http_status": status,
                "entry_count": len(entries), "entries": entries, "error": None}
    except HTTPError as exc:
        return {"author_id": author_id, "kind": kind, "url": url,
                "ok": False, "http_status": exc.code, "entry_count": None,
                "entries": [], "error": f"HTTP {exc.code}"}
    except (URLError, TimeoutError, ET.ParseError, OSError) as exc:
        return {"author_id": author_id, "kind": kind, "url": url,
                "ok": False, "http_status": None, "entry_count": None,
                "entries": [], "error": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:
        return {"author_id": author_id, "kind": kind, "url": url,
                "ok": False, "http_status": None, "entry_count": None,
                "entries": [], "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    if not AUTHOR_IDS:
        print("ERROR: AUTHOR_IDS is empty", file=sys.stderr)
        return 2
    authors = []
    for author_id in AUTHOR_IDS:
        if not author_id.isdigit():
            print(f"ERROR: invalid author ID: {author_id}", file=sys.stderr)
            return 2
        feeds = [
            fetch_feed(author_id, "novel",
                       f"https://api.syosetu.com/writernovel/{author_id}.Atom"),
            fetch_feed(author_id, "activity",
                       f"https://api.syosetu.com/writerblog/{author_id}.Atom"),
        ]
        authors.append({
            "author_id": author_id,
            "ok": all(feed["ok"] for feed in feeds),
            "feeds": feeds,
        })
    result = {
        "schema_version": 1,
        "purpose": "isolated-github-actions-multi-author-atom-test",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "author_count": len(authors),
        "authors": authors,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    for author in authors:
        for feed in author["feeds"]:
            print(f'author={author["author_id"]} {feed["kind"]}: '
                  f'ok={feed["ok"]}, HTTP={feed["http_status"]}, '
                  f'entries={feed["entry_count"]}, error={feed["error"]}')
    print(f"JSON written: {OUTPUT_PATH}")
    return 0 if all(author["ok"] for author in authors) else 1


if __name__ == "__main__":
    sys.exit(main())
