from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import json

from tools.financial import get_stock_data

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

# Expose an SSE endpoint (/sse) and a message endpoint (/messages).
app.mount("/", server.sse_app())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
