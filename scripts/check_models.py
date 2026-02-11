
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from config.settings import settings

print("Checking available Gemini models...")
print(f"API Key: {settings.gemini_api_key[:5]}...{settings.gemini_api_key[-5:] if settings.gemini_api_key else 'None'}")

if not settings.gemini_api_key:
    print("❌ Error: No API Key found in settings.")
    exit(1)

try:
    genai.configure(api_key=settings.gemini_api_key)
    print("\n--- Available Models ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
    print("------------------------")
    
except Exception as e:
    print(f"\n❌ Error listing models: {e}")
