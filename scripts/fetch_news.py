import json
import os
from datetime import datetime, timezone, timedelta

import requests
import feedparser

# --------- 翻译函数 ---------


def translate_to_zh(text: str) -> str:
    """使用 MyMemory 免费 API，把英文翻译为中文"""
    try:
        url = (
            "https://api.mymemory.translated.net/get"
            f"?q={requests.utils.quote(text)}&langpair=en|zh-CN"
        )
        r = requests.get(url, timeout=10).json()
        translated = r.get("responseData", {}).get("translatedText", "")
        return translated or text
    except Exception:
        # 翻译失败就用原文兜底
        return text


# --------- 各站点抓取函数 ---------

API_HN = "https://hn.algolia.com/api/v1/search?tags=front_page"


def fetch_hn(limit=15):
    """Hacker News 首页"""
    resp = requests.get(API_HN, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for hit in data.get("hits", [])[:limit]:
        title_en = hit.get("title") or hit.get("story_title") or "No title"
        title_zh = translate_to_zh(title_en)
        url = hit.get("url") or hit.get("story_url") or ""
        points = hit.get("points") or 0
        comments = hit.get("num_comments") or 0
        items.append(
            {
                "source": "Hacker News",
                "title": title_en,      # 英文原文
                "title_zh": title_zh,   # 中文翻译
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
        title_en = entry.get("title", "No title")
        title_zh = translate_to_zh(title_en)
        link = entry.get("link", "")
        items.append(
            {
                "source": source_name,
                "title": title_en,
                "title_zh": title_zh,
                "url": link,
                "points": None,
                "comments": None,
            }
        )
    return items


def build_summary(items, max_items: int = 5) -> str:
    """
    用前几条中文标题拼一段大白话总结：
    “用大白话说，今天的热点大概是这些：1）…；2）…；…。”
    """
    zh_titles = []
    for it in items:
        t = it.get("title_zh") or it.get("title")
        if not t:
            continue
        zh_titles.append(t)
        if len(zh_titles) >= max_items:
            break

    if not zh_titles:
        return ""

    parts = []
    for idx, t in enumerate(zh_titles, 1):
        t_short = t
        if len(t_short) > 40:
            t_short = t_short[:38] + "..."
        parts.append(f"{idx}）{t_short}")

    return "用大白话说，今天的热点大概是这些： " + "； ".join(parts) + "。"


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

    # 北京时间（UTC+8）
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)

    summary = build_summary(all_items)

    out = {
        "last_updated": beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "items": all_items,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
