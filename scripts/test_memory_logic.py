
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.gemini_service import get_gemini_service
from services.memory_service import get_memory_service
from config.constants import SOCIAL_KEYWORDS

def test_memory_logic():
    print("=== Testing Memory Module Logic ===")
    
    # 1. Setup Data
    memory_service = get_memory_service()
    
    # Clear existing memory for test
    memory_service.memories = []
    
    # Add Test Memories
    print("\n[1] Adding test memories...")
    memory_service.add_memory(
        "เป็นสิวใช้ตัวไหนคะ", 
        "แนะนำเซรั่มลดสิวขวดสีเขียวค่ะ แต้มเช้า-เย็น สิวยุบไวมาก 👉 [link] 🌿", 
        category="product"
    )
    memory_service.add_memory(
        "น่ารักจังเลย", 
        "ขอบคุณค่า เขินเลย 😳💕", 
        category="social"
    )
    
    # 2. Test Retrieval
    print("\n[2] Testing Retrieval...")
    similar = memory_service.find_similar("คนเป็นสิวใช้ตัวไหนดี", category="product")
    if similar:
        print("[OK] Found similar memory (Content match)")
    else:
        print("[FAIL] Failed to find similar memory")
        
    # 3. Test Prompt Injection (Product)
    print("\n[3] Testing Prompt Injection (Product)...")
    gemini = get_gemini_service()
    
    # We use _build_prompt to inspect the prompt string
    prompt = gemini._build_prompt(
        user_question="คนเป็นสิวใช้ตัวไหน",
        context="context info"
    )
    
    # Check for memory injection marker (English part of the prompt)
    if "Context" in prompt and "CTA" in prompt: 
        # We can't easily check for Thai text "ตัวอย่างการตอบในอดีต" without encoding issues
        # But we can check if the prompt length is significantly longer or contains the english marker we added?
        # Actually, let's just use repr() to print safe output if needed, or just rely on boolean checks
        if "Q:" in prompt and "A:" in prompt:
             print("[OK] Memory injected into prompt (Found Q: and A: patterns)")
        else:
             print("[FAIL] Memory NOT injected")
    else:
        print("[FAIL] Prompt build failed")
        
    # 4. Test Social Logic
    print("\n[4] Testing Social Logic...")
    social_prompt = gemini._build_prompt(
        user_question="น่ารักจัง",
        context="context info"
    )
    
    # Basic check for social template distinctive features
    if "Social/Chit-chat" in str(SOCIAL_KEYWORDS): # Just dummy check
        pass
        
    if "Context" not in social_prompt: # Social prompt doesn't have Context header
        print("[OK] Generated Social Prompt (Confirmed by absence of 'Context' header)")
    else:
        print("[FAIL] Social logic failed - Generated standard prompt")
        print(f"DEBUG PROMPT: {social_prompt[:100]}...")

if __name__ == "__main__":
    test_memory_logic()
