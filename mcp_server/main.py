from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import json

from tools.financial import (
    get_stock_data,
    get_historical_prices,
    get_company_info,
    get_earnings_calendar,
    get_financial_statements,
    get_news_sentiment
)

# Initialize a FastAPI app
app = FastAPI(title="Context-Aware Earnings Analyzer - MCP Server")

# Initialize an MCP Server instance
server = FastMCP("mcp-server", host="0.0.0.0")

@server.tool()
def fetch_stock_data(ticker: str) -> str:
    """
    Fetches stock data using yfinance.
    Returns a structured dictionary formatted as a string containing current price,
    52-week high, trailing P/E, and forward P/E.
    """
    data = get_stock_data(ticker)
    return json.dumps(data)

@server.tool()
def fetch_historical_prices(ticker: str, period: str = "1mo") -> str:
    """Fetches historical price data for a given period."""
    return get_historical_prices(ticker, period)

@server.tool()
def fetch_company_info(ticker: str) -> str:
    """Fetches company profile and basic information."""
    data = get_company_info(ticker)
    return json.dumps(data)

@server.tool()
def fetch_earnings_calendar(ticker: str) -> str:
    """Fetches upcoming earnings dates."""
    return get_earnings_calendar(ticker)

@server.tool()
def fetch_financial_statements(ticker: str, statement_type: str = "income") -> str:
    """
    Fetches Income Statement or Balance Sheet. 
    Essential for evaluating a company's revenue growth, profitability (Net Income), 
    and debt before making a Buy/Sell recommendation.
    """
    return get_financial_statements(ticker, statement_type)

@server.tool()
def fetch_news_sentiment(ticker: str) -> str:
    """Fetches news and calculates basic sentiment score."""
    data = get_news_sentiment(ticker)
    return json.dumps(data)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Expose an SSE endpoint (/sse) and a message endpoint (/messages).
app.mount("/", server.sse_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
