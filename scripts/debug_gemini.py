import sys
import os
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gemini_service import get_gemini_service
from config.settings import settings

async def test_embed():
    s = get_gemini_service()
    print(f"API Key present: {bool(settings.gemini_api_key)}")
    print(f"OpenRouter Key present: {bool(settings.openrouter_api_key)} (Ends with: ...{str(settings.openrouter_api_key)[-4:] if settings.openrouter_api_key else 'N/A'})")
    
    print("\nTesting Chat Completion...")
    try:
        response = await s.generate_response("Hello, are you working?", context="Testing")
        # Handle encoding for Thai response print
        try:
            print(f"Chat Response: {response[:100]}...")
        except UnicodeEncodeError:
            print(f"Chat Response: {response[:100].encode('ascii', errors='replace').decode('ascii')}...")
    except Exception as e:
        print(f"Chat Error: {e}")

    print("\nTesting Embeddings...")
    try:
        result = s.get_embeddings("test")
        print(f"Result type: {type(result)}")
        if result:
            print(f"Embedding length: {len(result[0]) if isinstance(result, list) and result and isinstance(result[0], list) else len(result)}")
            print(f"First 5 values: {result[0][:5] if isinstance(result, list) and result and isinstance(result[0], list) else result[:5]}")
        else:
            print("Embedding is empty.")
    except Exception as e:
        print(f"Embedding Error: {e}")

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_embed())
