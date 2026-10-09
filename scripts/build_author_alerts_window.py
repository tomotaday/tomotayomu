#!/usr/bin/env python3
"""Build a compact 90-day snapshot for the independent author-alert preview.

The source snapshot is the successful GitHub Actions output at data/atom/author-feeds.json.
This script never reads or writes the app's IndexedDB and does not touch index.html.
"""
from datetime import datetime, timezone, timedelta
import json, os, sys

SOURCE = os.environ.get("SOURCE_PATH", "data/atom/author-feeds.json")
OUTPUT = os.environ.get("OUTPUT_PATH", "data/atom/author-alerts-window.json")
WINDOW_DAYS = 90

def parse_date(entry):
    for key in ("updated", "published"):
        value = entry.get(key)
        if value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except (ValueError, TypeError):
                pass
    return None

def main():
    with open(SOURCE, encoding="utf-8") as f:
        source = json.load(f)
    fetched_at = datetime.fromisoformat(source["fetched_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
    cutoff = fetched_at - timedelta(days=WINDOW_DAYS)
    authors = []
    for author in source.get("authors", []):
        feeds = []
        for feed in author.get("feeds", []):
            selected = []
            for entry in feed.get("entries") or []:
                dt = parse_date(entry)
                if dt is None or dt < cutoff or dt > fetched_at + timedelta(days=1):
                    continue
                selected.append({
                    "title": entry.get("title", ""),
                    "date": (entry.get("updated") or entry.get("published") or ""),
                    "url": entry.get("url", ""),
                    "id": entry.get("id", ""),
                })
            selected.sort(key=lambda e: e["date"], reverse=True)
            feeds.append({"kind": feed.get("kind", ""), "entries": selected})
        if any(feed["entries"] for feed in feeds):
            authors.append({
                "author_id": author.get("author_id", ""),
                "author_type": author.get("author_type", ""),
                "feeds": feeds,
            })
    result = {
        "schema_version": 1,
        "purpose": "tomotayomu-author-alert-window-preview",
        "fetched_at": fetched_at.isoformat(),
        "window_days": WINDOW_DAYS,
        "source_author_count": source.get("author_count", len(source.get("authors", []))),
        "source_failed_feed_count": source.get("failed_feed_count", 0),
        "authors_with_recent_entries": len(authors),
        "authors": authors,
        "notes": "Only entries present in the source Atom snapshot are included; this is not a guarantee of complete coverage beyond the source feed limits."
    }
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {OUTPUT}: {len(authors)} authors, {os.path.getsize(OUTPUT)} bytes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
