import json
import os
from datetime import datetime, timezone
import requests

API_URL = "https://hn.algolia.com/api/v1/search?tags=front_page"

def fetch_hn():
    resp = requests.get(API_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for hit in data.get("hits", []):
        title = hit.get("title") or hit.get("story_title") or "No title"
        url = hit.get("url") or hit.get("story_url") or ""
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        items.append(
            {
                "source": "Hacker News",
                "title": title,
                "url": url,
                "points": points,
                "comments": comments,
            }
        )
    return items

def main():
    items = fetch_hn()
    out = {
        "last_updated": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
