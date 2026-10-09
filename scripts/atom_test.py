#!/usr/bin/env python3
"""Isolated GitHub Actions test: fetch one author's Narou Atom feeds and write JSON.

This script does not read or modify the app's IndexedDB or bookshelf.
It distinguishes a successful empty feed from a failed request.
"""
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import sys
import xml.etree.ElementTree as ET

AUTHOR_ID = os.environ.get("AUTHOR_ID", "1826746")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "atom-test-result/author-1826746.json")
FEEDS = {
    "novel": f"https://api.syosetu.com/writernovel/{AUTHOR_ID}.Atom",
    "activity": f"https://api.syosetu.com/writerblog/{AUTHOR_ID}.Atom",
}
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def fetch_feed(kind: str, url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "tomotayomu-github-actions-atom-test/1.0",
            "Accept": "application/atom+xml, application/xml, text/xml",
        },
    )
    try:
        with urlopen(request, timeout=25) as response:
            status = response.status
            body = response.read()
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
        return {
            "kind": kind,
            "url": url,
            "ok": True,
            "http_status": status,
            "entry_count": len(entries),
            "entries": entries,
            "error": None,
        }
    except HTTPError as exc:
        return {"kind": kind, "url": url, "ok": False,
                "http_status": exc.code, "entry_count": None,
                "entries": [], "error": f"HTTP {exc.code}"}
    except (URLError, TimeoutError, ET.ParseError, OSError) as exc:
        return {"kind": kind, "url": url, "ok": False,
                "http_status": None, "entry_count": None,
                "entries": [], "error": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:
        return {"kind": kind, "url": url, "ok": False,
                "http_status": None, "entry_count": None,
                "entries": [], "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    result = {
        "schema_version": 1,
        "purpose": "isolated-github-actions-atom-test",
        "author_id": AUTHOR_ID,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "feeds": [fetch_feed(kind, url) for kind, url in FEEDS.items()],
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    for feed in result["feeds"]:
        print(f'{feed["kind"]}: ok={feed["ok"]}, '
              f'HTTP={feed["http_status"]}, entries={feed["entry_count"]}, '
              f'error={feed["error"]}')
    print(f"JSON written: {OUTPUT_PATH}")

    # A feed failure must be visible as a failed workflow, not mistaken for 0 updates.
    return 0 if all(feed["ok"] for feed in result["feeds"]) else 1


if __name__ == "__main__":
    sys.exit(main())
