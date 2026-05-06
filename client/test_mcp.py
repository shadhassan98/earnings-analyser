import asyncio
import traceback
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    try:
        async with sse_client("http://localhost:8000/sse") as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                await mcp_session.initialize()
                mcp_tools = await mcp_session.list_tools()
                print("Tools:", mcp_tools)
    except Exception as e:
        print(f"Exception caught:")
        traceback.print_exc()

asyncio.run(main())
