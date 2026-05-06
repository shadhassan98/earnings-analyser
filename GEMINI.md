# Project Instructions: Earnings Analyzer

## AI Model
The application now primarily uses **DeepSeek (v4-flash)** via an OpenAI-compatible interface for orchestration and reasoning.

## Financial Tools
You have access to a local MCP server with the following tools:

- `fetch_stock_data(ticker)`: Basic price and P/E info.
- `fetch_historical_prices(ticker, period)`: Analyze trends (1mo, 6mo, 1y). Returns JSON for charting.
- `fetch_company_info(ticker)`: Business model context, sector, and industry.
- `fetch_earnings_calendar(ticker)`: Check for upcoming earnings dates or catalysts.
- `fetch_financial_statements(ticker, statement_type)`: Deep dive into 'income' or 'balance'. Returns last 2 years.
- `fetch_news_sentiment(ticker)`: Gauge market sentiment based on the last 5 headlines using VADER.

## Guidelines
- When asked about a stock's 'health,' combine news sentiment with financial statements for a holistic answer.
- Truncate financial statements to the last 2 years (handled by the tool) and summaries to 500 characters to manage context limits if necessary.
- Use `yfinance` for all data fetching.
- Sentiment analysis uses NLTK's VADER, which is memory-efficient.
- The UI handles rich rendering (charts, cards) automatically when these tools are called.
