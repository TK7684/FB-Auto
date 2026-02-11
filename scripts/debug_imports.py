
import sys
import os
import time

print("1. Starting debug bisect...")
# Add parent dir to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def test_import(module_name):
    print(f"Importing {module_name}...", end="", flush=True)
    start = time.time()
    try:
        __import__(module_name)
        print(f" DONE ({time.time() - start:.2f}s)")
    except Exception as e:
        print(f" FAIL: {e}")

test_import("config.settings")
test_import("services.rate_limiter")
test_import("services.gemini_service")
test_import("services.facebook_service")
test_import("services.knowledge_base")
test_import("api.webhooks")
test_import("api.health")
test_import("main")

print("Bisect complete.")
