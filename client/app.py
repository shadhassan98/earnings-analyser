import streamlit as st
import asyncio
import os
import json
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# Load environment variables
load_dotenv()

# Setup page
st.set_page_config(page_title="Stock Market Analyzer", layout="wide")
st.title("Stock Market Analyzer")

# Initialize DeepSeek API key
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    api_key = st.text_input("Enter DeepSeek API Key", type="password")
    if not api_key:
        st.warning("Please provide a DeepSeek API Key to continue.")
        st.stop()

# Initialize DeepSeek (OpenAI-compatible) client
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": """You are a helpful financial assistant. Use the provided tools to fetch live data. 
            For 'buy/sell/hold' recommendations, you should always check:
            1. Current stock data & valuation (P/E).
            2. Recent financial statements (Fetch both 'income' and 'balance' in the same turn if needed).
            3. Market sentiment from recent news.
            
            Provide a clear, concise summary and a direct answer. Avoid fluff, but ensure your recommendation is data-driven."""
        }
    ]

if "company_info" not in st.session_state:
    st.session_state.company_info = {}

def display_sentiment_card(news_data):
    """
    Expects a list of dicts: [{'headline': '...', 'sentiment': 'Positive', 'score': 0.8}]
    """
    st.markdown("### 📊 Market Sentiment Analysis")
    cols = st.columns(len(news_data) if len(news_data) < 4 else 3)
    
    for i, article in enumerate(news_data):
        with cols[i % len(cols)]:
            sentiment = article.get('sentiment', 'Neutral')
            score = article.get('score', 0.0)
            headline = article.get('headline', 'No Title Available')
            
            # Sentiment color logic
            if sentiment == "Positive":
                st.success(f"**{sentiment}** ({score:+.2f})")
            elif sentiment == "Negative":
                st.error(f"**{sentiment}** ({score:+.2f})")
            else:
                st.info(f"**{sentiment}** ({score:+.2f})")
            
            st.caption(f"{headline[:120]}...")

def display_price_chart(ticker, raw_data):
    """
    Converts raw tool output (JSON string of dates/prices) into a line chart.
    """
    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        if not data or not isinstance(data, dict):
             return
             
        # yfinance to_json() results in {column: {timestamp: value}}
        if "Close" in data:
            df = pd.DataFrame.from_dict(data["Close"], orient='index', columns=['Close'])
            # Check if index is already datetime, if not convert it
            if not isinstance(df.index, pd.DatetimeIndex):
                # Try to convert string index to datetime
                df.index = pd.to_datetime(df.index)
            
            st.markdown(f"#### 📈 {ticker} Price Trend")
            st.line_chart(df, y="Close", color="#29b5e8", use_container_width=True)
        else:
            # Maybe it's a different format?
            pass
    except Exception as e:
        st.error(f"Chart Render Error: {e}")

# Sidebar for Company Info
if st.session_state.company_info:
    info = st.session_state.company_info
    with st.sidebar:
        st.divider()
        st.header(info.get('longName', 'Company Info'))
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        if info.get('website'):
            st.link_button("Visit Website", info['website'])
        with st.expander("Business Summary"):
            st.write(info.get('longBusinessSummary', 'No summary available.'))

# Sidebar for Available Tools (Discovery)
if "openai_tools" in st.session_state and st.session_state.openai_tools:
    with st.sidebar:
        st.divider()
        st.header("🛠️ Available Tools")
        for tool in st.session_state.openai_tools:
            func = tool.get("function", {})
            with st.expander(f"`{func.get('name')}`"):
                st.caption(func.get("description", "No description"))
                st.json(func.get("parameters", {}).get("properties", {}))

# Welcome Message (Only shows if no user messages exist)
user_messages = [m for m in st.session_state.messages if m["role"] == "user"]
if not user_messages:
    st.info("""
    ### Hello! 👋 I'm your financial expert assistant.
    I analyze stocks using live data to provide investment insights.
    
    **What I can do:**
    📊 Stock Data | 📈 Price Trends | 🏢 Company Info | 💰 Financials | 📅 Earnings | 📰 News Sentiment
    
    **Ready to get started?** Just give me a ticker (e.g., **AAPL**, **MSFT**, **NVDA**) and ask:
    * *"Should I buy, hold or sell **AAPL** stocks right now ? Analyze current market data and tell me."*
    * *"Should I buy **NVDA** stocks right now or wait for next earnings call ? Analyze historical data and current sentiment."*
    
    **What stock would you like me to look into?**
    """)

# Display chat messages
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls")
    
    if role == "user":
        with st.chat_message("user"):
            if content:
                st.markdown(content)
            # Handle tool response (role: tool) is handled separately in OpenAI format
    
    elif role == "assistant":
        with st.chat_message("assistant"):
            if content:
                with st.expander("📋 Summary Report", expanded=True):
                    st.markdown(content)
            if tool_calls:
                for tc in tool_calls:
                    # Handle both dict and object (attribute) access
                    if isinstance(tc, dict):
                        t_name = tc.get("function", {}).get("name")
                        t_args = tc.get("function", {}).get("arguments")
                    else:
                        t_name = tc.function.name
                        t_args = tc.function.arguments
                    st.info(f"**Executing Tool:** `{t_name}`\n\n**Args:** `{t_args}`")
                    
    elif role == "tool":
        # Render tool output in the chat history
        with st.chat_message("user"):
            tool_name = msg.get("name", "Unknown Tool")
            raw_result = content
            try:
                parsed_result = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
                if tool_name == "fetch_news_sentiment" and isinstance(parsed_result, list):
                    display_sentiment_card(parsed_result)
                elif tool_name == "fetch_historical_prices":
                    display_price_chart("Selected Stock", raw_result)
                elif tool_name == "fetch_financial_statements":
                    with st.expander("📊 Financial Statements Data", expanded=False):
                        st.dataframe(pd.DataFrame(parsed_result), use_container_width=True)
                else:
                    with st.expander(f"🛠️ Tool Result: {tool_name}"):
                        st.json(parsed_result)
            except Exception as e:
                with st.expander(f"🛠️ Tool Result: {tool_name}"):
                    st.write(raw_result)

def map_mcp_to_openai(mcp_tools):
    openai_tools = []
    for t in mcp_tools.tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema
            }
        })
    return openai_tools

@st.cache_resource(ttl=3600)
def get_cached_tools(mcp_url):
    print("FETCHING TOOLS FROM MCP (Cache Miss)...")
    async def _fetch():
        async with sse_client(mcp_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                await mcp_session.initialize()
                mcp_tools = await mcp_session.list_tools()
                return map_mcp_to_openai(mcp_tools)
                
    import threading
    result = None
    exc = None
    def target():
        nonlocal result, exc
        try:
            result = asyncio.run(_fetch())
        except Exception as e:
            exc = e
            
    t = threading.Thread(target=target)
    t.start()
    t.join()
    if exc:
        raise exc
    return result

async def process_chat(prompt_text, openai_tools):
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
    final_content = None
    
    # Create a stable container for tool visuals (charts, cards, etc.)
    visuals_container = st.container()

    # --- PHASE 1: DATA GATHERING ---
    status_placeholder = st.empty()
    with status_placeholder.status("🔍 Fetching Data...", expanded=True) as status:
        while True:
            # If we just finished tools, we are now "Analyzing" the results to see if we need more
            if st.session_state.messages and st.session_state.messages[-1].get("role") == "tool":
                status.update(label="🧠 Analyzing gathered data...", state="running")
            else:
                status.update(label="🔍 Fetching Data...", state="running")

            try:
                response = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=st.session_state.messages,
                    tools=openai_tools if openai_tools else None,
                    extra_body={"thinking": {"type": "disabled"}}
                )
            except Exception as api_err:
                st.error(f"DeepSeek API Error: {api_err}")
                return

            assistant_message = response.choices[0].message
            st.session_state.messages.append(assistant_message.model_dump())

            if not assistant_message.tool_calls:
                final_content = assistant_message.content
                status.update(label="✅ Data Gathering Complete!", state="complete", expanded=False)
                break

            # Execute tools
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Single-line progress update inside the status block
                status.update(label=f"⚙️ Running `{tool_name}`...", state="running")
                start_time = time.time()

                try:
                    async with sse_client(mcp_url) as (read_stream, write_stream):
                        async with ClientSession(read_stream, write_stream) as mcp_session:
                            await mcp_session.initialize()
                            mcp_result = await mcp_session.call_tool(tool_name, tool_args)
                            result_text = "\n".join([getattr(c, "text", str(c)) for c in mcp_result.content if getattr(c, "type", "") == "text" or hasattr(c, "text")])
                except Exception as e:
                    result_text = f"Error calling tool: {e}"

                duration = time.time() - start_time
                st.write(f"✅ Finished `{tool_name}` ({duration:.2f}s)")

                # Update sidebar if company info is fetched
                if tool_name == "fetch_company_info":
                    try:
                        info = json.loads(result_text)
                        if "error" not in info:
                            st.session_state.company_info = info
                    except: pass

                # Add to history
                st.session_state.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result_text
                })

                # --- RICH VISUALS (Rendered in the STABLE container) ---
                with visuals_container:
                    try:
                        parsed_result = json.loads(result_text)
                        if tool_name == "fetch_news_sentiment" and isinstance(parsed_result, list):
                            display_sentiment_card(parsed_result)
                        elif tool_name == "fetch_historical_prices":
                            display_price_chart("Selected Stock", result_text)
                        elif tool_name == "fetch_financial_statements":
                            s_type = tool_args.get('statement_type', 'income').capitalize()
                            with st.expander(f"📊 {s_type} Statement Data"):
                                st.dataframe(pd.DataFrame(parsed_result), use_container_width=True)
                        else:
                            with st.expander(f"🛠️ Tool Result: {tool_name}"):
                                st.json(parsed_result)
                    except:
                        with st.expander(f"🛠️ Tool Result: {tool_name}"):
                            st.write(result_text)

    # --- PHASE 2: SUMMARY ---
    if final_content:
        with st.spinner("✨ Formatting summary report..."):
            with st.chat_message("assistant"):
                with st.expander("📝 Summary Report", expanded=True):
                    st.markdown(final_content)
    else:
        with st.spinner("✍️ Preparing final summary..."):
            try:
                response = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=st.session_state.messages,
                    extra_body={"thinking": {"type": "disabled"}}
                )
                final_message = response.choices[0].message
                st.session_state.messages.append(final_message.model_dump())

                with st.chat_message("assistant"):
                    with st.expander("📝 Summary Report", expanded=True):
                        st.markdown(final_message.content)
            except Exception as e:
                st.error(f"Error generating summary: {e}")

if prompt := st.chat_input("Ask about an earnings report or stock..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
    with st.spinner("Loading tools..."):
        try:
            openai_tools = get_cached_tools(mcp_url)
            st.session_state.openai_tools = openai_tools # Store for UI
        except Exception as e:
            st.error(f"Failed to fetch tools: {e}")
            openai_tools = []
            
    try:
        asyncio.run(process_chat(prompt, openai_tools))
    except Exception as e:
        st.error(f"Error: {e}")
        st.rerun()
