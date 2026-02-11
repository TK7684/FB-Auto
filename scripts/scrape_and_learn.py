import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import time

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc=""):
        print(f"Processing: {desc}")
        return iterable

# Configure logging
logger.add("logs/scrape.log", rotation="10 MB", retention="5 days", level="INFO")

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.facebook_service import get_facebook_service
from services.gemini_service import get_gemini_service
from services.memory_service import get_memory_service
from services.knowledge_base import get_knowledge_base
from config.settings import settings

# Configuration
MAX_CONVERSATIONS = 50  # Limit to recent 50 conversations for safety
MESSAGES_PER_THREAD = 20 # Last 20 messages per thread
OUTPUT_FILE = Path("data/knowledge_base/learned_patterns.json")

# Prompt for analysis
ANALYSIS_PROMPT = """
You are an expert Sales Analyst. 
Analyze this conversation transcript between a Customer and an Admin (D Plus Skin).

## Context
- Product: D Plus Skin (Skincare for acne, melasma, white skin)
- Goal: Identify successful sales patterns and Q&A pairs.

## Transcript
{transcript}

## Task
Extract 1-3 high-quality Q&A pairs from this conversation IF:
1. The Admin gave a correct, helpful answer.
2. The Admin successfully closed a sale (optional but good).
3. The Customer asked a clear question.

Ignore chit-chat like "Hello", "OK", "Thank you" unless it relates to a sale.

## Format (JSON ONLY)
[
  {{
    "question": "Customer's question (refined for clarity)",
    "answer": "Admin's answer (refined for clarity)",
    "category": "product_info" | "price" | "usage" | "shipping" | "objection_handling",
    "sentiment": "positive" | "neutral" | "negative"
  }}
]
"""

async def scrape_conversations(limit: int = 10) -> List[Dict]:
    """Scrape conversations from inbox."""
    fb = get_facebook_service()
    all_threads = []
    
    logger.info(f"Fetching up to {limit} conversations...")
    
    # 1. Get list of conversations
    conversations_data = await fb.get_conversations(limit=limit)
    threads = conversations_data.get("data", [])
    
    logger.info(f"Found {len(threads)} threads. Fetching messages...")
    
    for thread in tqdm(threads, desc="Scraping Threads"):
        thread_id = thread.get("id")
        
        # 2. Get messages for each thread
        messages_data = await fb.get_thread_messages(thread_id, limit=MESSAGES_PER_THREAD)
        messages = messages_data.get("data", [])
        
        # Reverse to chronological order (oldest first)
        messages.reverse()
        
        if messages:
            all_threads.append({
                "id": thread_id,
                "updated_time": thread.get("updated_time"),
                "messages": messages
            })
            
    return all_threads

def build_transcript(messages: List[Dict]) -> str:
    """Convert message list to readable transcript."""
    transcript = []
    page_id = settings.facebook_page_id
    
    for msg in messages:
        sender_id = msg.get("from", {}).get("id")
        text = msg.get("message", "")
        
        if not text:
            continue
            
        role = "Admin" if sender_id == page_id else "Customer"
        transcript.append(f"{role}: {text}")
        
    return "\n".join(transcript)

async def analyze_thread(gemini, transcript: str) -> List[Dict]:
    """Send transcript to Gemini for analysis."""
    if not transcript or len(transcript) < 50:
        return []

    prompt = ANALYSIS_PROMPT.format(transcript=transcript)
    
    try:
        response = await gemini.generate_response(
            user_question="ANALYZE_TRANSCRIPT",
            context=prompt,
            conversation_history=[],
            max_retries=1
        )
        
        # Clean up JSON
        response = response.replace("```json", "").replace("```", "").strip()
        start = response.find("[")
        end = response.rfind("]") + 1
        
        if start != -1 and end != -1:
            json_str = response[start:end]
            return json.loads(json_str)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        
    return []

async def main(dry_run: bool = False):
    """Main execution flow."""
    logger.info("Starting Inbox Scraper & Pattern Learning...")
    
    fb = get_facebook_service()
    gemini = get_gemini_service()
    memory = get_memory_service()
    kb = get_knowledge_base()
    
    # 1. Scrape
    threads = await scrape_conversations(limit=MAX_CONVERSATIONS)
    logger.info(f"Successfully scraped {len(threads)} conversation threads.")
    
    # 2. Analyze
    extracted_patterns = []
    
    logger.info("Analyzing conversations with Gemini...")
    for thread in tqdm(threads, desc="Analyzing"):
        transcript = build_transcript(thread["messages"])
        if not transcript:
            continue
            
        patterns = await analyze_thread(gemini, transcript)
        if patterns:
            extracted_patterns.extend(patterns)
            
    logger.info(f"Extracted {len(extracted_patterns)} useful patterns.")
    
    if dry_run:
        print("\n--- PREVIEW OF EXTRACTED PATTERNS ---")
        print(json.dumps(extracted_patterns[:3], indent=2, ensure_ascii=False))
        logger.info("Dry run complete. No data saved.")
        return

    # 3. Save & Learn
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing if exists
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
                existing.extend(extracted_patterns)
                extracted_patterns = existing
        except:
            pass
            
    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_patterns, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved patterns to {OUTPUT_FILE}")
    
    # Ingest into Memory/KB
    logger.info("Ingesting into Knowledge Base & Memory...")
    count = 0
    for item in extracted_patterns:
        try:
            # Add to Memory (for specific recall)
            memory.add_memory(
                question=item["question"],
                answer=item["answer"],
                category=item.get("category", "learned")
            )
            
            # Add to Knowledge Base (for RAG)
            kb.add_qa_pair(
                question=item["question"],
                answer=item["answer"],
                source="inbox_learning",
                metadata={"sentiment": item.get("sentiment", "neutral")}
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to ingest item: {e}")
            
    logger.info(f"Successfully ingested {count} new patterns!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run without saving")
    args = parser.parse_args()
    
    asyncio.run(main(dry_run=args.dry_run))
