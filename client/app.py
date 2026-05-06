import streamlit as st
import asyncio
import os
import json
import time
from google import genai
from google.genai import types
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# Setup page
st.set_page_config(page_title="Earnings Analyzer Chat", layout="wide")
st.title("Earnings Analyzer Chat")

# Initialize Gemini API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if not api_key:
        st.warning("Please provide a Gemini API Key to continue.")
        st.stop()

# Initialize Gemini client
client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for msg in st.session_state.messages:
    if msg.role == "user":
        with st.chat_message("user"):
            for part in msg.parts:
                if part.text:
                    st.markdown(part.text)
                elif part.function_response:
                    with st.expander(f"Tool Result: {part.function_response.name}"):
                        st.json(part.function_response.response)
    elif msg.role == "model":
        with st.chat_message("assistant"):
            for part in msg.parts:
                if part.text:
                    st.markdown(part.text)
                elif part.function_call:
                    st.code(f"Calling tool: {part.function_call.name}({part.function_call.args})")

def map_mcp_to_gemini(mcp_tools):
    gemini_tools = []
    for t in mcp_tools.tools:
        schema = t.inputSchema
        properties = {}
        for prop_name, prop_info in schema.get("properties", {}).items():
            ptype = prop_info.get("type", "string")
            if ptype == "string":
                gtype = types.Type.STRING
            elif ptype == "number":
                gtype = types.Type.NUMBER
            elif ptype == "integer":
                gtype = types.Type.INTEGER
            elif ptype == "boolean":
                gtype = types.Type.BOOLEAN
            elif ptype == "array":
                gtype = types.Type.ARRAY
            elif ptype == "object":
                gtype = types.Type.OBJECT
            else:
                gtype = types.Type.STRING

            properties[prop_name] = types.Schema(
                type=gtype,
                description=prop_info.get("description", "")
            )
            
        gemini_tools.append(types.FunctionDeclaration(
            name=t.name,
            description=t.description or "",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties=properties,
                required=schema.get("required", [])
            )
        ))
    return gemini_tools

@st.cache_resource(ttl=3600)
def get_cached_tools(mcp_url):
    print("FETCHING TOOLS FROM MCP (Cache Miss)...")
    async def _fetch():
        async with sse_client(mcp_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                await mcp_session.initialize()
                mcp_tools = await mcp_session.list_tools()
                return map_mcp_to_gemini(mcp_tools)
                
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

async def process_chat(prompt_text, gemini_tools):
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
    
    tool_config = types.Tool(function_declarations=gemini_tools) if gemini_tools else None
    
    with st.spinner("Thinking..."):
        while True:
            try:
                print("Calling Gemini API...")
                start_t = time.time()
                response = await client.aio.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=st.session_state.messages,
                    config=types.GenerateContentConfig(
                        tools=[tool_config] if tool_config else None
                    )
                )
                print(f"Gemini API took: {time.time() - start_t:.2f}s")
            except Exception as api_err:
                st.error(f"Gemini API Error: {api_err}")
                break
            
            if not response.candidates:
                st.error("No response from model.")
                break
                
            candidate = response.candidates[0]
            st.session_state.messages.append(candidate.content)
            
            has_function_call = False
            for part in candidate.content.parts:
                if part.function_call:
                    has_function_call = True
                    tool_name = part.function_call.name
                    tool_args = part.function_call.args
                    
                    with st.chat_message("assistant"):
                        st.code(f"Calling tool: {tool_name}({tool_args})")
                    
                    try:
                        args_dict = dict(tool_args) if tool_args else {}
                        async with sse_client(mcp_url) as (read_stream, write_stream):
                            async with ClientSession(read_stream, write_stream) as mcp_session:
                                await mcp_session.initialize()
                                mcp_result = await mcp_session.call_tool(tool_name, args_dict)
                                result_text = "\n".join([getattr(c, "text", str(c)) for c in mcp_result.content if getattr(c, "type", "") == "text" or hasattr(c, "text")])
                    except Exception as e:
                        result_text = f"Error calling tool: {e}"
                        
                    tool_response_part = types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result_text}
                    )
                    
                    user_msg = types.Content(role="user", parts=[tool_response_part])
                    st.session_state.messages.append(user_msg)
                    
                    with st.chat_message("user"):
                        with st.expander(f"Tool Result: {tool_name}"):
                            st.json({"result": result_text})
                            
            if not has_function_call:
                with st.chat_message("assistant"):
                    for part in candidate.content.parts:
                        if part.text:
                            st.markdown(part.text)
                break

if prompt := st.chat_input("Ask about an earnings report or stock..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
    
    mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/sse")
    with st.spinner("Loading tools..."):
        try:
            t0 = time.time()
            gemini_tools = get_cached_tools(mcp_url)
            print(f"Loading tools took: {time.time() - t0:.2f}s")
        except Exception as e:
            st.error(f"Failed to fetch tools: {e}")
            gemini_tools = []
            
    try:
        asyncio.run(process_chat(prompt, gemini_tools))
    except ExceptionGroup as eg:
        st.error(f"Caught ExceptionGroup: {eg.exceptions}")
        raise
    except Exception as e:
        st.error(f"Error: {e}")
        raise
