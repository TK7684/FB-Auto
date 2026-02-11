"""
Continuous Cleanup Runner (Deep Loop).
Runs the historical cleanup script in a loop with safety delays.
Now optimized for the Dual-Loop Architecture (Runs every 4 hours).
"""
import asyncio
import sys
import os
from pathlib import Path
from loguru import logger

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import logic
try:
    from scripts.historical_cleanup import run_cleanup
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("historical_cleanup", PROJECT_ROOT / "scripts" / "historical_cleanup.py")
    historical_cleanup = importlib.util.module_from_spec(spec)
    sys.modules["historical_cleanup"] = historical_cleanup
    spec.loader.exec_module(historical_cleanup)
    run_cleanup = historical_cleanup.run_cleanup

# --- Configuration (Optimized) ---
# Less frequent because "Fast Responder" handles new comments
RESTART_INTERVAL_HOURS = 4     # Run every 4 hours (Deep Clean)
ERROR_WAIT_SECONDS = 300       # Wait time after a crash
MAX_REPLIES = 50               # Max replies per session (higher limit for deep cleans)
POST_COUNT = 100               # Scan last 100 posts (Go deeper)

async def main_loop():
    logger.info("=" * 60)
    logger.info("🧹 D Plus Skin - Deep Cleanup Runner")
    logger.info("   Mode: Schedule Loop (Every 4 Hours)")
    logger.info(f"   Settings: Max {MAX_REPLIES} replies/session, Scan {POST_COUNT} posts")
    logger.info("=" * 60)
    
    session_count = 0
    
    while True:
        session_count += 1
        try:
            logger.info(f"\n▶ Starting Cleanup Session #{session_count}...")
            
            # Execute the cleanup logic
            await run_cleanup(max_replies=MAX_REPLIES, post_count=POST_COUNT)
            
            logger.info(f"✅ Session #{session_count} Complete.")
            
        except Exception as e:
            logger.error(f"💥 Critical Error in Session #{session_count}: {e}")
            logger.info(f"Waiting {ERROR_WAIT_SECONDS}s before retrying...")
            await asyncio.sleep(ERROR_WAIT_SECONDS)
            continue

        # Cooldown Period
        logger.info(f"⏳ Sleeping for {RESTART_INTERVAL_HOURS} hours...")
        await asyncio.sleep(RESTART_INTERVAL_HOURS * 3600)
        logger.info("⏰ Waking up for next cleanup...")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("\n🛑 Runner stopped by user.")
