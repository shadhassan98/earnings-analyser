import yfinance as yf
import json

ticker = "NVDA"
stock = yf.Ticker(ticker)
news = stock.news[:5]
print(f"News count: {len(news)}")
for n in news:
    print(f"Title: {n.get('title')}")
    print(f"Content: {json.dumps(n, indent=2)}")
