#!/usr/bin/env python3
"""Fetch public note RSS and maintain a deduplicated article archive."""
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / "note-articles.json"
RSS = "https://note.com/ready_mimosa9257/rss"
existing = []
if DEST.exists():
    try:
        existing = json.loads(DEST.read_text(encoding="utf-8")).get("articles", [])
    except (ValueError, TypeError):
        pass
req = urllib.request.Request(RSS, headers={"User-Agent": "AI-Lab-Shop-RSS-Sync/1.0 (+https://github.com/liangchenggongqi-jpg/ai-lab-shop)"})
with urllib.request.urlopen(req, timeout=25) as response:
    xml = response.read(2_000_000)
root = ET.fromstring(xml)
incoming = []
for item in root.findall("./channel/item"):
    title = (item.findtext("title") or "").strip()
    url = (item.findtext("link") or "").strip()
    date = (item.findtext("pubDate") or "").strip()
    if title and url.startswith("https://note.com/ready_mimosa9257/n/"):
        incoming.append({"title": title, "url": url, "published": date})
if not incoming:
    raise RuntimeError("RSS had no matching articles; archive not overwritten")
by_url = {a["url"]: a for a in existing if isinstance(a, dict) and a.get("url")}
for article in incoming:
    by_url[article["url"]] = article
archive = {"source": RSS, "updated_at": datetime.now(timezone.utc).isoformat(), "articles": list(by_url.values())}
DEST.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Stored {len(archive['articles'])} distinct articles ({len(incoming)} from RSS)")
