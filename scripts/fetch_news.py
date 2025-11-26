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


def fetch_hn(limit=15, region="Global"):
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
                "region": region,
                "published": None,
                "summary": "",
            }
        )
    return items


def fetch_rss(url, source_name, region="Global", limit=10):
    """通用 RSS 抓取"""
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        title_en = entry.get("title", "").strip()
        title_zh = translate_to_zh(title_en) if title_en else ""
        link = entry.get("link", "")

        items.append(
            {
                "source": source_name,
                "title": title_en,
                "title_zh": title_zh,
                "url": link,          # 和 Hacker News 保持一致，都用 url 字段
                "region": region,     # 地区标签
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "").strip(),
            }
        )
    return items


def main():
    all_items = []

    # ========= 🌍 Global / 全球 =========
    all_items += fetch_hn(limit=15, region="Global")

    all_items += fetch_rss(
        "https://www.reddit.com/r/all/.rss",
        "Reddit r/all",
        region="Global",
        limit=10,
    )
    all_items += fetch_rss(
        "https://www.reddit.com/r/worldnews/.rss",
        "Reddit r/worldnews",
        region="Global",
        limit=10,
    )

    all_items += fetch_rss(
        "https://techcrunch.com/feed/",
        "TechCrunch",
        region="Global",
        limit=10,
    )
    all_items += fetch_rss(
        "https://www.theverge.com/rss/index.xml",
        "The Verge",
        region="Global",
        limit=10,
    )
    all_items += fetch_rss(
        "https://www.producthunt.com/feed",
        "Product Hunt",
        region="Global",
        limit=10,
    )
    all_items += fetch_rss(
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "BBC World",
        region="Global",
        limit=10,
    )
    # 你也可以在这里继续加 NYTimes World 等其它 Global 源

    # ========= 🇧🇷 Brazil / 巴西 =========
    all_items += fetch_rss(
        "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
        "Folha de S.Paulo",
        region="Brazil",
        limit=10,
    )
    all_items += fetch_rss(
        "https://riotimesonline.com/feed/",
        "The Rio Times",
        region="Brazil",
        limit=10,
    )

    # ========= 🇮🇩 Indonesia / 印尼 =========
    all_items += fetch_rss(
        "https://rss.thejakartapost.com/home",
        "The Jakarta Post",
        region="Indonesia",
        limit=10,
    )
    all_items += fetch_rss(
        "https://www.kontan.co.id/feed",
        "Kontan",
        region="Indonesia",
        limit=10,
    )

    # ========= 🇮🇳 India / 印度 =========
    all_items += fetch_rss(
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "Times of India - Top Stories",
        region="India",
        limit=10,
    )
    all_items += fetch_rss(
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "NDTV - Top Stories",
        region="India",
        limit=10,
    )

    # ========= 🇯🇵 Japan / 日本 =========
    all_items += fetch_rss(
        "https://feedx.net/rss/nhk.xml",
        "NHK WORLD-JAPAN",
        region="Japan",
        limit=10,
    )

    # ========= 🇰🇷 South Korea / 韩国 =========
    all_items += fetch_rss(
        "https://www.koreaherald.com/rss",
        "The Korea Herald",
        region="South Korea",
        limit=10,
    )

    # ========= 🇸🇦 Saudi Arabia / 沙特 =========
    all_items += fetch_rss(
        "https://www.arabnews.com/rss",
        "Arab News",
        region="Saudi Arabia",
        limit=10,
    )
    all_items += fetch_rss(
        "https://saudigazette.com.sa/rssFeed/74",
        "Saudi Gazette",
        region="Saudi Arabia",
        limit=10,
    )

    # 北京时间（UTC+8）
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=8)

    out = {
        "last_updated": beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
        "items": all_items,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
