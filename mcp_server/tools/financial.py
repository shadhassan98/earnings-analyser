import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from typing import Dict, Any, List
import pandas as pd

# Initialize VADER (Lightweight sentiment)
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except (LookupError, Exception):
    nltk.download('vader_lexicon', quiet=True)

sia = SentimentIntensityAnalyzer()

def get_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetches stock data using yfinance.
    Returns a dictionary with current price, 52-week high, trailing P/E, and forward P/E.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            return {"error": f"No information found for ticker '{ticker}'."}
            
        # Check if basic price information is present to validate the ticker
        if "currentPrice" not in info and "regularMarketPrice" not in info and "previousClose" not in info:
             return {"error": f"Invalid ticker or no data available for '{ticker}'."}

        data = {
            "ticker": ticker.upper(),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE")
        }
        return data
        
    except Exception as e:
        return {"error": f"Failed to fetch data for '{ticker}': {str(e)}"}

def get_historical_prices(ticker: str, period: str = "1mo") -> str:
    """Fetches historical price data for a given period."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return f"No historical data found for {ticker} over period {period}."
        
        # Convert index to string to avoid serialization issues with milliseconds in some JSON parsers
        hist.index = hist.index.strftime('%Y-%m-%d %H:%M:%S')
        return hist.to_json()
    except Exception as e:
        return f"Error fetching historical prices: {str(e)}"

def get_company_info(ticker: str) -> Dict[str, Any]:
    """Fetches company profile and basic information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return {"error": f"No info found for {ticker}."}
        # Selectively return some info to keep it lean
        keys = ['longName', 'sector', 'industry', 'longBusinessSummary', 'website']
        return {k: info.get(k) for k in keys if k in info}
    except Exception as e:
        return {"error": f"Error fetching company info: {str(e)}"}

def get_earnings_calendar(ticker: str) -> str:
    """Fetches upcoming earnings dates."""
    try:
        import json
        from datetime import date, datetime

        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            raise TypeError ("Type %s not serializable" % type(obj))

        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        if calendar is None:
             return "No upcoming earnings found."
             
        # calendar is now a dict in newer yfinance versions
        if isinstance(calendar, dict):
            return json.dumps(calendar, default=json_serial)
        
        return calendar.to_json()
    except Exception as e:
        return f"Error fetching earnings calendar: {str(e)}"

def get_financial_statements(ticker: str, statement_type: str = "income") -> str:
    """Fetches Income Statement or Balance Sheet."""
    try:
        stock = yf.Ticker(ticker)
        if statement_type.lower() == "income":
            data = stock.income_stmt
        elif statement_type.lower() == "balance":
            data = stock.balance_sheet
        else:
            return "Invalid statement type. Use 'income' or 'balance'."
        
        if data is None or data.empty:
            return f"No {statement_type} data found for {ticker}."
            
        return data.iloc[:, :2].to_json() # Return only last 2 years to save tokens
    except Exception as e:
        return f"Error fetching financial statements: {str(e)}"

def get_news_sentiment(ticker: str) -> List[Dict[str, Any]]:
    """Fetches news and calculates basic sentiment score."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news[:5] # Last 5 headlines
        results = []
        for article in news:
            # Handle new yfinance format where title is inside 'content'
            title = article.get('content', {}).get('title', article.get('title', ''))
            if not title:
                continue
                
            score = sia.polarity_scores(title)['compound']
            sentiment = "Positive" if score > 0.05 else "Negative" if score < -0.05 else "Neutral"
            results.append({"headline": title, "sentiment": sentiment, "score": score})
        return results
    except Exception as e:
        return [{"error": f"Error fetching news sentiment: {str(e)}"}]
