import time
import json
import logging
import threading
from pathlib import Path
from filelock import FileLock # Requires `pip install filelock`

logger = logging.getLogger(__name__)

# Constants
RATE_LIMIT_FILE = Path("data/rate_limits.json")
LOCK_FILE = Path("data/rate_limits.json.lock")
MAX_COMMENTS_PER_HOUR = 60 # Safe limit for human-like behavior (1/min)
PANIC_COOLDOWN = 3600 # 1 hour if blocked

class RateLimiter:
    """
    Global Rate Limiter using a shared file.
    Ensures multiple scripts (Fast Reply & Cleanup) don't exceed FB limits.
    """
    
    def __init__(self):
        self._ensure_file_exists()
        self.local_lock = threading.Lock()

    def _ensure_file_exists(self):
        """Initialize the shared state file if missing."""
        if not RATE_LIMIT_FILE.exists():
            RATE_LIMIT_FILE.parent.mkdir(exist_ok=True)
            self._save_state({
                "comments_this_hour": 0,
                "hour_start_ts": time.time(),
                "panic_until_ts": 0,
                "last_action_ts": 0
            })

    def _load_state(self) -> dict:
        """Load state safely with file lock."""
        with FileLock(str(LOCK_FILE), timeout=5):
            try:
                if RATE_LIMIT_FILE.exists():
                    with open(RATE_LIMIT_FILE, "r") as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load rate limit state: {e}")
        return {}

    def _save_state(self, state: dict):
        """Save state safely with file lock."""
        with FileLock(str(LOCK_FILE), timeout=5):
            try:
                with open(RATE_LIMIT_FILE, "w") as f:
                    json.dump(state, f)
            except Exception as e:
                logger.error(f"Failed to save rate limit state: {e}")

    def check_and_increment(self) -> bool:
        """
        Check if we can make a request.
        Returns True if allowed, False if limited.
        """
        state = self._load_state()
        if not state: return True # Default to allow if state broken (fail open? typical is fail closed, but let's be lenient locally)
        
        now = time.time()
        
        # 1. Check Panic Mode
        if now < state.get("panic_until_ts", 0):
            remaining = int(state["panic_until_ts"] - now)
            logger.warning(f"⛔ GLOBAL PANIC MODE ACTIVE. {remaining}s remaining.")
            return False

        # 2. Reset Hourly Counter
        if now - state.get("hour_start_ts", 0) > 3600:
            state["comments_this_hour"] = 0
            state["hour_start_ts"] = now
            
        # 3. Check Hourly Limit
        if state["comments_this_hour"] >= MAX_COMMENTS_PER_HOUR:
            logger.warning(f"⏳ Hourly Limit Reached ({state['comments_this_hour']}/{MAX_COMMENTS_PER_HOUR}). Waiting...")
            return False
            
        # 4. Increment
        state["comments_this_hour"] += 1
        state["last_action_ts"] = now
        self._save_state(state)
        return True

    def trigger_panic(self):
        """Trigger global panic mode (stop everything for 1 hour)."""
        logger.error("🚨 TRIGGERING GLOBAL PANIC MODE (1 HOUR COOLDOWN)")
        state = self._load_state()
        state["panic_until_ts"] = time.time() + PANIC_COOLDOWN
        self._save_state(state)

_instance = None

def get_rate_limiter() -> RateLimiter:
    global _instance
    if _instance is None:
        _instance = RateLimiter()
    return _instance
