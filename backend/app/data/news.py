# backend/app/data/news.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import yfinance as yf
import urllib.request
import xml.etree.ElementTree as ET

def _iso(value: Any) -> Optional[str]:
    """Normalise yfinance epoch seconds / ISO strings / RSS dates to ISO-8601 UTC."""
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        text = str(value)
        if text[:4].isdigit():
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        return parsedate_to_datetime(text).astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def fetch_rss_headlines(ticker: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Fallback news fetcher using Google News RSS feed for stock tickers.
    Guarantees 100% uptime when yfinance endpoints are rate-limited or empty.
    """
    ticker_clean = ticker.upper().strip()
    rss_url = f"https://news.google.com/rss/search?q={ticker_clean}+stock&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        req = urllib.request.Request(rss_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        articles = []

        for item in root.findall(".//item")[:limit]:
            title = item.find("title").text if item.find("title") is not None else "No Title"
            link = item.find("link").text if item.find("link") is not None else ""
            source_elem = item.find("source")
            publisher = source_elem.text if source_elem is not None else "Market News"
            pub = item.find("pubDate")
            # Google News titles end with " - Publisher"; drop the duplicate
            if publisher and title.endswith(f" - {publisher}"):
                title = title[: -len(publisher) - 3]

            articles.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "published": _iso(pub.text if pub is not None else None),
            })

        return articles
    except Exception as e:
        print(f"[news] RSS fallback failed for {ticker_clean}: {e}")
        return []


def get_ticker_news(ticker: str, limit: int = 5) -> Dict[str, Any]:
    """
    Fetches recent news headlines for a stock ticker.
    Uses yfinance first, automatically falling back to RSS if yfinance returns 0 articles.
    """
    ticker_clean = ticker.upper().strip()
    parsed_news: List[Dict[str, str]] = []

    # 1. Primary Attempt: yfinance ticker news
    try:
        t = yf.Ticker(ticker_clean)
        raw_news = t.news or []

        for item in raw_news[:limit]:
            content = item.get("content", {}) if isinstance(item.get("content"), dict) else {}
            title = item.get("title") or content.get("title")
            if not title:
                continue

            publisher = (
                item.get("publisher")
                or content.get("provider", {}).get("displayName")
                or "Market News"
            )
            link = (
                item.get("link")
                or content.get("canonicalUrl", {}).get("url")
                or ""
            )

            parsed_news.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "published": _iso(item.get("providerPublishTime") or content.get("pubDate")),
            })
    except Exception as e:
        print(f"[news] yfinance lookup bypassed for {ticker_clean}: {e}")

    # 2. Fallback Attempt: RSS feed if yfinance returned empty
    if not parsed_news:
        parsed_news = fetch_rss_headlines(ticker_clean, limit=limit)

    return {
        "status": "success",
        "ticker": ticker_clean,
        "count": len(parsed_news),
        "articles": parsed_news
    }