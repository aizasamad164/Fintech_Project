# backend/test_news.py
from app.data.news import get_ticker_news

if __name__ == "__main__":
    test_ticker = "APPL"
    print(f"Fetching live news for {test_ticker}...")
    news_data = get_ticker_news(test_ticker, limit=3)
    
    print(f"\nStatus: {news_data['status']}")
    print(f"Articles Found: {news_data['count']}\n")
    
    for idx, article in enumerate(news_data.get("articles", []), 1):
        print(f"[{idx}] {article['title']}")
        print(f"    Publisher: {article['publisher']}")
        print(f"    URL:       {article['link']}\n")