"""
Facebook Page Scraper Script.

This script scrapes historical posts and comments from your Facebook page
to build the knowledge base for the AI bot.

Usage:
    python scripts/scrape_facebook.py --full          # Full scrape
    python scripts/scrape_facebook.py --incremental   # Since last scrape
    python scripts/scrape_facebook.py --days 7        # Last 7 days
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from facebook_scraper import get_posts
except ImportError:
    logger.error("facebook-scraper not installed. Run: pip install facebook-scraper")
    sys.exit(1)

from services.knowledge_base import KnowledgeBase


def scrape_facebook_page(
    page_name: str,
    limit: int = 50,
    days: int = None
) -> list:
    """
    Scrape posts from Facebook page.

    Args:
        page_name: Facebook page name or ID
        limit: Maximum number of posts to scrape
        days: Only scrape posts from last N days (None for all)

    Returns:
        List of post dictionaries
    """
    logger.info(f"Scraping {limit} posts from {page_name}")

    if days:
        logger.info(f"Only scraping posts from last {days} days")
        cutoff_date = datetime.now() - timedelta(days=days)
    else:
        cutoff_date = None

    posts_data = []

    try:
        for post in get_posts(account=page_name, pages=limit):
            post_data = {
                "post_id": post.get("post_id", ""),
                "text": post.get("text", ""),
                "time": post.get("time", None),
                "image": post.get("image", None),
                "likes": post.get("likes", 0),
                "comments": post.get("comments", [])[:10]  # Top 10 comments
            }

            # Filter by date if specified
            if cutoff_date and post_data["time"]:
                if post_data["time"] < cutoff_date:
                    continue

            posts_data.append(post_data)

            if len(posts_data) % 10 == 0:
                logger.info(f"Scraped {len(posts_data)} posts...")

        logger.info(f"✓ Scraped {len(posts_data)} posts total")
        return posts_data

    except Exception as e:
        logger.error(f"Error scraping Facebook: {e}")
        return []


def extract_qa_pairs(posts_data: list) -> list:
    """
    Extract Q&A pairs from posts and comments.

    Args:
        posts_data: List of post dictionaries

    Returns:
        List of Q&A dictionaries
    """
    qa_pairs = []

    for post in posts_data:
        post_text = post.get("text", "")
        comments = post.get("comments", [])

        for comment in comments:
            comment_text = comment.get("comment", "")

            # Simple heuristic: questions contain "?"
            if "?" in comment_text and len(comment_text) > 10:
                # Check for admin replies
                replies = comment.get("comments", [])
                admin_reply = ""

                for reply in replies:
                    # Often admin replies are marked
                    if reply.get("admin", False):
                        admin_reply = reply.get("comment", "")
                        break

                qa_pairs.append({
                    "question": comment_text,
                    "answer": admin_reply,
                    "source": "comment",
                    "post_id": post.get("post_id"),
                    "timestamp": comment.get("time", datetime.now().isoformat())
                })

    logger.info(f"✓ Extracted {len(qa_pairs)} Q&A pairs")
    return qa_pairs


def save_scraped_data(posts_data: list, output_dir: str = "data/scraped_data"):
    """
    Save scraped data to JSON file.

    Args:
        posts_data: List of post dictionaries
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"posts_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ Saved scraped data to {filename}")


def load_and_add_to_kb(kb: KnowledgeBase, qa_pairs: list):
    """
    Add Q&A pairs to knowledge base.

    Args:
        kb: KnowledgeBase instance
        qa_pairs: List of Q&A dictionaries
    """
    added = 0

    for qa in qa_pairs:
        if qa["answer"]:  # Only add if we have an answer
            success = kb.add_qa_pair(
                question=qa["question"],
                answer=qa["answer"],
                source=qa["source"],
                metadata={"post_id": qa.get("post_id")}
            )
            if success:
                added += 1

    logger.info(f"✓ Added {added} Q&A pairs to knowledge base")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scrape Facebook page for knowledge base")
    parser.add_argument("--page", default="dplusskin", help="Facebook page name")
    parser.add_argument("--limit", type=int, default=50, help="Number of posts to scrape")
    parser.add_argument("--days", type=int, help="Only scrape last N days")
    parser.add_argument("--full", action="store_true", help="Full scrape (all time)")
    parser.add_argument("--add-to-kb", action="store_true", help="Add Q&A to knowledge base")
    parser.add_argument("--output", default="data/scraped_data", help="Output directory")

    args = parser.parse_args()

    # Scrape posts
    posts = scrape_facebook_page(
        page_name=args.page,
        limit=args.limit,
        days=None if args.full else args.days
    )

    if not posts:
        logger.warning("No posts scraped, exiting")
        return

    # Save scraped data
    save_scraped_data(posts, args.output)

    # Extract Q&A pairs
    qa_pairs = extract_qa_pairs(posts)

    # Save Q&A pairs
    qa_path = Path(args.output) / f"qa_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    logger.info(f"✓ Saved Q&A pairs to {qa_path}")

    # Optionally add to knowledge base
    if args.add_to_kb:
        kb = KnowledgeBase()
        load_and_add_to_kb(kb, qa_pairs)

    logger.info("Scraping complete!")


if __name__ == "__main__":
    main()
