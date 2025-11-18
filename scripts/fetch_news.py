import json
import os
from datetime import datetime, timezone

import requests
import feedparser

# --------- 各站点抓取函数 ---------

API_HN = "https://hn.algolia.com/api/v1/search?tags=front_page"


def fetch_hn(limit=15):
    """Hacker News 首页"""
    resp = requests.get(API_HN, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for hit in data.get("hits", [])[:limit]:
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


def fetch_rss(url: str, source_name: str, limit: int = 10):
    """通用 RSS 抓取"""
    d = feedparser.parse(url)
    items = []
    for entry in d.entries[:limit]:
        title = entry.get("title", "No title")
        link = entry.get("link", "")
        items.append(
            {
                "source": source_name,
                "title": title,
                "url": link,
                "points": None,
                "comments": None,
            }
        )
    return items


def main():
    all_items = []

    # 1. Hacker News
    all_items += fetch_hn(limit=15)

    # 2. Reddit
    all_items += fetch_rss("https://www.reddit.com/r/all/.rss", "Reddit r/all", limit=10)
    all_items += fetch_rss(
        "https://www.reddit.com/r/worldnews/.rss", "Reddit r/worldnews", limit=10
    )

    # 3. TechCrunch
    all_items += fetch_rss("https://techcrunch.com/feed/", "TechCrunch", limit=10)

    # 4. The Verge
    all_items += fetch_rss(
        "https://www.theverge.com/rss/index.xml", "The Verge", limit=10
    )

    # 5. Product Hunt
    all_items += fetch_rss("https://www.producthunt.com/feed", "Product Hunt", limit=10)

    # 6. BBC World News
    all_items += fetch_rss(
        "http://feeds.bbci.co.uk/news/world/rss.xml", "BBC World", limit=10
    )

    # 未来如果你想新增别的，只要再加几行 fetch_rss(...) 即可

    out = {
        "last_updated": datetime.now(timezone.utc)
        .astimezone()
        .strftime("%Y-%m-%d %H:%M:%S"),
        "items": all_items,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
