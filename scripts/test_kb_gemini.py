import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.knowledge_base import KnowledgeBase
from config.settings import settings

def test_kb():
    print("Initializing Knowledge Base with Gemini Embeddings...")
    # Use a test directory to avoid corrupting main DB yet
    test_dir = "./data/knowledge_base_test"
    
    try:
        # Initialize KB
        kb = KnowledgeBase(persist_dir=test_dir)
        
        # Add a QA pair
        question = "ราคาเท่าไหร่"
        answer = "เริ่มต้น 290 บาทค่ะ"
        print(f"Adding QA pair: Q={question}, A={answer}")
        success = kb.add_qa_pair(question, answer, source="test")
        
        if success:
            print("QA pair added successfully.")
        else:
            print("Failed to add QA pair.")
            return

        # Search
        search_query = "ราคา"
        print(f"Searching for: {search_query}")
        results = kb.search_qa(search_query)
        
        print(f"Found {len(results)} results:")
        for res in results:
            print(f"- {res['question']} -> {res['answer']}")
            
        if len(results) > 0:
            print("TEST PASSED: Gemini Embeddings working!")
        else:
            print("TEST FAILED: No results found.")
            
    except Exception as e:
        print(f"TEST FAILED with Exception: {e}")

if __name__ == "__main__":
    # Ensure env loaded
    from dotenv import load_dotenv
    load_dotenv()
    
    test_kb()
