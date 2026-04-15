import re

import requests
from datetime import datetime, timezone


# DuckDuckGo News search via their lite API (no API key needed)
DDG_BASE = "https://duckduckgo.com"
DDG_NEWS = "https://duckduckgo.com/news.js"

def _get_vqd(query: str) -> str:
    """Extract vqd token from DuckDuckGo HTML"""
    resp = requests.get(
        DDG_BASE,
        params={"q": query},
        headers={
            "User-Agent": "Mozilla/5.0",
        },
        timeout=10,
    )

    match = re.search(r'vqd="(.*?)"', resp.text)
    if not match:
        raise RuntimeError("Failed to extract vqd")

    return match.group(1)

def search_news(query: str, max_results: int = 10) -> list[dict]:
    """
    Search DuckDuckGo for news articles related to a query.
    Returns a list of dicts with: title, body, url, date, source
    """
    vqd = _get_vqd(query)

    params = {
        "q": query,
        "vqd": vqd,
        "l": "wt-wt",   # region
        "p": "1",       # safe search off
        "o":"json",
        "noamp":"1"
    }

    resp = requests.get(
        DDG_NEWS,
        params=params,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        timeout=10,
    )

    data = resp.json()
    results = []

    for item in data.get("results", [])[:max_results]:
        timestamp = item.get("date")
        news_date = datetime.fromtimestamp(timestamp, tz=timezone.utc) \
                    .replace(tzinfo=None) \
                    .isoformat()
        results.append({
            "title": item.get("title"),
            "body": item.get("excerpt"),
            "url": item.get("url"),
            "date": news_date, 
            "source": item.get("source", "DuckDuckGo"),
        })
        if len(results) >= max_results:
            break

    # Fallback: use DuckDuckGo HTML search via news endpoint
    if not results:
        results = _ddg_news_fallback(query, max_results)

    print(f"[search] Found {len(results)} results for: '{query}'")
    return results[:max_results]


def _ddg_news_fallback(query: str, max_results: int = 10) -> list[dict]:
    """
    Fallback: scrape DuckDuckGo news lite page.
    Returns structured news items.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (stock-news-agent/1.0)"}
        res = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": f"{query} news", "df": "w"},  # last week
            headers=headers,
            timeout=10,
        )

        from html.parser import HTMLParser

        results = []

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self._in_result = False
                self._current = {}
                self._capture = None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                cls = attrs.get("class", "")

                if "result__title" in cls:
                    self._in_result = True
                    self._current = {}

                if self._in_result and tag == "a" and "result__a" in cls:
                    self._current["url"] = attrs.get("href", "")
                    self._capture = "title"

                if self._in_result and "result__snippet" in cls:
                    self._capture = "body"

            def handle_data(self, data):
                if self._capture and data.strip():
                    self._current[self._capture] = (
                        self._current.get(self._capture, "") + data
                    )

            def handle_endtag(self, tag):
                if self._capture in ("title", "body") and tag in ("a", "div"):
                    self._capture = None

                if self._in_result and tag == "div":
                    if self._current.get("title"):
                        results.append({
                            "title": self._current.get("title", "").strip(),
                            "body": self._current.get("body", "").strip(),
                            "url": self._current.get("url", ""),
                            "date": datetime.utcnow().isoformat(),
                            "source": "DuckDuckGo",
                        })
                        self._in_result = False
                        self._current = {}

        parser = DDGParser()
        parser.feed(res.text)
        return results[:max_results]

    except Exception as e:
        print(f"[search] Fallback search failed: {e}")
        return []


def format_results_as_text(results: list[dict]) -> str:
    """Convert search results list into a single text blob for RAG ingestion."""
    lines = []
    for r in results:
        lines.append(f"Title: {r['title']}")
        if r.get("body"):
            lines.append(f"Content: {r['body']}")
        if r.get("url"):
            lines.append(f"URL: {r['url']}")
        if r.get("date"):
            lines.append(f"Date: {r['date']}")
        lines.append("")  # blank line between articles
    return "\n".join(lines)

if __name__ == "__main__":
    search_news(query="NVIDIA latest news 2026")
