import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
import os
from google import genai
from google.genai import types

async def process_chat(prompt_text):
    async with sse_client("http://localhost:8000/sse", timeout=30.0) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            await mcp_session.initialize()
            mcp_tools = await mcp_session.list_tools()
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
            print("Tools:", mcp_tools)
            response = await client.aio.models.generate_content(
                model="gemini-1.5-flash",
                contents="Hello",
            )
            print("Response:", response.text)

asyncio.run(process_chat("test"))
