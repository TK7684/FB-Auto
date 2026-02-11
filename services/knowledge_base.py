"""
Knowledge Base Service using ChromaDB.

This module provides semantic search capabilities for products and Q&A pairs.
Uses sentence transformers for Thai language embeddings and ChromaDB for vector storage.
"""

# import pandas as pd # Lazy loaded in method
# Move heavy imports inside class to avoid blocking startup
# import chromadb
# from chromadb.config import Settings as ChromaSettings
# from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
from loguru import logger
from pathlib import Path
import json
import hashlib
from datetime import datetime
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from functools import lru_cache

from services.gemini_service import get_gemini_service


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        service = get_gemini_service()
        # Ensure input is a list of strings
        if isinstance(input, str):
            input = [input]
        return service.get_embeddings(input)


class KnowledgeBase:
    """
    Knowledge base for product search and Q&A retrieval.

    Uses ChromaDB with Gemini embeddings for semantic search
    in Thai and English languages.
    """

    def __init__(
        self,
        persist_dir: str = "./data/knowledge_base",
        embedding_model: Optional[str] = None
    ):
        """
        Initialize the knowledge base.

        Args:
            persist_dir: Directory for ChromaDB persistence
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))

        # Initialize Gemini embedding function
        self.embedding_fn = GeminiEmbeddingFunction()
        logger.info("Initialized Gemini Embedding Function")

        # Get or create collections
        self.products_collection = self.client.get_or_create_collection(
            name="products",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        self.qa_collection = self.client.get_or_create_collection(
            name="qa_pairs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            f"Knowledge base initialized at {persist_dir}. "
            f"Products: {self.products_collection.count()}, "
            f"Q&A: {self.qa_collection.count()}"
        )

    def load_products_from_csv(
        self,
        csv_path: str,
        clear_existing: bool = False
    ) -> int:
        """
        Load products from CSV file into ChromaDB.

        Args:
            csv_path: Path to CSV file with product data
            clear_existing: Clear existing products before loading

        Returns:
            Number of products loaded
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"Product CSV not found: {csv_path}")
            return 0

        try:
            # Lazy import pandas
            import pandas as pd
            
            # Check hash to avoid redundant reload
            hash_file = csv_file.with_suffix('.hash')
            current_hash = hashlib.md5(csv_file.read_bytes()).hexdigest()
            
            if not clear_existing and hash_file.exists():
                stored_hash = hash_file.read_text().strip()
                if stored_hash == current_hash and self.products_collection.count() > 0:
                    logger.info(f"Products CSV hash matches ({current_hash[:8]}). Skipping reload.")
                    return self.products_collection.count()
            
            # Read CSV - the file has English headers first, then Thai headers
            # Skip the first 2 rows (English headers + empty row) to get to Thai headers
            df = pd.read_csv(csv_file, encoding="utf-8", skiprows=2, on_bad_lines='skip')

            # Remove completely empty rows
            df = df.dropna(how='all')

            logger.info(f"Loaded {len(df)} raw rows from {csv_path}")

            # Column mapping: Thai columns -> English columns
            column_mapping = {
                "ชื่อสินค้า": "Product_Name",
                "คำอธิบายสินค้า": "Description",
                "ลิงก์สินค้า": "Link",
                "Link": "Link",
            }

            # Rename Thai columns to English
            df = df.rename(columns=column_mapping)

            # For columns that don't have a direct mapping, try to auto-detect
            if "Product_Name" not in df.columns:
                # Try to find a column that looks like product name
                for col in df.columns:
                    col_lower = col.lower()
                    if "name" in col_lower or "ชื่อ" in col or "สินค้า" in col:
                        df = df.rename(columns={col: "Product_Name"})
                        break

            if "Description" not in df.columns:
                for col in df.columns:
                    col_lower = col.lower()
                    if "desc" in col_lower or "อธิบาย" in col:
                        df = df.rename(columns={col: "Description"})
                        break

            # Required columns after mapping
            required_cols = ["Product_Name", "Link"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                logger.error(f"Available columns: {list(df.columns)}")
                return 0

            # Set defaults for optional columns
            if "Symptom_Target" not in df.columns:
                df["Symptom_Target"] = ""
            if "Price" not in df.columns:
                df["Price"] = "ติดต่อสอบถาม"
            if "Promotion" not in df.columns:
                df["Promotion"] = ""

            # Clear existing if requested
            if clear_existing:
                self.client.delete_collection("products")
                self.products_collection = self.client.create_collection(
                    name="products",
                    embedding_function=self.embedding_fn,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Cleared existing products")

            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []

            for idx, row in df.iterrows():
                # Create searchable text
                text_parts = [
                    str(row["Product_Name"]),
                    str(row["Symptom_Target"]),
                ]
                if "Description" in df.columns:
                    text_parts.append(str(row["Description"]))
                if "Ingredients" in df.columns:
                    text_parts.append(str(row["Ingredients"]))

                document = " ".join(text_parts)

                # Build metadata
                metadata = {
                    "product_name": str(row["Product_Name"]),
                    "price": str(row["Price"]),
                    "link": str(row["Link"]),
                    "symptoms": str(row["Symptom_Target"]),
                }

                # Optional fields
                if "Promotion" in df.columns:
                    metadata["promotion"] = str(row["Promotion"])
                if "Description" in df.columns:
                    metadata["description"] = str(row["Description"])

                documents.append(document)
                metadatas.append(metadata)
                ids.append(f"product_{idx}")

            # Add to collection
            self.products_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            # Save new hash
            hash_file.write_text(current_hash)
            logger.info(f"Successfully loaded {len(documents)} products and updated hash")
            return len(documents)

        except Exception as e:
            logger.error(f"Error loading products from CSV: {e}")
            return 0

    def search_products(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using semantic search.

        Args:
            query: Search query (Thai or English)
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of product dictionaries with relevance scores
        """
        try:
            results = self.products_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata
            )

            if not results["ids"][0]:
                logger.warning(f"No products found for query: {query}")
                return []

            products = []
            for i in range(len(results["ids"][0])):
                product = {
                    "id": results["ids"][0][i],
                    "product_name": results["metadatas"][0][i]["product_name"],
                    "price": results["metadatas"][0][i]["price"],
                    "link": results["metadatas"][0][i]["link"],
                    "symptoms": results["metadatas"][0][i].get("symptoms", ""),
                    "distance": results["distances"][0][i] if "distances" in results else None,
                }

                # Optional fields
                if "promotion" in results["metadatas"][0][i]:
                    product["promotion"] = results["metadatas"][0][i]["promotion"]
                if "description" in results["metadatas"][0][i]:
                    product["description"] = results["metadatas"][0][i]["description"]

                products.append(product)

            logger.debug(f"Found {len(products)} products for query: {query}")
            return products

        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []

    def search_qa(
        self,
        query: str,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Search Q&A pairs for relevant past conversations.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of Q&A dictionaries
        """
        try:
            results = self.qa_collection.query(
                query_texts=[query],
                n_results=top_k
            )

            if not results["ids"][0]:
                return []

            qa_pairs = []
            for i in range(len(results["ids"][0])):
                qa_pairs.append({
                    "id": results["ids"][0][i],
                    "question": results["metadatas"][0][i].get("question", ""),
                    "answer": results["metadatas"][0][i].get("answer", ""),
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "timestamp": results["metadatas"][0][i].get("timestamp", ""),
                })

            return qa_pairs

        except Exception as e:
            logger.error(f"Error searching Q&A: {e}")
            return []

    @lru_cache(maxsize=128)
    def generate_context(
        self,
        query: str,
        include_qa: bool = True,
        top_products: int = 3,
        top_qa: int = 2
    ) -> str:
        """
        Generate context string for Gemini LLM from search results.

        Args:
            query: User query
            include_qa: Include Q&A pairs in context
            top_products: Number of products to include
            top_qa: Number of Q&A pairs to include

        Returns:
            Formatted context string
        """
        context_parts = []

        # Search products
        products = self.search_products(query, top_k=top_products)

        if products:
            context_parts.append("ข้อมูลผลิตภัณฑ์ที่เกี่ยวข้อง:")
            for p in products:
                product_line = f"- {p['product_name']}: {p['price']} บาท"
                if p.get("promotion"):
                    product_line += f" ({p['promotion']})"
                product_line += f" ลิงก์: {p['link']}"
                if p.get("symptoms"):
                    product_line += f" (เหมาะสำหรับ: {p['symptoms']})"
                context_parts.append(product_line)
        else:
            context_parts.append("ไม่พบผลิตภัณฑ์ที่เกี่ยวข้อง")

        # Search Q&A pairs
        if include_qa:
            qa_pairs = self.search_qa(query, top_k=top_qa)
            if qa_pairs:
                context_parts.append("\nคำถามที่คล้ายกันในอดีต:")
                for qa in qa_pairs:
                    context_parts.append(f"Q: {qa['question']}")
                    if qa["answer"]:
                        context_parts.append(f"A: {qa['answer']}")

        return "\n".join(context_parts)

    def add_qa_pair(
        self,
        question: str,
        answer: str,
        source: str = "conversation",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a new Q&A pair to the knowledge base.

        Args:
            question: Question text
            answer: Answer text
            source: Source (e.g., "comment", "dm", "manual")
            metadata: Additional metadata

        Returns:
            True if added successfully
        """
        try:
            qa_id = f"qa_{int(datetime.now().timestamp() * 1000)}"
            qa_metadata = {
                "question": question,
                "answer": answer,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                qa_metadata.update(metadata)

            self.qa_collection.add(
                documents=[f"{question} {answer}"],
                metadatas=[qa_metadata],
                ids=[qa_id]
            )

            logger.info(f"Added Q&A pair: {question[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error adding Q&A pair: {e}")
            return False

    def get_product_count(self) -> int:
        """Get number of products in knowledge base."""
        return self.products_collection.count()

    def get_qa_count(self) -> int:
        """Get number of Q&A pairs in knowledge base."""
        return self.qa_collection.count()

    def export_qa_pairs(self, output_path: str) -> bool:
        """
        Export all Q&A pairs to JSON file.

        Args:
            output_path: Path to output JSON file

        Returns:
            True if exported successfully
        """
        try:
            results = self.qa_collection.get()
            qa_pairs = []

            for i, doc_id in enumerate(results["ids"]):
                qa_pairs.append({
                    "id": doc_id,
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

            logger.info(f"Exported {len(qa_pairs)} Q&A pairs to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting Q&A pairs: {e}")
            return False


# Singleton instance
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base(
    persist_dir: str = "./data/knowledge_base"
) -> KnowledgeBase:
    """Get the global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase(persist_dir)
    return _knowledge_base


def reset_knowledge_base():
    """Reset the global knowledge base instance."""
    global _knowledge_base
    _knowledge_base = None
