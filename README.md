# Context-Aware Earnings Analyzer

This project is a microservice-based application that allows users to ask questions about stocks and earnings reports using a chat interface powered by Google's Gemini LLM. It leverages the Model Context Protocol (MCP) to provide the LLM with live financial data through custom tools.

## Architecture

The project is divided into two distinct components:

1.  **`mcp_server` (Backend Model Context Protocol Server)**
    *   **Role**: Exposes tools that can be consumed by AI models. Currently, it provides a tool to fetch real-time stock data.
    *   **Tech Stack**: FastAPI, FastMCP, `yfinance`, Uvicorn.
    *   **Key Files**:
        *   `main.py`: Sets up the FastAPI application and the FastMCP server, defining a `/sse` endpoint for Server-Sent Events communication and exposing the `fetch_stock_data` tool.
        *   `tools/financial.py`: Contains the core logic using the `yfinance` library to retrieve stock information (current price, 52-week high, trailing P/E, forward P/E).

2.  **`client` (Frontend Streamlit Application)**
    *   **Role**: Provides the user interface (a chat application) and orchestrates the interaction between the user, the Gemini LLM, and the MCP server.
    *   **Tech Stack**: Streamlit, Google GenAI SDK (`google-genai`), MCP Python Client SDK.
    *   **Key Files**:
        *   `app.py`: Sets up the Streamlit chat interface. It establishes a connection to the backend MCP server via SSE, discovers available tools (like `fetch_stock_data`), maps them to Gemini's tool schema, and handles the chat loop. When the Gemini model decides to call a tool, the client executes the request against the MCP server and returns the results to the model to formulate a final response.

## Prerequisites

*   Python 3.10+
*   A Google Gemini API Key

## How to Run the Application

Since this is a dual-microservice architecture, you need to run the server and the client in separate terminal windows.

### 1. Start the MCP Server

Open a terminal and navigate to the `mcp_server` directory:

```bash
cd mcp_server
```

Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
python main.py
```
*The server will start and listen on `http://localhost:8000` (the SSE endpoint is at `/sse`).*

### 2. Start the Streamlit Client

Open a **new** terminal window and navigate to the `client` directory:

```bash
cd client
```

Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Set your Gemini API Key as an environment variable (optional, the UI will prompt you if it's not set):

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Run the Streamlit application:

```bash
streamlit run app.py
```

*Your default web browser should open automatically to `http://localhost:8501`, showing the Earnings Analyzer Chat interface.*

## How it works

1.  The user types a query like "What is the current price and P/E ratio for AAPL?" into the Streamlit chat.
2.  The Streamlit app sends this query to the Gemini model, along with the descriptions of the tools available on the MCP server (discovered during startup).
3.  Gemini recognizes that it needs live data to answer the query and responds with a "tool call" for `fetch_stock_data(ticker="AAPL")`.
4.  The Streamlit app intercepts this tool call, executes it against the local MCP server via the SSE connection.
5.  The MCP server runs the `yfinance` logic, gets the data, and returns it to the Streamlit app.
6.  The Streamlit app feeds the retrieved JSON data back into Gemini.
7.  Gemini generates a natural language response based on the live data, which is then displayed to the user.
