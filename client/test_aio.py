from google import genai
import asyncio
import os

async def test():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))
    print("Has aio:", hasattr(client, "aio"))
    print("Has aio.models:", hasattr(client.aio, "models"))
    print("Has aio.models.generate_content:", hasattr(client.aio.models, "generate_content"))

asyncio.run(test())
