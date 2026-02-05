"""
Continuous Cleanup Runner (24/7 Mode).
Runs the historical cleanup script in a loop with safety delays.
"""
import asyncio
import sys
import os
from pathlib import Path
from loguru import logger

# Add project root to path
# This allows us to import modules from the project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import the logic function, not the script itself
# Check if scripts is a package, if not, we might need to import differently or rely on sys.path
try:
    from scripts.historical_cleanup import run_cleanup
except ImportError:
    # If running from root as 'python scripts/cleanup_runner.py', scripts might be a package
    # OR if we are just relying on path, we can import without package prefix if scripts is in path?
    # Actually, since we added PROJECT_ROOT, 'scripts.historical_cleanup' should work.
    # But historical_cleanup.py relies on its own sys.path hack.
    pass

# Direct import attempt if module path is tricky
if "scripts.historical_cleanup" not in sys.modules:
    # Use importlib to load source file if standard import fails
    import importlib.util
    spec = importlib.util.spec_from_file_location("historical_cleanup", PROJECT_ROOT / "scripts" / "historical_cleanup.py")
    historical_cleanup = importlib.util.module_from_spec(spec)
    sys.modules["historical_cleanup"] = historical_cleanup
    spec.loader.exec_module(historical_cleanup)
    run_cleanup = historical_cleanup.run_cleanup

# Configuration
RESTART_INTERVAL_MINUTES = 60  # Wait time between sessions
ERROR_WAIT_SECONDS = 300       # Wait time after a crash
MAX_REPLIES = 30               # Max replies per session
POST_COUNT = 50                # Posts to scan per session

async def main_loop():
    logger.info("=" * 60)
    logger.info("🚀 D Plus Skin - Continuous Historical Cleanup Runner")
    logger.info("   Mode: 24/7 Infinite Loop")
    logger.info(f"   Settings: Max {MAX_REPLIES} replies/session, Scan {POST_COUNT} posts")
    logger.info(f"   Interval: {RESTART_INTERVAL_MINUTES} minutes cooldown")
    logger.info("=" * 60)
    
    session_count = 0
    
    while True:
        session_count += 1
        try:
            logger.info(f"\n▶ Starting Session #{session_count}...")
            
            # Execute the cleanup logic
            await run_cleanup(max_replies=MAX_REPLIES, post_count=POST_COUNT)
            
            logger.info(f"✅ Session #{session_count} Complete.")
            
        except Exception as e:
            logger.error(f"💥 Critical Error in Session #{session_count}: {e}")
            logger.info(f"Waiting {ERROR_WAIT_SECONDS}s before retrying...")
            await asyncio.sleep(ERROR_WAIT_SECONDS)
            continue

        # Cooldown Period
        logger.info(f"⏳ Cooling down for {RESTART_INTERVAL_MINUTES} minutes to respect FB limits...")
        
        # Log countdown every minute (optional, keeping it simple for now)
        # Just simple sleep
        await asyncio.sleep(RESTART_INTERVAL_MINUTES * 60)
        logger.info("⏰ Cooldown finished. Waking up...")

if __name__ == "__main__":
    try:
        # Configure logger to output to stdout as well if needed, 
        # but historical_cleanup already configures a file logger.
        # We'll just run.
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("\n🛑 Runner stopped by user.")
