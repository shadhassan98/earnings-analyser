# Context-Aware Earnings Analyzer

This project is a microservice-based application that allows users to perform deep-dive financial analysis on stocks using a chat interface powered by **DeepSeek v4-flash**. It leverages the **Model Context Protocol (MCP)** to provide the LLM with live financial data, sentiment analysis, and historical trends through custom backend tools.

## Key Features

-   **Deep Financial Insights**: Access real-time price data, valuation metrics (P/E), and comprehensive financial statements.
-   **Market Sentiment**: Automated sentiment analysis of the latest news headlines using VADER.
-   **Interactive Visuals**: Rich rendering of price trend charts and color-coded sentiment cards.
-   **Company Context**: Integrated business summaries and sector mapping.
-   **Two-Phase Analysis**: A robust execution flow that first gathers all necessary data via tool calls and then generates a structured final report.

## Architecture

The project is divided into two distinct components:

1.  **`mcp_server` (Backend Tool Provider)**
    *   **Role**: Exposes financial tools (yfinance, sentiment) via the Model Context Protocol.
    *   **Tech Stack**: FastAPI, FastMCP, `yfinance`, NLTK.
    *   **Communication**: Server-Sent Events (SSE).

2.  **`client` (Frontend Orchestrator)**
    *   **Role**: Manages the user interface and orchestrates the interaction between the user, DeepSeek LLM, and the MCP server.
    *   **Tech Stack**: Streamlit, OpenAI SDK (for DeepSeek), MCP Client SDK.

## Prerequisites

*   Python 3.10+
*   A **DeepSeek API Key**

## How to Run the Application

### 1. Start the MCP Server

Navigate to the `mcp_server` directory:

```bash
cd mcp_server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
*Server starts on `http://localhost:8000`.*

### 2. Start the Streamlit Client

Open a **new** terminal window and navigate to the `client` directory:

```bash
cd client
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set your DeepSeek API Key:
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

Run the Streamlit application:
```bash
streamlit run app.py
```

## How it works

1.  **Discovery**: On startup, the Streamlit client connects to the MCP server and discovers available tools (e.g., `fetch_stock_data`, `fetch_news_sentiment`).
2.  **User Query**: The user asks a question like "Is NVDA a good buy right now?"
3.  **Data Gathering (Phase 1)**: DeepSeek identifies the tools needed and triggers multiple calls to the MCP server to fetch historical prices, financials, and news sentiment.
4.  **Rich Rendering**: As data arrives, the UI dynamically renders charts and sentiment cards.
5.  **Final Analysis (Phase 2)**: DeepSeek processes all retrieved data and provides a structured, data-driven investment summary.

---
*Developed with the Model Context Protocol.*
