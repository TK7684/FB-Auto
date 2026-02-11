
import json
import random
import time
import threading
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger
from datetime import datetime


class MemoryService:
    """
    Service for Memory & Learning (Simple RAG).
    Stores successful Q&A pairs and retrieves them to improve future responses.

    Optimized: Batches disk writes (every 10 items or 60s) instead of writing on each add.
    """

    BATCH_SIZE = 10
    FLUSH_INTERVAL = 60  # seconds

    def __init__(self, memory_file: str = "data/memory.json"):
        self.memory_file = Path(memory_file)
        self.memories: List[Dict] = []
        self._dirty_count = 0
        self._last_flush = time.time()
        self._lock = threading.Lock()
        self._load_memory()

    def _load_memory(self):
        """Load memory from JSON file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
                logger.info(f"Loaded {len(self.memories)} items from memory.")
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                self.memories = []
        else:
            logger.warning("Memory file not found, starting fresh.")
            self.memories = []

    def save_memory(self):
        """Save memory to JSON file (explicit flush)."""
        with self._lock:
            try:
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    json.dump(self.memories, f, ensure_ascii=False, indent=2)
                self._dirty_count = 0
                self._last_flush = time.time()
            except Exception as e:
                logger.error(f"Error saving memory: {e}")

    def _maybe_flush(self):
        """Flush to disk if batch threshold or time interval reached."""
        should_flush = (
            self._dirty_count >= self.BATCH_SIZE
            or (time.time() - self._last_flush) > self.FLUSH_INTERVAL
        )
        if should_flush:
            self.save_memory()

    def add_memory(self, question: str, answer: str, category: str = "general"):
        """Add a new Q&A pair to memory (batched write)."""
        with self._lock:
            # Simple deduplication
            for item in self.memories:
                if item["question"] == question and item["answer"] == answer:
                    return

            new_item = {
                "question": question,
                "answer": answer,
                "category": category,
                "timestamp": datetime.now().isoformat()
            }
            self.memories.append(new_item)
            self._dirty_count += 1

        self._maybe_flush()

    def find_similar(self, query: str, category: str = None, limit: int = 2) -> List[Dict]:
        """
        Find similar past Q&A pairs using keyword matching.
        
        Args:
            query: User question
            category: Optional filter by category
            limit: Max results to return
            
        Returns:
            List of similar memory items
        """
        if not self.memories:
            return []

        query_tokens = set(query.lower().split())
        scored_memories = []

        for item in self.memories:
            if category and item.get("category") != category:
                continue

            # Jaccard similarity
            item_tokens = set(item["question"].lower().split())
            intersection = query_tokens.intersection(item_tokens)
            union = query_tokens.union(item_tokens)
            
            if not union:
                score = 0
            else:
                score = len(intersection) / len(union)

            if category and item.get("category") == category:
                score += 0.2

            if score > 0.1:
                scored_memories.append((score, item))

        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        return [m[1] for m in scored_memories[:limit]]

    def get_random_example(self, category: str = "social") -> Optional[Dict]:
        """Get a random example for a specific category."""
        candidates = [m for m in self.memories if m.get("category") == category]
        if candidates:
            return random.choice(candidates)
        return None

    def flush(self):
        """Force flush any pending writes to disk."""
        if self._dirty_count > 0:
            self.save_memory()

# Singleton instance
_memory_service = None

def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
