import asyncio
import os
from dotenv import load_dotenv
from app.providers import VercelProvider, OpenAIProvider

load_dotenv()

async def test_providers():
    print("Testing providers...")
    
    # Test Vercel
    try:
        vercel = VercelProvider()
        print(f"Vercel API key: {vercel.api_key[:20]}...")
        result = await vercel.get_models()
        print("✅ Vercel works!")
    except Exception as e:
        print(f"❌ Vercel failed: {e}")
    
    # Test OpenAI
    try:
        openai = OpenAIProvider()
        print(f"OpenAI API key: {openai.api_key[:20]}...")
        result = await openai.get_models()
        print("✅ OpenAI works!")
    except Exception as e:
        print(f"❌ OpenAI failed: {e}")

asyncio.run(test_providers())
