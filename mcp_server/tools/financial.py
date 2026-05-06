import yfinance as yf
from typing import Dict, Any

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
