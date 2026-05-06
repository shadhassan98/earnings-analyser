from fastapi import FastAPI

# Verify isolated imports
import mcp
import yfinance as yf
import langchain
import faiss
from google import genai

app = FastAPI(title="Context-Aware Earnings Analyzer - MCP Server")

@app.get("/")
def read_root():
    return {"status": "Backend MCP server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
